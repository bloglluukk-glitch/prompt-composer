# Prompt Composer

[Korean](README.md) | **English**

**Turn a visual intention into production instructions you can run and review.**

An offline tool that combines C4D-style motion and timing knowledge with Redshift-style material, lighting, focus, and atmosphere knowledge. It includes Korean and English request examples and prompts in both languages. The result records what was selected or excluded, the selection rationale, background sources, and what remains unverified.

**v0.1.0 / experimental.** It does not generate images, videos, or C4D scenes, and it does not connect to a generation provider or a C4D/Redshift plugin. It composes prompts and a review plan for you to test in a tool of your choice.

## Quick start

Use Python 3.11 or later. The tool uses only Python's standard library; no additional packages are required. Download the repository and run from its directory.

```sh
python prompt_composer.py --input examples/en/01_coat_reveal.json --format markdown --language en
```

Korean output:

```sh
python prompt_composer.py --input examples/ko/01_coat_reveal.json --format markdown --language ko
```

You can also start with a short brief:

```sh
python prompt_composer.py --brief "A satin-metal product has a narrow highlight sweep and a thin clear coat reveal." --subject "a satin-metal hero product" --format markdown --language en
```

[Actual composed example — English](examples/results/coat_reveal.en.md) · [Korean](examples/results/coat_reveal.ko.md)

## Brief → production instructions

For example: "Reveal the surface of a satin-metal product with light, then show a thin coating reflection."

The tool selects directional highlight motion, restrained roughness, and a top-layer coat reflection. It distinguishes a coating layer from whole-object transmission and retains explicit preservation and delivery conditions in the detailed prompt. Selection scores are heuristic ranks, not generation success rates.

JSON results contain concise and detailed prompts in Korean and English, selected and excluded candidates with scoring reasons, a temporal plan, negative clauses, reference strategies, sources, and uncertainty. Markdown output provides a readable production plan.

## Knowledge and examples

The public pack contains **23 knowledge cards**: four Motion and 19 Redshift cards. Six workflows are provided in both languages: coat reveal, subsurface backlight, micro surface detail, rack focus, fog/light shafts, and relative timing. The **12 examples are composition dry runs**, not successful generated videos.

The full original knowledge store is not included. This edition bundles cards and settings for these six workflows. C4D, Redshift, and a private database are not required to run the tool.

## Validation and limits

- Twenty behavioral tests, 12/12 example dry runs, matching selection in six language pairs, and execution from a separate directory have been checked. [Validation record](docs/VALIDATION.json)
- Actual generation and render tests: zero. Quality, exact timing, and reference adherence need separate comparisons using the same model and inputs.
- English prompts combine registered knowledge clauses. This is not a general translator for arbitrary Korean text. Unmapped Korean subjects use a neutral English phrase and an uncertainty notice.
- Example image filenames are role placeholders. No images are supplied, read, or uploaded by the tool.
- Requested delivery settings are instructions, not evidence that a generation tool supports them. Five-phase temporal proportions are editorial suggestions.

[Usage](docs/USAGE.en.md) · [Architecture and selection rules](docs/ARCHITECTURE.en.md) · [Sources](SOURCES.en.md) · [Contributing](CONTRIBUTING.en.md) · [Release report](docs/RELEASE_REPORT.en.md)

## Reuse

The reviewed public code, configuration, cards, documentation, and examples are offered under the [MIT License](LICENSE). External Maxon documents, trademarks, and software are excluded. This project is not affiliated with or endorsed by Maxon. Creator: [bloglluukk-glitch](https://github.com/bloglluukk-glitch). Codex assisted with the public adaptation and translations.

[Changelog](CHANGELOG.en.md) · [Public file manifest](UPLOAD_MANIFEST.json)
