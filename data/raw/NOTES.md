# OSD-575 — verified on retrieval, 2026-11-14

Everything below was measured by parsing the downloaded file. Nothing here is quoted from a secondary source.

## Access

| Item | Value |
|---|---|
| Study | `OSD-575` — SpaceX Inspiration4 Blood Serum Metabolic Panel and Immune/Cardiac Cytokine Arrays |
| Discovery endpoint | `GET https://osdr.nasa.gov/osdr/data/osd/files/575` → `OSD-575_files.json` |
| Files listed | 9, every one `restricted=false` |
| Download | `GET https://osdr.nasa.gov/geode-py/ws/studies/OSD-575/download?source=datamanager&file=<name>` |
| Licence | CC0-1.0 |

## Downloaded files

```
5eb1e7f0…09d9  8 506 b   LSDS-8_Comprehensive_Metabolic_Panel_CMP_TRANSFORMED.csv
dab247eb…a0c  25 275 b   LSDS-8_Comprehensive_Metabolic_Panel_CMP.upload_SUBMITTED.csv
4c2430cf…9c00  4 144 b   OSD-575_files.json   (file inventory, kept as provenance)
```

## Shape confirmed

- 29 lines total = 1 header + **28 data rows**; **58 columns**.
- One sample identifier per row, shape `C001_serum_L-3`: subject, matrix, timepoint.
- Subjects `C001`–`C004`. Matrix is `serum` only.
- Seven timepoints, all present: `L-92, L-44, L-3, R+1, R+45, R+82, R+194`. 4 rows × 7 = 28.
- 21 analytes, each with `value` + `range_min` + `range_max` columns.

## Defects found, with counts

| Defect | Count |
|---|---|
| `N/A` literal | 56 |
| `NA` literal | 22 |
| Empty cell | 3 |
| Columns carrying at least one missing value | 6 of 58 |
| `egfr_*_range_max` missing in **every** row | 28 of 28 each (2 columns) |
| `bun_to_creatinine_ratio_value` missing | 22 of 28 |

Consequences for the importer: three distinct missing tokens must be normalised to one `null`, and a reference range can itself be missing — so a band cannot assume `range_min`/`range_max` exist. `R+194` is present in the file even though it is the timepoint most likely to be described inconsistently elsewhere; it stays, flagged, never deleted.

## Reference ranges live in the file

Each row carries its own `range_min` and `range_max` for every analyte, and they are constant across subjects and timepoints. Example, `C001`:

| Analyte | Range | L-92 | L-44 | L-3 | R+1 | R+45 | R+82 | R+194 |
|---|---|---|---|---|---|---|---|---|
| glucose (mg/dL) | 65–99 | 83 | 80 | 69 | 90 | 84 | 91 | 87 |
| sodium (mmol/L) | 135–146 | 141 | 139 | 142 | 138 | 138 | 140 | 137 |
| potassium (mmol/L) | 3.5–5.3 | 4.6 | 4.2 | 3.9 | 4.4 | 4.0 | 4.3 | 4.3 |
| creatinine (mg/dL) | 0.52–1.04 | 1.24 | 1.10 | 1.37 | 1.12 | 1.11 | 1.25 | 1.29 |
| albumin (g/dL) | 3.6–5.1 | 5.0 | 5.0 | 4.9 | 4.9 | 4.9 | 5.1 | 4.6 |

This is the most useful finding for the band engine: **layer 1 of the band comes from the data file itself**, cited as `source_file` + column name, and needs no external threshold table. Layer 2, the deviation from the subject's own pre-flight baseline, is computed from `L-*` rows. No invented numbers are required for either layer.

## What this dataset cannot support

Four subjects, seven discrete samples, no continuous signal, no heart rate, no sleep, no mood, no blood pressure. It cannot support trend claims between samples, population statistics, or any statement about an individual astronaut's health. It is the fidelity and evidence tab, not the hero screen.

## Reproducing this check

```bash
cd data/raw
sha256sum -c <<'EOF'
5eb1e7f025dd8443a9e70111e62bc32afae3432753024489c5c013e401d709d9  LSDS-8_Comprehensive_Metabolic_Panel_CMP_TRANSFORMED.csv
dab247eb794edab59aaaa683c85fd1f2dbf4ae3684872739338e10ead4192a0c  LSDS-8_Comprehensive_Metabolic_Panel_CMP.upload_SUBMITTED.csv
EOF
```
