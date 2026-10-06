# Usage

[Korean](USAGE.md) | **English**

## Start from an example

| Example | Main intention |
|---|---|
| [01 Coat reveal](../examples/en/01_coat_reveal.json) | Thin coat reflection over a satin surface and a directional highlight |
| [02 Subsurface backlight](../examples/en/02_sss_backlight.json) | Backlight diffuses through thin regions while solid shape remains |
| [03 Micro surface detail](../examples/en/03_micro_imperfection.json) | Sparse micro scratches stay attached to a rotating product |
| [04 Rack focus](../examples/en/04_rack_focus.json) | Fixed camera body, focus transfer from foreground to product |
| [05 Fog and shafts](../examples/en/05_fog_godrays.json) | Light shafts connected to a source, medium, and opening |
| [06 Relative timing](../examples/en/06_curve_timing.json) | Explicit acceleration, deceleration, overshoot, rebound, and settling |

## Make your request

Copy [request.json](../templates/request.json) and fill in `user_brief` and `subject.description`. The blank template is not a valid request; running it unchanged produces an input error.

- `visual_intent`: concrete material, lighting, focus, and atmosphere intentions.
- `motion_intent`: movement and explicit acceleration, deceleration, and settling conditions.
- `subject.*_must_remain`: preservation conditions explicitly set to true are included in the detailed prompt.
- `constraints.must_include` / `must_avoid`: lists of required and excluded strings. Their original text is retained in the result.
- `output`: specify duration, fps, aspect ratio, and resolution only when known. Use an aspect-ratio string such as `"16:9"`.
- `curve.curve_data`: only supplied relative timing is used. A profile ID alone is marked unresolved, not interpreted as an actual stored curve.

Supported input modes are text_only, start_only, start_end, start_middle_end, and reference_video. Modes other than text_only require the corresponding asset filenames, but the compiler never opens or transfers them. Attach your prepared assets separately when using a generation tool.

This edition supports video-shot briefs and the generic adapter only. Unregistered materials or styles require your judgment and real experiments. It does not fully translate arbitrary Korean sentences; provide your own English input when precise free-form English conditions are needed.

## Save the result

The following output path is relative to the current working directory. Results can contain the original request, so store them in the gitignored `outputs/` directory by default.

```sh
python prompt_composer.py --input examples/en/01_coat_reveal.json --format markdown --language en --output outputs/my-plan.en.md
```

Existing files are not overwritten; choose a new name. JSON contains prompt fields in both languages. `--language` selects the display language for Markdown only.

## Validate

```sh
python validate_prompt_composer.py
python prompt_composer.py --all-fixtures
```

The first command runs 20 behavioral checks. The second outputs all 12 composition examples and their evaluations as JSON, returning a failing exit status if the example checks fail. Passing composition checks is not validation of generation quality.
