# Prompt Composer public release report

[한국어](RELEASE_REPORT.md) | **English**

Version 0.1.0 · Reviewed 2026-10-06 · [Public repository](https://github.com/bloglluukk-glitch/prompt-composer)

## What is shared

An offline tool that turns a visual intention into material, lighting, motion, focus, timing, and preservation instructions. It combines editorial knowledge informed by C4D and Redshift into Korean and English production prompts. Results include concise and detailed prompts, selected and excluded candidates, selection rationale, sources, uncertainty, and a relative temporal plan.

For example, “Sweep light across a satin-metal product and reveal a thin coat reflection” combines directional highlights, roughness, a separate coat layer, and controlled light size. The detailed prompt retains the requested five seconds, 24fps, 16:9, and geometry/logo preservation. The rules distinguish a coat reflection from whole-object transmission.

## The 40 public files

| Component | Files | Contents |
| --- | ---: | --- |
| Runtime and checks | 4 | Composer, behavioral validator, JSON settings, in-memory trace SQL |
| Public knowledge | 2 | 23 knowledge cards and nine official background sources |
| Bilingual input examples | 12 | Coat reveal, subsurface backlight, micro surface, rack focus, fog/shafts, relative timing; each in two languages |
| Actual composed results | 3 | JSON record of 12 dry runs and readable coat-reveal plans in both languages |
| Input template | 1 | JSON for users to fill in |
| Bilingual documentation | 14 | Introduction, usage, architecture, sources, contributing, changelog, and this report; each in two languages |
| Validation record | 1 | Check results and scope |
| Publication controls | 3 | MIT License, ignore rules, per-file SHA-256 manifest |

This first edition curates four Motion and 19 Redshift cards. It does not publish the complete personal knowledge store or all 60 original cards. Users can run it with Python 3.11+ without extra packages, C4D, Redshift, or a private database. Execution was checked on Windows with Python 3.12.14. [Complete manifest](../UPLOAD_MANIFEST.json)

## What was tested

- 20/20 behavioral checks and 12/12 bilingual example composition dry runs passed.
- All six language pairs select the same knowledge cards; example English prompts contain no residual Korean text.
- Explicit delivery settings, preservation, and exclusions survive composition; unset values and curve behavior are not invented.
- Checks cover generic-word over-selection, subsurface/transmission confusion, and physical components retained for derived shafts.
- Separate working-directory and fresh-copy execution, refusal to overwrite outputs, no network use, and no example image access.
- A release-pack regression that treated stored results as input examples was fixed and rechecked with the results included.

[Validation record](VALIDATION.json) · [Actual composition results](../examples/results/dry_runs.json)

## Pre-publication review and exclusions

The text, JSON, documentation links, and inventory of all 40 public files were reviewed. No actual personal contact details, workstation user paths, or credential patterns were found. Public attribution uses the GitHub handle; commits use the GitHub privacy email. Separate hash comparisons confirm that original files were preserved.

The upload excludes original private SQL, environment files, account/credential files, internal operations, client materials, actual images/videos, and prior private work history. Example image names are role placeholders, with no actual assets included. The new repository starts with fresh history containing only the reviewed files.

Official Maxon documents are linked as background sources; their text and screenshots are not redistributed. Public clauses were rewritten as editorial judgments and experimental hypotheses. MIT applies to this reviewed package, excluding external documents, trademarks, and software. [Sources and claim boundaries](../SOURCES.en.md)

## What remains unverified

Actual generation-provider calls and render comparisons: **zero**. There is no guarantee of generation success, physical accuracy, exact F-Curve reproduction, or support for requested settings in a particular model. Scores are heuristic selection ranks, not success rates. Five relative temporal phases are editorial suggestions. This is not a C4D plugin or scene generator.

English output combines registered knowledge clauses rather than generally translating arbitrary Korean. Unmapped Korean subjects use a neutral English phrase and an uncertainty notice. Additional original constraints are preserved separately; users should review new outputs.

## Start here

```sh
python prompt_composer.py --input examples/en/01_coat_reveal.json --format markdown --language en
python prompt_composer.py --input examples/ko/01_coat_reveal.json --format markdown --language ko
python validate_prompt_composer.py
```

[English usage](USAGE.en.md) · [한국어 사용법](USAGE.md) · [English introduction](../README.en.md) · [한국어 소개](../README.md)
