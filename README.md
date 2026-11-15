# Pulse-0G

Health self-assessment for astronauts on long missions, with every claim traced to its source.

Built for the NASA Space Apps Challenge 2026, Córdoba — *Create Health Monitoring Software for Astronauts on Space Missions*.

## What it does

An astronaut taps a region of a body map and sees the measurement, the band it falls in, the deviation from their own pre-flight baseline, a one-line action, and the evidence behind it. When a value leaves the band, the system assembles a case package for the flight surgeon. Nothing is diagnosed, nothing is transmitted, and every number comes from a deterministic engine — never from a language model.

Three tabs: **Misión** (the synthetic scenario, replayable day by day), **Biblioteca** (the two published NASA studies and the 24 curated evidence cards, searchable), **Consultar** (eight fixed query intents over the data, with a visible claim verifier).

## Three things that make it different

- **Two-layer bands.** A reference range plus the deviation from the subject's own pre-flight baseline. A value can be normal for anyone and still be a signal for that person.
- **A visible claim verifier.** Every sentence must cite a data row or an evidence card, and every printed number is re-checked against the cited values. A sentence that cannot be backed is struck through on screen with the reason. The verifier's own probe cases are visible in the app, because a verifier that never rejects anything is decoration.
- **Honest data handling.** Real OSDR data is ingested with its defects preserved: `N/A` versus `NA` versus empty cells, a timepoint that contradicts the study narrative, two headerless columns, a dataset that lacks a timepoint its sibling has. Nothing is silently repaired, and a missing value is never a zero.

## What backs the numbers

24 evidence cards, each with the source's literal quote in English, a Spanish summary, a link, and a verifier. Every quote was checked word by word against its live page. Two thresholds are cited from NASA documents:

| Indicator | Threshold | Source |
| --- | --- | --- |
| Sleep | restriction = <6 h per 24 h | HRP risk page, i=100 |
| Radiation | 620 mSv career limit at 3 % REID | HRP Evidence Book, Table 4-1 |

Blood pressure, resting heart rate and mood stay marked **provisional**: HRP publishes no numeric threshold for them, and NASA states its behavioural-health thresholds still have to be normed to the astronaut population. That absence is recorded in a card rather than filled with an invented number.

## Documentation

Bilingual. The product interface is in Spanish; the documentation is in both languages.

- [English: complete project description](docs/en/PROJECT.md) · [plain language](docs/en/PLAIN-LANGUAGE.md) · [architecture and growth](docs/en/ARCHITECTURE.md)
- [Español: descripción completa](docs/PROJECT.md) · [resumen simple](docs/RESUMEN-SIMPLE.md) · [arquitectura y crecimiento](docs/ARQUITECTURA-Y-CRECIMIENTO.md)
- [Index of all documents](docs/README.md) · [Sources and resources](docs/RESOURCES.md)

## Non-goals

No diagnosis, no treatment prescriptions, no physiological simulation, no clinical validation. The real datasets cover four subjects at six and seven discrete timepoints; they cannot support generalization and the product never claims it.

## Run it

```bash
npm install
npm run db      # rebuild the seeded database from data/raw (optional; a build is committed)
npm run dev     # http://localhost:3000
npm run check   # contract suites: intents, verifier, journal, case package (server must be up)
npm run check:cards   # evidence card gate (offline)
```

No network at runtime, no CDN, no remote fonts. The database is built at build time and opened read-only by the app; comments live in a separate append-only journal.

## Layout

```
app/                     Next.js routes and the global stylesheet
components/              dashboard, body map, sparkline, ask panel, comments, case package
lib/                     band engine, card loader, assemble, answer, verify, journal, case
evidence/cards/          one JSON per evidence card; evidence/README.md is the authoring protocol
evidence/SOURCES.md      which NASA documents to read and what to search for in each
tools/                   build_db.py, check_answers.py, check_case.py, check_cards.py, import_cards.py
design/                  design system sync and four artboards; artboard 04 is implemented
docs/                    video briefs, deck and demo material
odd/tasks/crewcheck.md   specification, tasks and decision log
data/raw/                downloaded source files, never edited
```

## Sources

NASA OSDR `OSD-575` (Inspiration4 blood serum metabolic panel, CC0, 4 subjects × 7 timepoints × 19 analytes) and `OSD-656` (Inspiration4 urine inflammation panel, CC0, 4 subjects × 6 timepoints × 404 variables). HRP risk pages and the HRP Evidence Book for the evidence cards. PhysioNet datasets, if used, are terrestrial software-testing fixtures and never presented as NASA data.
