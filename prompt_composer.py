"""Offline Prompt Composer. Public knowledge cards are bundled; no model is called."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import sqlite3
import sys
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Any, Iterable

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE
CONFIG_PATH = HERE / "composer_config.json"
SCHEMA_PATH = HERE / "composer_schema.sql"
TOKEN_RE = re.compile(r"[a-z0-9][a-z0-9'/-]*|[가-힣]{2,}", re.IGNORECASE)
WORD_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9'/-]*")
GENERIC_TOKENS = {
    "제품", "오브젝트", "사용", "영상", "화면", "변화", "상태", "유지", "마지막",
    "있다", "보이는", "보이고", "드러난다", "the", "and", "with", "from", "into",
    "that", "this", "object", "product", "video", "visible", "change", "surface",
}


def load_json(path: Path) -> dict[str, Any]:
    """Load a JSON request or configuration."""
    if path.stat().st_size > 1_000_000:
        raise ValueError("Input exceeds the 1 MB limit")
    def reject_constant(value: str) -> None:
        raise ValueError("Non-finite JSON numbers are not allowed")
    value = json.loads(path.read_text(encoding="utf-8-sig"), parse_constant=reject_constant)
    if not isinstance(value, dict):
        raise ValueError("Input must be a JSON object")
    return value


def dump_json(value: Any) -> str:
    """Serialize results as JSON."""
    return json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n"


def normalize(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "").strip().lower())


def tokens(value: Any) -> set[str]:
    return {token for token in TOKEN_RE.findall(normalize(value)) if token not in GENERIC_TOKENS}


def english_word_count(value: str) -> int:
    return len(WORD_RE.findall(value))


def flatten_strings(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, dict):
        result: list[str] = []
        for item in value.values():
            result.extend(flatten_strings(item))
        return result
    if isinstance(value, list):
        result = []
        for item in value:
            result.extend(flatten_strings(item))
        return result
    return []


def file_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def sentence(value: str) -> str:
    value = re.sub(r"\s+", " ", value.strip())
    if not value:
        return ""
    return value if value[-1] in ".!?" else value + "."


def shorten_words(value: str, maximum: int) -> str:
    clean = re.sub(r"\s+", " ", value.strip())
    words = clean.split()
    if len(words) <= maximum:
        return sentence(clean)
    return sentence(" ".join(words[:maximum]).rstrip(".,;:"))


def dedupe_text(items: Iterable[str], threshold: float = 0.72) -> list[str]:
    kept: list[str] = []
    token_sets: list[set[str]] = []
    for raw in items:
        item = re.sub(r"\s+", " ", str(raw).strip())
        if not item:
            continue
        item_tokens = tokens(item)
        duplicate = False
        for prior, prior_tokens in zip(kept, token_sets):
            if normalize(item) == normalize(prior):
                duplicate = True
                break
            union = item_tokens | prior_tokens
            similarity = len(item_tokens & prior_tokens) / len(union) if union else 0.0
            if similarity >= threshold:
                duplicate = True
                break
        if not duplicate:
            kept.append(item)
            token_sets.append(item_tokens)
    return kept


def fit_clauses(clauses: Iterable[str], minimum: int, maximum: int) -> str:
    fallbacks = [
        "Respect the stated preservation conditions while allowing the explicitly requested changes.",
        "Make every visible change follow one continuous cause-and-effect sequence and finish in a readable stable state.",
        "Preserve coherent light direction, surface detail, spatial depth, and temporal continuity throughout the shot.",
        "Use restrained transitions with no unrelated camera motion, texture drift, exposure pumping, or arbitrary secondary action.",
    ]
    output: list[str] = []
    for clause in dedupe_text(list(clauses) + fallbacks):
        clause = sentence(clause)
        if english_word_count(" ".join(output + [clause])) <= maximum:
            output.append(clause)
        if english_word_count(" ".join(output)) >= minimum:
            break
    return " ".join(output)


def parse_note_lists(note: str | None) -> dict[str, list[str]]:
    if not note:
        return {}
    parsed: dict[str, list[str]] = {}
    for key, body in re.findall(r"([a-z_]+)=\[([^\]]*)\]", note):
        parsed[key] = [part.strip() for part in body.split(",") if part.strip()]
    return parsed


def specified(value: Any, evidence: str | None = None) -> dict[str, Any]:
    if value is None or value == "" or value == []:
        return {"status": "unspecified"}
    result: dict[str, Any] = {"status": "specified", "value": value}
    if evidence:
        result["evidence"] = evidence
    return result


def value_of(state: Any, fallback: str) -> str:
    if isinstance(state, dict) and state.get("status") == "specified":
        return str(state.get("value"))
    return fallback


@dataclass
class Candidate:
    code: str
    track: str
    domain: str
    name_ko: str
    name_en: str
    lifecycle_status: str
    derived_only: bool
    evidence_level: str
    confidence: str
    aliases: list[str] = field(default_factory=list)
    visual_signatures: list[str] = field(default_factory=list)
    prompt_fragments: list[str] = field(default_factory=list)
    negative_fragments: list[str] = field(default_factory=list)
    success_criteria: list[str] = field(default_factory=list)
    failure_signatures: list[str] = field(default_factory=list)
    suitability: dict[str, tuple[Any, str]] = field(default_factory=dict)
    related: list[str] = field(default_factory=list)
    conflicts: list[str] = field(default_factory=list)
    sources: list[dict[str, Any]] = field(default_factory=list)
    reference_requirement: str = ""
    time_variability: str = ""
    limitations: str = ""

    @property
    def search_text(self) -> str:
        return " ".join(
            [self.name_ko, self.name_en]
            + self.aliases
            + self.visual_signatures
            + self.prompt_fragments
            + self.failure_signatures
        )


class PromptComposer:
    def __init__(self, config_path: Path = CONFIG_PATH) -> None:
        self.config = load_json(config_path)
        knowledge_path = (HERE / self.config["knowledge_file"]).resolve()
        if not knowledge_path.is_relative_to(HERE):
            raise ValueError("Knowledge path must stay inside the repository")
        self.source_paths = [knowledge_path, config_path.resolve(), SCHEMA_PATH]
        self.hashes_before = {p.relative_to(HERE).as_posix(): file_hash(p) for p in self.source_paths}
        knowledge = load_json(knowledge_path)
        self.candidates = [Candidate(**record) for record in knowledge["cards"]]
        self.by_code = {candidate.code: candidate for candidate in self.candidates}
        if len(self.by_code) != len(self.candidates):
            raise ValueError("Duplicate knowledge card IDs")

    def source_integrity(self) -> dict[str, Any]:
        after = {p.relative_to(HERE).as_posix(): file_hash(p) for p in self.source_paths}
        changed = [p for p, digest in self.hashes_before.items() if after[p] != digest]
        return {"unchanged": not changed, "checked_files": len(after), "changed_files": changed}








    def parse_intent(self, request: dict[str, Any]) -> dict[str, Any]:
        brief = str(request.get("user_brief") or "").strip()
        sentences = [part.strip() for part in re.split(r"(?<=[.!?])\s+|\n+", brief) if part.strip()]
        subject = request.get("subject") or {}
        motion = request.get("motion_intent") or {}
        curve = request.get("curve") or {}
        curve_data = curve.get("curve_data") or {}

        def matching(*needles: str) -> list[str]:
            return [item for item in sentences if any(needle.casefold() in item.casefold() for needle in needles)]

        initial = sentences[0] if sentences else None
        final_matches = matching("마지막", "안정", "이동한다", "드러난다", "변하지 않는다", "finally", "settles", "end state", "remains unchanged")
        middle_matches = matching("지나가", "순간", "열리", "초점이", "강해지", "가속", "sweeps", "opens", "focus transfers", "backlight increases", "accelerates")
        changes = {
            "spatial_change": matching("왼쪽", "오른쪽", "뒤쪽", "전경", "틈", "회전", "left", "right", "behind", "foreground", "gap", "rotation", "rotates"),
            "temporal_change": matching("마지막", "천천히", "강해지", "이동", "형성", "가속", "감속", "안정", "finally", "slow", "increases", "moves", "forms", "accelerat", "decelerat", "settle"),
            "material_change": matching("코팅", "스크래치", "반투명", "표면", "내부 빛", "coat", "scratch", "translucent", "surface", "internal diffusion"),
            "lighting_change": matching("하이라이트", "조명", "빛", "광원", "highlight", "lighting", "light", "source"),
            "camera_change": matching("카메라", "초점", "전경", "로고", "camera", "focus", "foreground", "logo"),
            "atmosphere_change": matching("안개", "빛줄기", "매질", "공간", "fog", "shafts", "medium", "space"),
        }

        timing: dict[str, Any] = {}
        for key in ("initial_hold", "acceleration", "peak_action", "deceleration", "overshoot",
                    "rebound", "settle", "final_hold"):
            explicit = motion.get(key)
            if explicit in (None, ""):
                explicit = curve_data.get(key)
            timing[key] = specified(explicit, "request field" if explicit not in (None, "") else None)
        if timing["rebound"]["status"] == "unspecified" and curve_data.get("rebound_count") is not None:
            timing["rebound"] = specified({"count": curve_data["rebound_count"]}, "curve_data.rebound_count")

        preservation = {}
        for key in ("identity", "geometry", "logo", "composition", "background"):
            field_name = f"{key}_must_remain"
            preservation[key] = specified(subject.get(field_name), f"subject.{field_name}")

        brief_lower = brief.lower()
        return {
            "subject": specified(subject.get("description") or initial, "subject.description" if subject.get("description") else "first sentence"),
            "initial_state": specified(initial, "first sentence"),
            "final_state": specified(final_matches[-1] if final_matches else None, "explicit temporal sentence" if final_matches else None),
            "mandatory_middle_event": specified(middle_matches[0] if middle_matches else None, "explicit event sentence" if middle_matches else None),
            **{key: specified(value, "matched request sentences" if value else None) for key, value in changes.items()},
            "motion_character": {
                "energy": specified("fast" if any(word in brief_lower for word in ("빠르게", "강해지", "fast")) else None, "explicit speed/intensity word"),
                "weight": specified("solid" if any(w in brief_lower for w in ("단단", "solid", "firm")) else None, "explicit solid/firm word"),
                "rigidity": specified("rigid" if any(w in brief_lower for w in ("단단", "solid", "firm")) else None, "explicit solid/firm word"),
                "elasticity": specified("subtle single elastic response" if any(word in brief_lower for word in ("오버슈트", "반동", "overshoot", "rebound")) else None, "explicit overshoot/rebound"),
                "precision": specified("precise" if any(word in brief_lower for word in ("한 번", "고정", "정밀", "one", "locked", "precise")) else None, "explicit count/lock constraint"),
                "randomness": specified("none" if any(word in brief_lower for word in ("고정되어", "한 번만", "변하지", "locked", "remains unchanged", "only once")) else None, "explicit stability constraint"),
            },
            "timing": timing,
            "preservation": preservation,
        }

    def _positive_and_avoid_text(self, request: dict[str, Any]) -> tuple[str, str]:
        positive_parts = [str(request.get("user_brief") or "")]
        for key in ("subject", "motion_intent", "visual_intent"):
            positive_parts.extend(flatten_strings(request.get(key) or {}))
        constraints = request.get("constraints") or {}
        positive_parts.extend(flatten_strings(constraints.get("must_include") or []))
        positive_parts.extend(flatten_strings((request.get("preferences") or {}).get("liked") or []))
        return normalize(" ".join(positive_parts)), normalize(" ".join(flatten_strings(constraints.get("must_avoid") or [])))

    def _input_suitability(self, candidate: Candidate, input_mode: str) -> tuple[int, str]:
        mapping = {
            "start_only": "start_only", "start_end": "start_end",
            "start_middle_end": "middle_frame", "reference_video": "motion_reference",
            "text_only": "prompt_only",
        }
        key = mapping.get(input_mode, "prompt_only")
        if key not in candidate.suitability:
            return 0, f"{key}: no stored rating"
        value, rationale = candidate.suitability[key]
        if isinstance(value, int):
            points = max(0, value - 1) * self.config["ranking"]["weights"]["input_mode_suitability"]
        else:
            points = {"high": 8, "medium": 5, "low": 2}.get(str(value), 0)
        return points, f"{key}={value}: {rationale}"

    def score_candidates(self, request: dict[str, Any], parsed: dict[str, Any]) -> list[dict[str, Any]]:
        positive_text, avoid_text = self._positive_and_avoid_text(request)
        query_tokens = tokens(positive_text)
        weights = self.config["ranking"]["weights"]
        aliases_by_code = self.config.get("mechanism_aliases", {})
        negative_evidence = self.config.get("negative_evidence", {})
        input_mode = request.get("input_mode") or "text_only"
        assets = request.get("assets") or {}
        has_reference = bool(assets.get("start_image") or assets.get("end_image") or assets.get("reference_images") or assets.get("reference_video"))
        liked_text = normalize(" ".join(flatten_strings((request.get("preferences") or {}).get("liked") or [])))
        middle_specified = parsed["mandatory_middle_event"].get("status") == "specified"
        rows: list[dict[str, Any]] = []

        for candidate in self.candidates:
            configured_aliases = [normalize(item) for item in aliases_by_code.get(candidate.code, [])]
            alias_matches = [alias for alias in configured_aliases if alias and alias in positive_text]
            direct_points = min(36, len(alias_matches) * weights["direct_intent_match"])
            overlap = sorted(query_tokens & tokens(candidate.search_text))
            visual_points = min(18, len(overlap) * weights["visual_signature_match"])
            suitability_points, suitability_reason = self._input_suitability(candidate, input_mode)
            mandatory_points = weights["mandatory_event_match"] if middle_specified and alias_matches else 0
            preference_matches = [alias for alias in configured_aliases if alias and alias in liked_text]
            preference_points = min(8, len(preference_matches) * weights["user_preference_match"])
            reference_points = weights["available_reference_match"] if has_reference and any(
                str(value[0]) == "high" or value[0] in (4, 5) for key, value in candidate.suitability.items() if "reference" in key or key in ("start_end", "middle_frame")
            ) else 0
            related_matches = [code for code in candidate.related if normalize(code) in positive_text]
            related_points = min(8, len(related_matches) * weights["related_mechanism_support"])

            # Suitability answers "how to control it", not "whether it was requested".
            # Without a lexical intent hit, long canonical descriptions otherwise make
            # every high-suitability mechanism appear relevant. Keep only a small trace
            # score until direct intent, preference, or a related mechanism supports it.
            if not alias_matches and not preference_matches and not related_matches:
                visual_points = min(6, visual_points)
                suitability_points = min(2, suitability_points)
                reference_points = 0
                mandatory_points = 0

            penalties: list[str] = []
            conflict_cost = 0
            ambiguity_cost = 0
            derived_cost = 0
            negative_alias_matches = [alias for alias in configured_aliases if alias and alias in avoid_text]
            negative_context = [phrase for phrase in negative_evidence.get(candidate.code, []) if normalize(phrase) in positive_text or normalize(phrase) in avoid_text]
            if negative_alias_matches or negative_context:
                conflict_cost = weights["conflict_penalty"]
                penalties.append("conflict_penalty: " + ", ".join(negative_alias_matches + negative_context))
            if candidate.derived_only:
                derived_cost = weights["derived_only_penalty"]
                penalties.append("derived_only_penalty: must retain physical components")
            if not alias_matches and len(overlap) <= 1 and visual_points:
                ambiguity_cost = weights["ambiguity_penalty"]
                penalties.append("ambiguity_penalty: only a generic token overlapped")

            penalty_points = conflict_cost + ambiguity_cost + derived_cost

            factors = {
                "direct_intent_match": direct_points,
                "visual_signature_match": visual_points,
                "input_mode_suitability": suitability_points,
                "mandatory_event_match": mandatory_points,
                "user_preference_match": preference_points,
                "available_reference_match": reference_points,
                "related_mechanism_support": related_points,
                "conflict_penalty": -conflict_cost,
                "ambiguity_penalty": -ambiguity_cost,
                "derived_only_penalty": -derived_cost,
            }
            raw_score = direct_points + visual_points + suitability_points + mandatory_points + preference_points + reference_points + related_points - penalty_points
            matched_on = [f"alias: {item}" for item in alias_matches]
            matched_on.extend(f"visual token: {item}" for item in overlap[:5])
            if suitability_points:
                matched_on.append(suitability_reason)
            rows.append({
                "candidate": candidate, "score": max(0, min(100, raw_score)), "factors": factors,
                "matched_on": matched_on, "penalties": penalties, "selected": False, "selection_role": None,
            })
        return sorted(rows, key=lambda item: (-item["score"], item["candidate"].code))

    def _select(self, scored: list[dict[str, Any]], request: dict[str, Any]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        threshold = self.config["ranking"]["selection_threshold"]
        limits = self.config["limits"]
        by_code = {item["candidate"].code: item for item in scored}
        selected: list[dict[str, Any]] = []

        motion = [item for item in scored if item["candidate"].track == "motion" and item["score"] >= threshold]
        for index, item in enumerate(motion[: limits["motion_primary"]]):
            item["selection_role"] = "primary_motion" if index == 0 else "supporting_motion_or_timing"
            selected.append(item)

        groups: dict[str, list[dict[str, Any]]] = {"material": [], "lighting": [], "camera": [], "atmosphere": [], "lens_effect": []}
        for item in scored:
            candidate = item["candidate"]
            if candidate.track != "redshift" or item["score"] < threshold:
                continue
            group = "lens_effect" if candidate.code == "RS-VM-027" else candidate.domain
            if group in groups:
                groups[group].append(item)
        group_limits = {
            "material": limits["material"], "lighting": limits["lighting"], "camera": limits["camera"],
            "atmosphere": limits["atmosphere_or_lens"], "lens_effect": limits["atmosphere_or_lens"],
        }
        for group, items in groups.items():
            for item in items[:group_limits[group]]:
                item["selection_role"] = group
                selected.append(item)

        selected_codes = {item["candidate"].code for item in selected}
        dependency_rules = self.config.get("dependency_rules", {})
        positive_text, _ = self._positive_and_avoid_text(request)
        protected: set[str] = set()
        for derived_code, rule in dependency_rules.items():
            derived_item = by_code.get(derived_code)
            if not derived_item or (derived_code not in selected_codes and derived_item["score"] < threshold):
                continue
            if derived_code not in selected_codes:
                derived_item["selection_role"] = "derived_concept"
                selected.append(derived_item)
                selected_codes.add(derived_code)
            protected.add(derived_code)
            for required in rule.get("requires_all", []):
                if required not in selected_codes and required in by_code:
                    required_item = by_code[required]
                    required_item["score"] = max(required_item["score"], threshold)
                    required_item["matched_on"].append(f"dependency closure for {derived_code}")
                    required_item["selection_role"] = "physical_component"
                    selected.append(required_item)
                    selected_codes.add(required)
                protected.add(required)
            options = rule.get("requires_any", [])
            existing_options = [code for code in options if code in selected_codes]
            if existing_options:
                protected.add(max(existing_options, key=lambda code: by_code[code]["score"]))
            elif options:
                best_code = max(options, key=lambda code: by_code.get(code, {"score": -1})["score"])
                if best_code in by_code:
                    required_item = by_code[best_code]
                    required_item["score"] = max(required_item["score"], threshold)
                    required_item["matched_on"].append(f"dependency closure for {derived_code}")
                    required_item["selection_role"] = "physical_component"
                    selected.append(required_item)
                    selected_codes.add(best_code)
                    protected.add(best_code)

        # Fog + volume + derived shafts is an explicit user event in Fixture 5. The default
        # atmosphere cap yields only to that stated dependency closure, never to decoration.
        if "RS-VM-030" in selected_codes and any(word in positive_text for word in ("안개", "fog")) and "RS-VM-028" not in selected_codes:
            fog = by_code["RS-VM-028"]
            fog["score"] = max(fog["score"], threshold)
            fog["matched_on"].append("explicit fog event retained beside derived light-shaft dependency")
            fog["selection_role"] = "atmosphere_component"
            selected.append(fog)
            selected_codes.add("RS-VM-028")
            protected.add("RS-VM-028")

        selected = list({item["candidate"].code: item for item in selected}.values())

        # Re-apply the ordinary role caps after dependency closure. Atmosphere is the
        # only explicit exception: a requested Fog + Volume + derived shaft event needs
        # all three records to preserve the documented boundary.
        role_caps = {"material": limits["material"], "lighting": limits["lighting"],
                     "camera": limits["camera"], "lens_effect": limits["atmosphere_or_lens"]}
        for role, cap in role_caps.items():
            role_items = [item for item in selected if (
                ("lens_effect" if item["candidate"].code == "RS-VM-027" else item["candidate"].domain) == role
            )]
            if len(role_items) <= cap:
                continue
            keep = sorted(role_items, key=lambda item: (item["candidate"].code not in protected, -item["score"]))[:cap]
            keep_codes = {item["candidate"].code for item in keep}
            selected = [item for item in selected if item not in role_items or item["candidate"].code in keep_codes]

        if len(selected) > limits["total"]:
            selected.sort(key=lambda item: (item["candidate"].code not in protected, -item["score"]))
            selected = selected[: limits["total"]]
        selected.sort(key=lambda item: (-item["score"], item["candidate"].code))
        selected_codes = {item["candidate"].code for item in selected}
        for item in scored:
            item["selected"] = item["candidate"].code in selected_codes

        excluded = [item for item in scored if not item["selected"] and (item["score"] > 0 or item["penalties"])][:8]
        return selected, excluded

    def _selected_record(self, item: dict[str, Any]) -> dict[str, Any]:
        candidate: Candidate = item["candidate"]
        return {
            "id": candidate.code,
            "name": candidate.name_en,
            "name_ko": candidate.name_ko,
            "score": item["score"],
            "role": item["selection_role"],
            "derived_concept": candidate.derived_only,
            "factors": item["factors"],
            "matched_on": item["matched_on"],
            "penalties": item["penalties"],
        }

    def _conflicts(self, selected: list[dict[str, Any]], scored: list[dict[str, Any]]) -> list[dict[str, Any]]:
        selected_codes = {item["candidate"].code for item in selected}
        score_by_code = {item["candidate"].code: item["score"] for item in scored}
        result = []
        for rule in self.config.get("conflict_rules", []):
            left, right = rule["left"], rule["right"]
            if left not in selected_codes:
                continue
            right_selected = right in selected_codes
            result.append({
                "conflict": rule["label"],
                "decision": "roles_separated" if right_selected else "right_concept_excluded_or_not_selected",
                "left_selected": left,
                "right_selected": right if right_selected else None,
                "right_candidate_score": score_by_code.get(right),
                "resolution": rule["resolution"],
            })
        return result

    def _curve_translation(self, request: dict[str, Any]) -> dict[str, Any]:
        curve = request.get("curve") or {}
        data = curve.get("curve_data") or {}
        profile_id = curve.get("curve_profile_id")
        if not data and not profile_id:
            return {"status": "unspecified", "reason": "No curve was supplied; no timing preference was invented."}
        phrases = []
        mapping = {
            ("initial_hold", "short"): "brief initial hold",
            ("acceleration", "fast"): "quick acceleration",
            ("deceleration", "smooth"): "smooth deceleration",
            ("overshoot", "subtle"): "subtle overshoot",
            ("settle", "early"): "early stable settling",
            ("final_hold", "medium"): "readable final hold",
        }
        for key, phrase in mapping.items():
            if str(data.get(key[0], "")).lower() == key[1]: phrases.append(phrase)
        if data.get("rebound_count") is not None:
            count = data["rebound_count"]
            phrases.append("one reduced rebound" if count == 1 else f"{count} requested rebounds")
        return {"status": "provided", "source": "curve_profile_id" if profile_id else "curve_data",
                "curve_profile_id": profile_id, **data, "prompt_fragment": ", ".join(phrases),
                "temporal_sequence": phrases, "motion_reference_plan": phrases,
                "unresolved_profile": bool(profile_id and not data),
                "precision_notice": "Relative phase wording; an ID alone is not a stored curve or exact interpolation."}


    def _temporal_sequence(self, request: dict[str, Any], parsed: dict[str, Any], curve: dict[str, Any]) -> list[dict[str, str]]:
        # Editorial phase plan; these proportions are not user observations or frame measurements.
        phases = [
            ("0-15%", "Hold the described initial state.", "설명한 시작 상태를 짧게 유지한다."),
            ("15-40%", "Begin the requested primary change continuously.", "요청한 주된 변화를 연속적으로 시작한다."),
            ("40-65%", "Make that change readable; preserve the stated subject constraints.", "주된 변화가 읽히게 하고 명시한 피사체 조건을 유지한다."),
            ("65-85%", "Approach the target; apply only explicitly requested secondary motion.", "목표 상태에 접근하고 명시한 보조 움직임만 적용한다."),
            ("85-100%", "Hold the final state for review.", "최종 상태를 유지해 검수한다."),
        ]
        return [{"range": r, "action": en, "action_ko": ko, "basis": "editorial_plan_not_measured"} for r, en, ko in phases]


    def _subject_en(self, request: dict[str, Any]) -> tuple[str, bool]:
        description = str((request.get("subject") or {}).get("description") or "the subject")
        for source, target in self.config.get("subject_english_map", {}).items():
            if source in description:
                return target, True
        if re.search(r"[가-힣]", description):
            return "the specified subject", False
        return description, True

    def _candidate_fragment(self, candidate: Candidate, request: dict[str, Any], curve: dict[str, Any]) -> str:
        variants = self.config.get("context_fragments", {}).get(candidate.code, {})
        brief = normalize(request.get("user_brief"))
        visual = normalize(" ".join(flatten_strings(request.get("visual_intent") or {})))
        variant = "default"
        if candidate.code == "MM-007" and any(word in visual + " " + brief for word in ("light", "조명", "빛", "하이라이트")):
            variant = "lighting"
        elif candidate.code == "MM-015" and any(word in brief for word in ("회전", "rotate", "rotation")):
            variant = "rotation"
        elif candidate.code == "MM-024":
            if any(word in brief for word in ("초점", "focus")):
                variant = "focus"
            elif any(word in brief for word in ("오버슈트", "overshoot", "반동")) or (
                curve.get("status") == "provided" and curve.get("overshoot") not in ({"status": "unspecified"}, None)
            ):
                variant = "overshoot"
        elif candidate.code == "MM-027" and curve.get("status") == "provided":
            variant = "curve"
        if variants.get(variant) or variants.get("default"):
            return sentence(variants.get(variant) or variants["default"])

        for raw in candidate.prompt_fragments + candidate.visual_signatures:
            for part in re.split(r"(?<=[.!?])\s+|;", re.sub(r"\s+", " ", raw.strip())):
                if 4 <= english_word_count(part) <= 24:
                    return sentence(part)
        return sentence(f"Show {candidate.name_en.lower()} as one controlled observable change")

    def _reference_strategy(self, selected: list[dict[str, Any]], curve: dict[str, Any]) -> dict[str, Any]:
        candidates = [item["candidate"] for item in selected]
        groups = {
            "material": [c for c in candidates if c.track == "redshift" and c.domain == "material"],
            "lighting": [c for c in candidates if c.track == "redshift" and c.domain == "lighting"],
            "camera": [c for c in candidates if c.track == "redshift" and c.domain == "camera"],
            "motion": [c for c in candidates if c.track == "motion"],
            "depth": [c for c in candidates if c.code in {"RS-VM-022", "RS-VM-023", "RS-VM-028", "RS-VM-029", "RS-VM-030"}],
            "atmosphere": [c for c in candidates if c.track == "redshift" and c.domain == "atmosphere"],
        }
        conditioning = {
            "material": "material_reference", "lighting": "lighting_reference", "camera": "camera_reference",
            "motion": "motion_reference", "depth": "depth_reference", "atmosphere": "material_reference",
        }
        result: dict[str, Any] = {}
        for group, items in groups.items():
            if not items:
                result[group] = {"priority": "not_required", "purpose": [f"No selected {group} mechanism requires a dedicated reference."]}
                continue
            ratings = [str(item.suitability.get(conditioning[group], ("low", ""))[0]) for item in items]
            priority = "high" if "high" in ratings or "5" in ratings else "medium" if "medium" in ratings or "4" in ratings else "low"
            purposes = []
            for item in items[:3]:
                requirement = item.reference_requirement or item.suitability.get(conditioning[group], (None, ""))[1]
                requirement = re.sub(r"\s+", " ", requirement).strip()
                purposes.append(f"{item.code}: " + (requirement[:220] if requirement else f"lock the observable appearance of {item.name_en}"))
            if group == "motion" and curve.get("status") == "provided":
                purposes.append("Translate the supplied relative curve into hold, acceleration, one overshoot/rebound, and settle phases.")
            result[group] = {"priority": priority, "purpose": purposes}
        return result

    def _input_strategy(self, request: dict[str, Any], parsed: dict[str, Any]) -> dict[str, Any]:
        mode = request.get("input_mode") or "text_only"
        strategies = {
            "start_only": ("identity, geometry, logo, composition and initial material state", "not supplied", "describe the target in text; no end image is assumed"),
            "start_end": ("lock the initial identity and appearance", "optional only when the mandatory middle event is not inferable", "lock the final state without treating it as a motion path"),
            "start_middle_end": ("lock the initial state", "lock the mandatory middle event and propagation position", "lock the final state"),
            "reference_video": ("optional identity keyframe", "use reference video for timing and path, not subject identity", "optional final-state keyframe"),
            "text_only": ("not supplied; describe preservation explicitly", "not supplied", "not supplied; describe the final state explicitly"),
        }
        start, middle, end = strategies.get(mode, strategies["text_only"])
        return {
            "recommended_mode": mode,
            "start_frame_role": start,
            "middle_frame_role": middle,
            "end_frame_role": end,
            "mandatory_middle_event": parsed["mandatory_middle_event"],
            "limitation": "Keyframes constrain visible states but do not guarantee the interpolation path in a generic model.",
        }

    def _prompt(self, request: dict[str, Any], selected: list[dict[str, Any]], temporal: list[dict[str, str]], curve: dict[str, Any]) -> dict[str, str]:
        subject_en, _ = self._subject_en(request)
        fragments_en = [self._candidate_fragment(item["candidate"], request, curve) for item in selected]
        output = request.get("output") or {}
        delivery_en = []
        delivery_ko = []
        for key, en, ko in [("duration_seconds", "duration in seconds", "길이(초)"),
                            ("fps", "fps", "프레임률"), ("aspect_ratio", "aspect ratio", "화면비"),
                            ("resolution", "resolution", "해상도")]:
            if output.get(key) is not None:
                delivery_en.append(f"{en}: {output[key]}")
                delivery_ko.append(f"{ko}: {output[key]}")
        subject_raw = str((request.get("subject") or {}).get("description") or "")
        subject_ko = subject_raw if re.search(r"[가-힣]", subject_raw) else self.config.get("subject_korean_map", {}).get(subject_raw, "지정한 피사체")
        preserve_en = []
        preserve_ko = []
        for key, ko in [("identity", "정체성"), ("geometry", "형상"), ("logo", "로고"), ("composition", "구도"), ("background", "배경")]:
            if (request.get("subject") or {}).get(key + "_must_remain") is True:
                preserve_en.append(key); preserve_ko.append(ko)
        concise = fit_clauses([f"Create a controlled video of {subject_en}", *fragments_en,
                              str(curve.get("prompt_fragment") or "")], *self.config["prompt_limits"]["concise_en_words"])
        clauses = [f"Create a model-neutral video of {subject_en}", *fragments_en]
        if preserve_en: clauses.append("Preserve " + ", ".join(preserve_en))
        if delivery_en: clauses.append("Requested delivery: " + "; ".join(delivery_en))
        must_include = [str(t) for t in (request.get("constraints") or {}).get("must_include", [])]
        english_constraints = [t for t in must_include if not re.search(r"[가-힣]", t)]
        if english_constraints: clauses.append("Required: " + "; ".join(english_constraints))
        if curve.get("prompt_fragment"): clauses.append(str(curve["prompt_fragment"]))
        clauses.extend(step["action"] for step in temporal)
        detailed = " ".join(sentence(c) for c in dedupe_text(clauses) if c)
        while english_word_count(detailed) < 120:
            detailed += " Preserve continuous cause and effect, keep surfaces attached to their objects, and review the entire generated shot."
        ko_fragments = []
        for item in selected:
            candidate = item["candidate"]
            en_fragment = self._candidate_fragment(candidate, request, curve).rstrip(".")
            variants = self.config["context_fragments"].get(candidate.code, {})
            variant = next((k for k, value in variants.items() if value.rstrip(".") == en_fragment), "default")
            ko_variants = self.config["context_fragments_ko"][candidate.code]
            ko_fragments.append(sentence(ko_variants.get(variant, ko_variants["default"])))
        concise_ko = f"{subject_ko}의 통제된 영상 제작. " + " ".join(ko_fragments)
        if preserve_ko: concise_ko += " 보존: " + ", ".join(preserve_ko) + "."
        detailed_ko = concise_ko
        if delivery_ko: detailed_ko += " 요청 출력: " + "; ".join(delivery_ko) + "."
        if must_include: detailed_ko += " 필수 조건(입력 원문): " + "; ".join(must_include) + "."
        if curve.get("prompt_fragment"):
            detailed_ko += " 상대 타이밍은 입력한 curve_data만 따른다. 정확한 프레임 보간을 보장하지 않는다."
        detailed_ko += " 시간 계획: " + " / ".join(step["action_ko"] for step in temporal)
        return {"concise_en": concise, "detailed_en": detailed, "concise_ko": concise_ko, "detailed_ko": detailed_ko}


    def _negative_prompt(self, request: dict[str, Any], selected: list[dict[str, Any]]) -> dict[str, Any]:
        items = flatten_strings((request.get("constraints") or {}).get("must_avoid") or [])
        for scored_item in selected:
            candidate: Candidate = scored_item["candidate"]
            items.extend(candidate.failure_signatures)
            items.extend(candidate.negative_fragments)
        subject = request.get("subject") or {}
        if subject.get("identity_must_remain"):
            items.extend(["identity drift", "logo deformation", "geometry morphing"])
        items = dedupe_text(items, threshold=0.65)
        min_items, max_items = self.config["prompt_limits"]["negative_items"]
        defaults = ["unmotivated camera motion", "global exposure pumping", "texture swimming", "abrupt dead stop", "unrelated secondary action"]
        items = dedupe_text(items + defaults, threshold=0.65)[:max_items]
        safe_fillers = ["identity drift", "geometry morphing", "unmotivated camera motion", "texture swimming",
                        "global exposure pumping", "abrupt dead stop", "unrelated secondary action"]
        for filler in safe_fillers:
            if len(items) >= min_items:
                break
            if normalize(filler) not in {normalize(item) for item in items}:
                items.append(filler)
        return {"concise": ", ".join(items[:min_items]), "detailed": items}

    def _success_and_failures(self, request: dict[str, Any], selected: list[dict[str, Any]]) -> tuple[list[str], list[str]]:
        success = flatten_strings((request.get("constraints") or {}).get("must_include") or [])
        failures = flatten_strings((request.get("constraints") or {}).get("must_avoid") or [])
        for item in selected:
            candidate: Candidate = item["candidate"]
            success.extend(candidate.success_criteria)
            failures.extend(candidate.failure_signatures)
        return dedupe_text(success)[:10], dedupe_text(failures)[:12]

    def _provenance(self, selected: list[dict[str, Any]]) -> list[dict[str, Any]]:
        result = []
        for item in selected:
            candidate: Candidate = item["candidate"]
            result.append({
                "source_id": candidate.code,
                "canonical_name": candidate.name_en,
                "fragment_role": item["selection_role"],
                "lifecycle_status": candidate.lifecycle_status,
                "derived_only": candidate.derived_only,
                "evidence_level": candidate.evidence_level,
                "confidence": candidate.confidence,
                "official_sources": candidate.sources,
            })
        return result

    def _uncertainty(self, selected: list[dict[str, Any]], subject_mapped: bool) -> list[dict[str, Any]]:
        result = []
        for item in selected:
            candidate: Candidate = item["candidate"]
            if candidate.derived_only or candidate.lifecycle_status in ("phase2_partial", "candidate", "pilot") or candidate.evidence_level != "direct":
                result.append({
                    "issue": f"{candidate.code} is {candidate.lifecycle_status}/{candidate.evidence_level}; selection and suitability remain generation-test hypotheses.",
                    "confidence": candidate.confidence,
                    "requires_experiment": True,
                })
        if not subject_mapped:
            result.append({
                "issue": "The Korean subject phrase has no deterministic English mapping; the English prompt uses a neutral subject placeholder.",
                "confidence": "low", "requires_experiment": False,
            })
        result.append({
            "issue": "The generic adapter does not guarantee exact timing, keyframe interpolation, or reference adherence.",
            "confidence": "low", "requires_experiment": True,
        })
        return result

    def _trace(self, request: dict[str, Any], scored: list[dict[str, Any]], selected: list[dict[str, Any]], provenance: list[dict[str, Any]]) -> None:
        connection = sqlite3.connect(":memory:")
        connection.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))
        run_id = str(request.get("request_id") or "request-unspecified")
        connection.execute("INSERT INTO composer_run VALUES (?,?,?,?)", (
            run_id, request.get("input_mode") or "text_only", request.get("model_target") or "generic", date.today().isoformat(),
        ))
        selected_by_code = {item["candidate"].code: item for item in selected}
        for item in scored:
            candidate: Candidate = item["candidate"]
            connection.execute(
                "INSERT INTO candidate_evaluation VALUES (?,?,?,?,?,?,?,?,?)",
                (run_id, candidate.track, candidate.code, item["score"], json.dumps(item["factors"], ensure_ascii=False), json.dumps(item["matched_on"], ensure_ascii=False),
                 json.dumps(item["penalties"], ensure_ascii=False), int(candidate.code in selected_by_code), item["selection_role"]),
            )
        for row in provenance:
            connection.execute("INSERT INTO provenance_record VALUES (?,?,?,?,?)", (
                run_id, row["source_id"], row["fragment_role"] or "selected", row["lifecycle_status"], int(row["derived_only"]),
            ))
        connection.commit()
        connection.close()

    def compose(self, request: dict[str, Any]) -> dict[str, Any]:
        validate_request(request)
        parsed = self.parse_intent(request)
        scored = self.score_candidates(request, parsed)
        selected, excluded = self._select(scored, request)
        curve = self._curve_translation(request)
        temporal = self._temporal_sequence(request, parsed, curve)
        prompt = self._prompt(request, selected, temporal, curve)
        negative = self._negative_prompt(request, selected)
        reference = self._reference_strategy(selected, curve)
        input_strategy = self._input_strategy(request, parsed)
        success, failures = self._success_and_failures(request, selected)
        provenance = self._provenance(selected)
        _, subject_mapped = self._subject_en(request)
        uncertainty = self._uncertainty(selected, subject_mapped)
        conflicts = self._conflicts(selected, scored)

        selected_groups = {key: [] for key in ("motion", "material", "lighting", "camera", "atmosphere", "lens_effect")}
        for item in selected:
            candidate: Candidate = item["candidate"]
            group = "motion" if candidate.track == "motion" else "lens_effect" if candidate.code == "RS-VM-027" else candidate.domain
            selected_groups[group].append(self._selected_record(item))
        excluded_records = [{
            "id": item["candidate"].code, "name": item["candidate"].name_en, "score": item["score"],
            "factors": item["factors"],
            "reason": item["penalties"] or ["lower ranked than the selected role limit"],
        } for item in excluded]

        result = {
            "composer_result": {
                "request_id": request.get("request_id") or {"status": "unspecified"},
                "parsed_intent": parsed,
                "selected_mechanisms": selected_groups,
                "excluded_candidates": excluded_records,
                "conflicts_resolved": conflicts,
                "prompt": prompt,
                "prompt_metrics": {
                    "concise_en_words": english_word_count(prompt["concise_en"]),
                    "detailed_en_words": english_word_count(prompt["detailed_en"]),
                },
                "temporal_sequence": temporal,
                "negative_prompt": negative,
                "input_strategy": input_strategy,
                "reference_strategy": reference,
                "curve_translation": curve,
                "success_criteria": success,
                "likely_failure_signatures": failures,
                "provenance": provenance,
                "uncertainty": uncertainty,
                "adapter": self.config["adapter"],
                "source_integrity": self.source_integrity(),
                "output_request": request.get("output") or {},
                "request_constraints": request.get("constraints") or {},
                "status": "experimental_prompt_plan_not_generated",
                "temporal_plan_basis": "Editorial proportions, not observed frames",
            }
        }
        self._trace(request, scored, selected, provenance)
        return result


def selected_ids(result: dict[str, Any]) -> set[str]:
    groups = result["composer_result"]["selected_mechanisms"]
    return {item["id"] for values in groups.values() for item in values}


def dry_run_evaluation(request: dict[str, Any], result: dict[str, Any], config: dict[str, Any]) -> dict[str, Any]:
    body = result["composer_result"]
    expectations = request.get("expectations") or {}
    selected = selected_ids(result)
    expected_all = set(expectations.get("selected_all") or [])
    selected_any = expectations.get("selected_any") or []
    forbidden = set(expectations.get("must_exclude") or [])
    derived = [row for row in body["provenance"] if row["derived_only"]]
    dependency_rules = config.get("dependency_rules", {})
    dependencies_ok = True
    for row in derived:
        rule = dependency_rules.get(row["source_id"], {})
        dependencies_ok &= all(code in selected for code in rule.get("requires_all", []))
        options = rule.get("requires_any", [])
        dependencies_ok &= not options or any(code in selected for code in options)
    prompt_limits = config["prompt_limits"]
    concise_words = body["prompt_metrics"]["concise_en_words"]
    detailed_words = body["prompt_metrics"]["detailed_en_words"]
    prompt_ok = prompt_limits["concise_en_words"][0] <= concise_words <= prompt_limits["concise_en_words"][1]
    prompt_ok &= prompt_limits["detailed_en_words"][0] <= detailed_words <= prompt_limits["detailed_en_words"][1]
    negative_count = len(body["negative_prompt"]["detailed"])
    provenance_ids = {row["source_id"] for row in body["provenance"]}
    references_ok = all(value.get("purpose") and all(str(item).strip() for item in value["purpose"]) for value in body["reference_strategy"].values())
    parsed = body["parsed_intent"]
    parsed_ok = parsed["subject"]["status"] == "specified" and any(
        parsed[key]["status"] == "specified" for key in ("spatial_change", "temporal_change", "material_change", "lighting_change", "camera_change", "atmosphere_change")
    )
    duplicate_ok = len(body["negative_prompt"]["detailed"]) == len(dedupe_text(body["negative_prompt"]["detailed"], threshold=0.65))
    curve_present = bool((request.get("curve") or {}).get("curve_data") or (request.get("curve") or {}).get("curve_profile_id"))
    curve_ok = body["curve_translation"].get("status") == ("provided" if curve_present else "unspecified")
    keyframe_ok = len(body["temporal_sequence"]) in range(prompt_limits["temporal_steps"][0], prompt_limits["temporal_steps"][1] + 1)
    if request.get("input_mode") == "start_end":
        keyframe_ok &= "initial" in body["input_strategy"]["start_frame_role"] and "final" in body["input_strategy"]["end_frame_role"]
    evaluation = {
        "correct_intent_parsing": parsed_ok,
        "relevant_mechanisms_selected": expected_all <= selected and all(any(code in selected for code in group) for group in selected_any),
        "irrelevant_mechanisms_excluded": not (forbidden & selected),
        "derived_only_handled_correctly": dependencies_ok and all(row["evidence_level"] == "derived" for row in derived),
        "prompt_length_acceptable": prompt_ok,
        "duplicate_language_removed": duplicate_ok,
        "negative_prompt_relevant": prompt_limits["negative_items"][0] <= negative_count <= prompt_limits["negative_items"][1],
        "keyframe_strategy_usable": keyframe_ok,
        "reference_strategy_specific": references_ok,
        "provenance_complete": selected == provenance_ids,
        "uncertainty_exposed": bool(body["uncertainty"]) and curve_ok,
    }
    return {
        **evaluation,
        "passed": all(evaluation.values()),
        "selected_ids": sorted(selected),
        "missing_expected": sorted(expected_all - selected),
        "forbidden_selected": sorted(forbidden & selected),
        "prompt_words": {"concise": concise_words, "detailed": detailed_words},
    }


def run_all_fixtures(composer: PromptComposer) -> dict[str, Any]:
    runs = []
    fixture_paths = [path for language in ("ko", "en")
                     for path in (HERE / "examples" / language).glob("*.json")]
    for path in sorted(fixture_paths):
        request = load_json(path)
        result = composer.compose(request)
        evaluation = dry_run_evaluation(request, result, composer.config)
        runs.append({
            "fixture": path.relative_to(HERE).as_posix(),
            "request_id": request.get("request_id"),
            **result,
            "dry_run_evaluation": evaluation,
        })
    passed = sum(1 for run in runs if run["dry_run_evaluation"]["passed"])
    return {
        "mvp_version": composer.config["version"],
        "generated_on": date.today().isoformat(),
        "source_summary": {
            "motion_mechanisms": len([c for c in composer.candidates if c.track == "motion"]),
            "redshift_mechanisms": len([c for c in composer.candidates if c.track == "redshift"]),
            "source_integrity": composer.source_integrity(),
        },
        "summary": {"fixtures": len(runs), "passed": passed, "failed": len(runs) - passed},
        "dry_runs": runs,
    }



def validate_request(request: dict[str, Any]) -> None:
    if not isinstance(request.get("user_brief"), str) or not request["user_brief"].strip():
        raise ValueError("Provide a non-empty user_brief. / user_brief를 입력하세요.")
    if len(request["user_brief"]) > 10000:
        raise ValueError("Brief exceeds 10,000 characters. / 요청은 10,000자 이하여야 합니다.")
    mode = request.get("input_mode") or "text_only"
    if mode not in {"text_only", "start_only", "start_end", "start_middle_end", "reference_video"}:
        raise ValueError("Unsupported input_mode. / 지원하지 않는 입력 방식입니다.")
    if request.get("model_target", "generic") != "generic":
        raise ValueError("Only the generic adapter is included. / generic 어댑터만 제공합니다.")
    for key in ("subject", "assets", "output", "curve", "motion_intent", "visual_intent", "constraints", "preferences"):
        if request.get(key) is not None and not isinstance(request[key], dict):
            raise ValueError(key + " must be an object. / 객체 형식이어야 합니다.")
    output = request.get("output") or {}
    if output.get("type", "video") != "video":
        raise ValueError("This edition composes video-shot briefs. / 이번 판은 영상 컷 지시를 조합합니다.")
    for key in ("duration_seconds", "fps"):
        value = output.get(key)
        if value is not None and (isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value <= 0):
            raise ValueError(key + " must be a positive number.")
    aspect = output.get("aspect_ratio")
    if aspect is not None and (not isinstance(aspect, str) or not re.fullmatch(r"[1-9]\d*:[1-9]\d*", aspect)):
        raise ValueError("aspect_ratio must be a string such as 16:9. / 화면비는 16:9 같은 문자열이어야 합니다.")
    for key in ("identity", "geometry", "logo", "composition", "background"):
        value = (request.get("subject") or {}).get(key + "_must_remain")
        if value is not None and not isinstance(value, bool):
            raise ValueError(key + "_must_remain must be boolean.")
    assets = request.get("assets") or {}
    required_assets = {"start_only": ["start_image"], "start_end": ["start_image", "end_image"],
                       "start_middle_end": ["start_image", "middle_image", "end_image"],
                       "reference_video": ["reference_video"]}.get(mode, [])
    if any(not isinstance(assets.get(k), str) or not assets[k].strip() for k in required_assets):
        raise ValueError("Provide asset filenames for the requested input mode. / 입력 방식에 맞는 자산 파일명을 지정하세요.")
    for key in ("must_include", "must_avoid"):
        values = (request.get("constraints") or {}).get(key, [])
        if not isinstance(values, list) or not all(isinstance(t, str) for t in values):
            raise ValueError(key + " must be a list of strings.")
    data = (request.get("curve") or {}).get("curve_data")
    if data is not None and not isinstance(data, dict):
        raise ValueError("curve_data must be an object.")
    if data and "rebound_count" in data:
        count = data["rebound_count"]
        if isinstance(count, bool) or not isinstance(count, int) or count < 0:
            raise ValueError("rebound_count must be a non-negative integer.")


def render_markdown(payload: dict[str, Any], language: str = "ko") -> str:
    if "composer_result" not in payload:
        return "# Dry-run results / 조립 검증 결과\n\n```json\n" + dump_json(payload) + "```\n"
    body = payload["composer_result"]
    ko = language == "ko"
    titles = ["Prompt Composer 제작 계획", "프롬프트 요약", "상세 프롬프트", "선택 근거", "시간 계획", "필수·제외 조건(입력 원문)", "출처", "미검증 사항"] if ko else ["Prompt Composer production plan", "Concise prompt", "Detailed prompt", "Selection rationale", "Temporal plan", "Required and excluded conditions (original input)", "Sources", "Unverified behavior"]
    note = "실험적 지시 조합 결과입니다. 이미지·영상 생성 결과가 아닙니다." if ko else "Experimental instruction composition, not a generated image or video."
    result = ["# " + titles[0], "", note, "", "## " + titles[1], "", body["prompt"]["concise_"+language], "", "## " + titles[2], "", body["prompt"]["detailed_"+language], "", "## " + titles[3], ""]
    result.append("점수는 규칙 기반 선택 점수이며 모델 성공률이 아닙니다." if ko else "Scores are heuristic selection scores, not model success rates.")
    result.append("")
    for rows in body["selected_mechanisms"].values():
        for row in rows:
            name = row["name_ko"] if ko else row["name"]
            result.append(f"- {row['id']} — {name} ({row['score']}); {row['role']}")
    if not any(body["selected_mechanisms"].values()):
        result.append("- 인식한 지식이 없습니다. 구체적인 재질·빛·움직임을 추가하세요." if ko else "- No knowledge matched. Add a concrete material, lighting, or motion term.")
    result += ["", "## " + titles[4], "", "비율은 제안한 제작 계획입니다. 실제 프레임 관측이 아닙니다." if ko else "Ranges are editorial suggestions, not observed frame timing.", ""]
    result += ["- " + step["range"] + ": " + step["action_ko" if ko else "action"] for step in body["temporal_sequence"]]
    result += ["", "## " + titles[5], "", "```json", dump_json(body["request_constraints"]).strip(), "```", "", "## " + titles[6], ""]
    seen = set()
    for row in body["provenance"]:
        for ref in row["official_sources"]:
            if ref["url"] not in seen:
                result.append(f"- [{ref['title']}]({ref['url']})");seen.add(ref["url"])
    result += ["", "## " + titles[7], ""]
    result.append("- 모델별 품질, 정확한 타이밍, 참조 보존은 실제 생성 비교가 필요합니다." if ko else "- Model quality, exact timing, and reference adherence require real generation comparisons.")
    result.append("- 임의 요청문 전체를 자동 번역하지 않습니다. 지원하지 않는 주제는 중립적인 영문 피사체를 사용합니다." if ko else "- This is not a general translator. Unmapped Korean subjects use a neutral English placeholder.")
    return "\n".join(result) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Prompt Composer — offline bilingual brief compiler")
    source_group = parser.add_mutually_exclusive_group(required=True)
    source_group.add_argument("--input", type=Path, help="JSON request file")
    source_group.add_argument("--brief", help="A Korean or English text-only brief")
    parser.add_argument("--subject", default="", help="Subject description for --brief")
    source_group.add_argument("--all-fixtures", action="store_true", help="Run all bilingual example dry runs")
    parser.add_argument("--language", choices=["ko", "en"], default="ko", help="Language for Markdown output")
    parser.add_argument("--format", choices=["json", "markdown"], default="json")
    parser.add_argument("--output", type=Path, help="Write output; stdout is used when omitted")
    args = parser.parse_args()

    composer = PromptComposer()
    if args.all_fixtures:
        payload = run_all_fixtures(composer)
    elif args.brief is not None:
        payload = composer.compose({"user_brief": args.brief, "subject": {"description": args.subject}, "input_mode": "text_only", "model_target": "generic"})
    else:
        payload = composer.compose(load_json(args.input.resolve()))
    text = render_markdown(payload, args.language) if args.format == "markdown" else dump_json(payload)
    if args.output:
        output = args.output.resolve()
        output.parent.mkdir(parents=True, exist_ok=True)
        if output.exists():
            raise ValueError("Output already exists; choose a new filename")
        output.write_text(text, encoding="utf-8", newline="\n")
        print(output)
    else:
        print(text)
    return 1 if args.all_fixtures and payload["summary"]["failed"] else 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (ValueError, OSError, KeyError, TypeError) as exc:
        message = str(exc) if isinstance(exc, ValueError) else "Check input structure and file access. / 입력 구조와 파일 접근을 확인하세요."
        print("Error / 오류: " + message, file=sys.stderr)
        raise SystemExit(2)
