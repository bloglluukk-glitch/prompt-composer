# Architecture and selection rules

[Korean](ARCHITECTURE.md) | **English**

Request JSON → structured intent → Motion/Redshift card scoring → role selection and derived dependency closure → contextual prompt composition → review criteria, sources, and uncertainty.

`data/knowledge.json` contains 23 public cards. `composer_config.json` contains Korean/English expressions, ranking weights, conflict/dependency rules, and contextual clauses. [Source notes](../SOURCES.en.md) distinguish technical background from the creator's prompt judgments.

## Selection

Scores use direct intent phrases, visual vocabulary, explicit preferences, and relations. Generic words such as product, video, or surface cannot select a large collection by themselves. No empirically validated model-specific suitability scores are supplied.

Default caps are three Motion, two Material, two Lighting, one Camera, and one each for Atmosphere and Lens, with eight cards total. Atmosphere can exceed its default cap to retain derived components and an explicit Fog/Volume/Shafts combination. Scores are production-rule ranks, not success rates or physical simulation values.

Rim, Micro Imperfection, and God Rays are labeled as derived combinations rather than independent official features. Required light, surface, or medium cards remain selected. Easily confused roles such as SSS versus Transmission, Bump versus Displacement, and DOF versus Bloom are distinguished.

## Output and timing

Concise English is a 60–100-word summary. Detailed English includes explicit delivery and preservation settings plus selected instructions; the supplied examples use 120–180 words. Longer user conditions can produce a longer detailed prompt. Original condition lists are retained separately for review before using a generation service.

Five-phase timing proportions are an editorial review plan. Exact frames and tangents are not inferred. Curve translation does not add overshoot or rebound values absent from the supplied curve.

## Runtime boundaries

No external network, model calls, asset file reads, or persistent databases are used. `composer_schema.sql` supports an in-memory SQLite trace only. The original knowledge SQL is not loaded. Source hashes are compared before and after composition; results do not include personal installation paths.

The CLI writes only a result explicitly requested with `--output` and refuses to overwrite an existing result. The validator creates and removes its own temporary test directories; it does not delete a user's databases or media.
