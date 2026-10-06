-- Prompt Composer — ephemeral execution trace
-- Dialect: SQLite 3.37+
-- This schema is loaded into :memory:. No persistent database is created.

PRAGMA foreign_keys = ON;

CREATE TABLE composer_run (
    run_id          TEXT PRIMARY KEY,
    input_mode      TEXT NOT NULL,
    model_target    TEXT NOT NULL,
    created_on      TEXT NOT NULL CHECK (created_on LIKE '____-__-__')
);

CREATE TABLE candidate_evaluation (
    run_id          TEXT NOT NULL REFERENCES composer_run(run_id) ON DELETE CASCADE,
    source_track    TEXT NOT NULL CHECK (source_track IN ('motion','redshift')),
    source_id       TEXT NOT NULL,
    score           INTEGER NOT NULL,
    factors_json    TEXT NOT NULL,
    matched_on_json TEXT NOT NULL,
    penalties_json  TEXT NOT NULL,
    selected        INTEGER NOT NULL DEFAULT 0 CHECK (selected IN (0,1)),
    selection_role  TEXT,
    PRIMARY KEY (run_id, source_track, source_id)
);

CREATE TABLE provenance_record (
    run_id           TEXT NOT NULL REFERENCES composer_run(run_id) ON DELETE CASCADE,
    source_id        TEXT NOT NULL,
    fragment_role    TEXT NOT NULL,
    lifecycle_status TEXT NOT NULL,
    derived_only     INTEGER NOT NULL CHECK (derived_only IN (0,1)),
    PRIMARY KEY (run_id, source_id, fragment_role)
);

CREATE INDEX idx_candidate_score
    ON candidate_evaluation(run_id, score DESC);
