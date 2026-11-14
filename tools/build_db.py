#!/usr/bin/env python3
"""Build the seeded CrewCheck database from raw sources.

Two adapters, one schema:
  * OSD-575  — real NASA OSDR data, defects preserved verbatim.
  * synthetic — a labelled demonstration scenario with a reproducible manifest.

Run:  python3 tools/build_db.py
Out:  db/crewcheck.sqlite  (+ data/raw/SYNTHETIC-MANIFEST.json)

This is a build-time tool. The application only reads the resulting database.
"""
from __future__ import annotations

import csv
import hashlib
import json
import random
import sqlite3
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw"
DB = ROOT / "db" / "crewcheck.sqlite"
SCHEMA = ROOT / "db" / "schema.sql"

CMP_FILE = "LSDS-8_Comprehensive_Metabolic_Panel_CMP_TRANSFORMED.csv"
OSD575_URL = "https://osdr.nasa.gov/osdr/data/osd/files/575"
RETRIEVED_AT = "2026-11-14"

# Units as they appear in the OSD-575 header (including the file's own typo
# "millimol") mapped to one canonical display unit.
UNIT_MAP = {
    "gram_per_deciliter": "g/dL",
    "milligram_per_deciliter": "mg/dL",
    "units_per_liter": "U/L",
    "millimole_per_liter": "mmol/L",
    "millimol_per_liter": "mmol/L",
    "milliliter_per_minute_per_1.73_meter_squared": "mL/min/1.73m2",
    "milliliter_per_minute": "mL/min",
}

MISSING_TOKENS = {"": "EMPTY", "n/a": "N/A", "na": "NA", "nan": None,
                  "null": None, "-": None}

# Which hazard each analyte belongs to, for the hazard dimension.
ANALYTE_HAZARD = {
    "glucose": "hazard:environment", "sodium": "hazard:environment",
    "potassium": "hazard:environment", "chloride": "hazard:environment",
    "carbon_dioxide": "hazard:environment", "calcium": "hazard:gravity",
    "creatinine": "hazard:gravity", "urea_nitrogen_bun": "hazard:gravity",
    "egfr_african_american": "hazard:gravity",
    "egfr_non_african_american": "hazard:gravity",
    "bun_to_creatinine_ratio": "hazard:gravity",
    "albumin": "hazard:radiation", "globulin": "hazard:radiation",
    "total_protein": "hazard:radiation",
    "albumin_to_globulin_ratio": "hazard:radiation",
    "alkaline_phosphatase": "hazard:gravity", "alt": "hazard:radiation",
    "ast": "hazard:radiation", "total_bilirubin": "hazard:radiation",
}


class Build:
    def __init__(self) -> None:
        # Always build from scratch: a partial rebuild is not a valid state.
        DB.unlink(missing_ok=True)
        self.con = sqlite3.connect(DB)
        self.con.executescript(SCHEMA.read_text())
        self.now = datetime.now(timezone.utc).isoformat(timespec="seconds")
        self.rejections: list[tuple] = []
        self.audit: list[tuple] = []

    # ---------------------------------------------------------------- helpers
    def reject(self, dataset, source_file, row, column, raw, reason) -> None:
        self.rejections.append(
            (dataset, source_file, row, column, raw, reason, self.now))

    def parse_header(self, header: str):
        """Split 'glucose_value_milligram_per_deciliter' into its three parts.

        Returns (analyte, kind, unit) or None when the column cannot be
        identified with certainty — an unidentified column is never guessed.
        """
        body, unit = header, None
        for suffix, canonical in sorted(UNIT_MAP.items(), key=lambda kv: -len(kv[0])):
            if body.endswith("_" + suffix):
                body, unit = body[: -(len(suffix) + 1)], canonical
                break
        for suffix, kind in (("_range_min", "ref_min"), ("_range_max", "ref_max"),
                             ("_value", "value"), ("_min", "ref_min"),
                             ("_max", "ref_max")):
            if body.endswith(suffix):
                return body[: -len(suffix)], kind, unit
        return None

    @staticmethod
    def parse_value(raw: str):
        """Return (value, missing_token, quality_flag)."""
        token = raw.strip()
        key = token.lower()
        if key in MISSING_TOKENS:
            return None, MISSING_TOKENS[key], "missing:declared"
        try:
            return float(token), None, None
        except ValueError:
            return None, None, "malformed:numeric"

    @staticmethod
    def sort_key(phase: str, offset_days: float) -> float:
        # Preflight counts down to launch, inflight counts up from it, and
        # postflight is offset so the three phases can never interleave.
        return {"preflight": offset_days, "inflight": offset_days,
                "postflight": 1_000_000 + offset_days}[phase]

    # ------------------------------------------------------------- OSD-575
    def import_osd575(self) -> None:
        ds_id = "OSD-575"
        sha = hashlib.sha256((RAW / CMP_FILE).read_bytes()).hexdigest()
        self.con.execute(
            "INSERT INTO dataset VALUES (?,?,?,?,?,?,?)",
            (ds_id,
             "SpaceX Inspiration4 Blood Serum Metabolic Panel and Immune/Cardiac Cytokine Arrays",
             "TRANSFORMED", "CC0-1.0", OSD575_URL, sha, RETRIEVED_AT))

        with (RAW / CMP_FILE).open(newline="", encoding="utf-8-sig") as fh:
            reader = csv.reader(fh)
            header = next(reader)
            rows = list(reader)

        columns: dict[str, list[tuple[int, str, str | None]]] = defaultdict(list)
        unidentified = []
        for idx, name in enumerate(header[1:], start=1):
            parsed = self.parse_header(name)
            if parsed is None or not parsed[0]:
                unidentified.append((idx + 1, name))
                continue
            analyte, kind, unit = parsed
            columns[analyte].append((idx, kind, unit))

        for col_no, name in unidentified:
            self.reject(ds_id, CMP_FILE, 1, name, None, "unidentified_column")
            self.audit.append((ds_id, CMP_FILE, "unidentified_column", name, 1,
                               f"header position {col_no} could not be parsed"))

        subjects: set[str] = set()
        missing_per_column: Counter = Counter()
        inserted = 0

        for row_no, row in enumerate(rows, start=2):
            sample = row[0].strip()
            parts = sample.split("_")
            if len(parts) != 3:
                self.reject(ds_id, CMP_FILE, row_no, "Sample Name", sample,
                            "unparsable_sample_id")
                continue
            subject_raw, matrix, time_label = parts
            if matrix != "serum":
                self.reject(ds_id, CMP_FILE, row_no, "Sample Name", sample,
                            "unsupported_matrix")
                continue
            phase = "preflight" if time_label.startswith("L-") else "postflight"
            offset = float(time_label.split("-", 1)[1]) if phase == "preflight" \
                else float(time_label.split("+", 1)[1])
            if phase == "preflight":
                offset = -offset
            subject_id = f"{ds_id}:{subject_raw}"
            if subject_raw not in subjects:
                subjects.add(subject_raw)
                self.con.execute(
                    "INSERT INTO subject VALUES (?,?,?,?)",
                    (subject_id, ds_id, subject_raw,
                     "Inspiration4 crew member; identifier scoped to this dataset only"))

            for analyte, cols in columns.items():
                found = {kind: (idx, unit) for idx, kind, unit in cols}
                value_idx, unit = found.get("value", (None, None))
                if value_idx is None:
                    continue
                raw = row[value_idx] if value_idx < len(row) else ""
                value, token, flag = self.parse_value(raw)
                if token is not None:
                    missing_per_column[analyte] += 1
                if flag == "malformed:numeric":
                    self.reject(ds_id, CMP_FILE, row_no, header[value_idx], raw,
                                "malformed_numeric")
                    continue
                ref_min = ref_max = None
                if "ref_min" in found and found["ref_min"][0] < len(row):
                    ref_min = self.parse_value(row[found["ref_min"][0]])[0]
                if "ref_max" in found and found["ref_max"][0] < len(row):
                    ref_max = self.parse_value(row[found["ref_max"][0]])[0]
                ref_source = "dataset_file" if ref_min is not None or ref_max is not None \
                    else "absent"
                flags = [f for f in (flag,) if f]
                if unit is None:
                    flags.append("unit:absent")
                if ref_min is None and ref_max is None:
                    flags.append("ref_range:missing")
                self.con.execute(
                    """INSERT INTO measurement
                       (dataset_id, subject_id, scenario_id, variable, value, unit,
                        ref_min, ref_max, ref_source, raw_value, time_label, phase,
                        offset_days, sort_key, origin_type, hazard, source_file,
                        source_row, source_column, missing_token, quality_flags)
                       VALUES (?,?,NULL,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                    (ds_id, subject_id, analyte, value, unit, ref_min, ref_max,
                     ref_source, raw, time_label, phase, offset,
                     self.sort_key(phase, offset), "observed_real",
                     ANALYTE_HAZARD.get(analyte), CMP_FILE, row_no,
                     header[value_idx], token, json.dumps(flags)))
                inserted += 1

        for analyte, count in missing_per_column.items():
            self.audit.append((ds_id, CMP_FILE, "missing", analyte, count,
                               "declared missing token, stored as NULL"))
        self.audit.append((ds_id, CMP_FILE, "discrepancy", "time_label", 4,
                           "R+194 present in the data file; kept, never deleted"))
        print(f"OSD-575: {len(rows)} rows read, {inserted} measurements, "
              f"{len(subjects)} subjects, {len(unidentified)} unidentified columns")

    # ------------------------------------------------------------ synthetic
    def build_synthetic(self) -> None:
        scenario_id, subject_id, ds_id = "SCN-MARS-180", "SYNTH:ASTRO-01", "SYNTHETIC-DEMO"
        seed, generator, gen_version = 20261114, "tools/build_db.py", "1.0.0"
        rng = random.Random(seed)

        self.con.execute(
            "INSERT INTO dataset VALUES (?,?,?,?,?,?,?)",
            (ds_id, "CrewCheck demonstration scenario", gen_version,
             "generated", "local", None, self.now))
        self.con.execute(
            "INSERT INTO subject VALUES (?,?,?,?)",
            (subject_id, ds_id, "ASTRO-01",
             "Fictional crew member. Not a real person and not derived from OSDR participants."))

        # (variable, unit, baseline, daily drift, noise sd, hazard, demo range)
        spec = [
            ("systolic", "mmHg", 112, 0.060, 4.0, "hazard:gravity", 95, 130),
            ("diastolic", "mmHg", 70, 0.040, 3.0, "hazard:gravity", 60, 85),
            ("resting_hr", "bpm", 58, 0.050, 3.0, "hazard:gravity", 45, 85),
            ("glucose", "mg/dL", 88, 0.000, 6.0, "hazard:environment", 65, 99),
            ("temperature", "degC", 36.6, 0.000, 0.15, "hazard:environment", 36.0, 37.5),
            ("sleep_hours", "h", 7.4, -0.012, 0.70, "hazard:isolation", 6.0, 9.0),
            ("mood", "score_0_10", 7.5, -0.011, 0.60, "hazard:isolation", 5.0, 10.0),
        ]
        events: list[dict] = []
        rows: list[tuple] = []
        radiation = 0.0

        def emit(variable, unit, value, label, phase, offset, hazard,
                 ref, flags, raw=None):
            rows.append((ds_id, subject_id, scenario_id, variable, value, unit,
                         ref[0], ref[1], "demo_parameter",
                         raw if raw is not None else ("" if value is None else f"{value:.2f}"),
                         label, phase, offset, self.sort_key(phase, offset),
                         "synthetic", hazard, "scenario:SCN-MARS-180", None,
                         None, "NOT_RECORDED" if value is None else None,
                         json.dumps(flags)))

        day = -90
        while day <= -1:                                  # preflight, weekly
            label = f"L-{abs(day)}"
            for var, unit, base, _, sd, hazard, lo, hi in spec:
                emit(var, unit, round(rng.gauss(base, sd), 2), label, "preflight",
                     day, hazard, (lo, hi), ["synthetic", "ref:demo_parameter"])
            day += 7

        for day in range(0, 181):                         # inflight, daily
            label = f"FD{day}"
            if day == 120:
                events.append({"day": day, "event": "artifact",
                               "detail": "single temperature reading injected at 38.4 C"})
            if day == 61:
                events.append({"day": day, "event": "gap",
                               "detail": "sleep_hours not recorded on FD61-FD64"})
            if day == 30:
                events.append({"day": day, "event": "duplicate",
                               "detail": "systolic emitted twice on FD30"})
            for var, unit, base, drift, sd, hazard, lo, hi in spec:
                flags = ["synthetic", "ref:demo_parameter"]
                if var == "sleep_hours" and 61 <= day <= 64:
                    emit(var, unit, None, label, "inflight", day, hazard, (lo, hi),
                         flags + ["missing:sensor_not_worn"])
                    continue
                if var == "sleep_hours" and day >= 90:
                    base = 6.1
                if var == "mood" and day >= 100:
                    base = 6.2
                value = round(rng.gauss(base + drift * day, sd), 2)
                if var == "temperature" and day == 120:
                    value, flags = 38.4, flags + ["artifact:suspected"]
                emit(var, unit, value, label, "inflight", day, hazard, (lo, hi), flags)
                if var == "systolic" and day == 30:
                    emit(var, unit, value, label, "inflight", day, hazard, (lo, hi),
                         flags + ["duplicate:suspected"])
            radiation = round(radiation + 0.42 + rng.gauss(0, 0.02), 3)
            emit("radiation_dose_cumulative", "mSv", radiation, label, "inflight",
                 day, "hazard:radiation", (0, 600),
                 ["synthetic", "ref:demo_parameter", "ref:career_limit"])

        for day in range(181, 211, 7):                    # postflight, weekly
            label = f"R+{day - 180}"
            for var, unit, base, _, sd, hazard, lo, hi in spec:
                emit(var, unit, round(rng.gauss(base, sd), 2), label, "postflight",
                     day, hazard, (lo, hi), ["synthetic", "ref:demo_parameter"])

        manifest = {
            "scenario_id": scenario_id, "seed": seed, "generator": generator,
            "generator_version": gen_version, "subject": subject_id,
            "fictional": True, "days": {"preflight": 90, "inflight": 180, "postflight": 30},
            "parameters": {v: {"baseline": b, "drift_per_day": d, "sd": s,
                               "demo_range": [lo, hi], "hazard": h}
                           for v, _, b, d, s, h, lo, hi in spec},
            "events": events,
            "warning": "Demo parameters, not clinical thresholds. Never present as NASA data.",
        }
        # The scenario row must exist before any measurement references it.
        self.con.execute(
            "INSERT INTO scenario VALUES (?,?,?,?,?,?,?)",
            (scenario_id, "Marte 180 dias — sintetico", generator, gen_version,
             seed, json.dumps(manifest, indent=2), self.now))
        (RAW / "SYNTHETIC-MANIFEST.json").write_text(json.dumps(manifest, indent=2))

        self.con.executemany(
            """INSERT INTO measurement
               (dataset_id, subject_id, scenario_id, variable, value, unit,
                ref_min, ref_max, ref_source, raw_value, time_label, phase,
                offset_days, sort_key, origin_type, hazard, source_file,
                source_row, source_column, missing_token, quality_flags)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""", rows)
        print(f"synthetic: {len(rows)} measurements, {len(events)} documented events")

    # ------------------------------------------------------------------ run
    def run(self) -> None:
        self.import_osd575()
        self.build_synthetic()
        self.con.executemany(
            "INSERT INTO rejection (dataset_id, source_file, source_row, source_column,"
            " raw_value, reason, created_at) VALUES (?,?,?,?,?,?,?)", self.rejections)
        self.con.executemany(
            "INSERT INTO ingest_audit (dataset_id, source_file, kind, column_name,"
            " occurrences, note) VALUES (?,?,?,?,?,?)", self.audit)
        self.con.commit()
        print(f"rejections: {len(self.rejections)} | audit rows: {len(self.audit)}")

        print("\n-- verification --")
        q = lambda sql: self.con.execute(sql).fetchall()
        print("measurements by origin:",
              dict(q("SELECT origin_type, COUNT(*) FROM measurement GROUP BY 1")))
        print("missing values      :", q("SELECT COUNT(*) FROM measurement WHERE value IS NULL")[0][0])
        print("timepoints OSD-575  :",
              [r[0] for r in q("SELECT DISTINCT time_label FROM measurement WHERE dataset_id='OSD-575'")])
        print("semantic order      :",
              [r[0] for r in q("SELECT DISTINCT time_label FROM measurement WHERE dataset_id='OSD-575' ORDER BY sort_key")])
        print("ref_source split    :",
              dict(q("SELECT ref_source, COUNT(*) FROM measurement GROUP BY 1")))
        self.con.close()


if __name__ == "__main__":
    Build().run()
