-- Pulse-0G schema. One database, seeded at build time, committed to the repo.
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS dataset (
  id            TEXT PRIMARY KEY,
  title         TEXT NOT NULL,
  version       TEXT,
  license       TEXT NOT NULL,
  source_url    TEXT NOT NULL,
  sha256        TEXT,
  retrieved_at  TEXT
);

CREATE TABLE IF NOT EXISTS scenario (
  id            TEXT PRIMARY KEY,
  label         TEXT NOT NULL,
  generator     TEXT NOT NULL,
  generator_version TEXT NOT NULL,
  seed          INTEGER NOT NULL,
  manifest_json TEXT NOT NULL,
  created_at    TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS subject (
  id         TEXT PRIMARY KEY,
  dataset_id TEXT NOT NULL REFERENCES dataset(id),
  label      TEXT NOT NULL,
  note       TEXT
);

-- One row per (subject, variable, timepoint). A NULL value is a real absence,
-- never a zero, and always carries missing_token and a quality flag.
CREATE TABLE IF NOT EXISTS measurement (
  id           INTEGER PRIMARY KEY,
  dataset_id   TEXT NOT NULL REFERENCES dataset(id),
  subject_id   TEXT NOT NULL REFERENCES subject(id),
  scenario_id  TEXT REFERENCES scenario(id),
  variable     TEXT NOT NULL,
  value        REAL,
  unit         TEXT,
  ref_min      REAL,
  ref_max      REAL,
  ref_source   TEXT NOT NULL CHECK (ref_source IN ('dataset_file','demo_parameter','evidence_card','absent')),
  raw_value    TEXT,
  time_label   TEXT NOT NULL,
  -- Absolute timestamp, present only when the source defines an anchor.
  -- OSD-575 records L-92 / R+1 and never publishes a calendar date, so the
  -- column stays NULL there: inventing one would be a fabrication.
  recorded_at  TEXT,
  recorded_at_source TEXT NOT NULL
    CHECK (recorded_at_source IN ('scenario_anchor','absent')),
  phase        TEXT NOT NULL CHECK (phase IN ('preflight','inflight','postflight')),
  offset_days  REAL NOT NULL,
  sort_key     REAL NOT NULL,
  origin_type  TEXT NOT NULL CHECK (origin_type IN ('observed_real','replayed','injected_fault','synthetic')),
  hazard       TEXT,
  source_file  TEXT NOT NULL,
  source_row   INTEGER,
  source_column TEXT,
  missing_token TEXT CHECK (missing_token IN ('N/A','NA','EMPTY','NOT_RECORDED')
                          OR missing_token IS NULL),
  quality_flags TEXT NOT NULL DEFAULT '[]',
  -- A missing value must declare how it was missing, and a present value must not.
  CHECK ((value IS NULL AND missing_token IS NOT NULL)
      OR (value IS NOT NULL AND missing_token IS NULL))
);

CREATE INDEX IF NOT EXISTS idx_measurement_subject_variable
  ON measurement(subject_id, variable, sort_key);

-- Anything the importer refused, with the reason and the untouched original.
CREATE TABLE IF NOT EXISTS rejection (
  id            INTEGER PRIMARY KEY,
  dataset_id    TEXT NOT NULL,
  source_file   TEXT NOT NULL,
  source_row    INTEGER,
  source_column TEXT,
  raw_value     TEXT,
  reason        TEXT NOT NULL,
  created_at    TEXT NOT NULL
);

-- Per-column missing counts, so the integrity screen can show real numbers.
CREATE TABLE IF NOT EXISTS ingest_audit (
  id            INTEGER PRIMARY KEY,
  dataset_id    TEXT NOT NULL,
  source_file   TEXT NOT NULL,
  kind          TEXT NOT NULL CHECK (kind IN ('missing','unidentified_column','discrepancy')),
  column_name   TEXT,
  occurrences   INTEGER NOT NULL,
  note          TEXT
);

-- Append-only. No UPDATE or DELETE is ever issued against this table.
CREATE TABLE IF NOT EXISTS comment (
  id           INTEGER PRIMARY KEY,
  target_type  TEXT NOT NULL CHECK (target_type IN ('measurement','indicator','band_event','case_package')),
  target_id    TEXT NOT NULL,
  subject_id   TEXT NOT NULL,
  author_role  TEXT NOT NULL CHECK (author_role IN ('crew','surgeon')),
  body         TEXT NOT NULL,
  created_at   TEXT NOT NULL,
  mission_clock TEXT NOT NULL,
  revision_of  INTEGER REFERENCES comment(id),
  verified     INTEGER NOT NULL DEFAULT 0 CHECK (verified = 0)
);

CREATE TRIGGER IF NOT EXISTS comment_no_update
BEFORE UPDATE ON comment
BEGIN SELECT RAISE(ABORT, 'comment is append-only'); END;

CREATE TRIGGER IF NOT EXISTS comment_no_delete
BEFORE DELETE ON comment
BEGIN SELECT RAISE(ABORT, 'comment is append-only'); END;

CREATE VIEW IF NOT EXISTS v_missing_summary AS
SELECT dataset_id, source_file, variable, COUNT(*) AS rows_total,
       SUM(CASE WHEN value IS NULL THEN 1 ELSE 0 END) AS rows_missing
FROM measurement GROUP BY dataset_id, source_file, variable;
