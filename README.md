# Pulse-0G

Health self-assessment for astronauts on long missions, with every claim traced to its source.

Built for the NASA Space Apps Challenge 2026, Córdoba — *Create Health Monitoring Software for Astronauts on Space Missions*.

## What it does

An astronaut taps a region of a body map and sees: the measurement, the band it falls in, the deviation from their own pre-flight baseline, a one-line action, and the evidence behind it. When a value leaves the band, the system exports a case package for the flight surgeon. Nothing is diagnosed, nothing is transmitted, and every number comes from a deterministic engine — never from a language model.

## Three things that make it different

- **Two-layer bands.** Population reference range plus deviation from the subject's own pre-flight baseline.
- **A visible claim verifier.** Any sentence that cannot be anchored to a data row or an evidence card is struck through on screen and logged.
- **Honest data handling.** Real OSDR data is ingested with its actual defects preserved — `N/A` versus `NA` versus empty cells, a timepoint that contradicts the study narrative, unidentified columns — and never silently repaired.

## Non-goals

No diagnosis, no treatment prescriptions, no physiological simulation, no clinical validation. The real dataset covers four subjects at seven discrete timepoints; it cannot support generalization claims and the product never makes them.

## Layout

```
odd/tasks/crewcheck.md   specification and task log
evidence/cards/          curated evidence cards, one JSON per card
evidence/README.md       how to build a card (quote first, model second)
data/raw/                downloaded source files, never edited
docs/                    presentation material
```

## Status

Specification under review. Stack decision pending — see `D1` in the task document.

## Sources

NASA OSDR `OSD-575` (Inspiration4 blood serum metabolic panel, CC0) and `OSD-656` (Inspiration4 urine inflammation panel, CC0). PhysioNet datasets, if used, are terrestrial software-testing fixtures and never presented as NASA data.
