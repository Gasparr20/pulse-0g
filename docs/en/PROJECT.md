# Pulse-0G — complete project description

Reference document for presentations, judges, and anyone who needs to understand what this project is without reading the code.

> Spanish version: [`docs/PROJECT.md`](../PROJECT.md)

---

## 1. In one sentence

A health self-assessment dashboard for astronauts on long missions that shows, for every indicator, **the measured value, the band it falls in, the deviation from that crew member's own pre-flight baseline, the one action to take, and the source behind every sentence**.

## 2. The problem

On a Mars mission there is no doctor beside the astronaut, and communication with Earth arrives with up to 22 minutes of delay. They need to answer three questions alone:

1. Is this value normal **for me**?
2. Do I have to do something now?
3. Do I have to tell Earth?

NASA's Human Research Program mapped five hazards of spaceflight — radiation, isolation and confinement, distance from Earth, altered gravity, and a hostile closed environment — which produce bone loss, cardiovascular deconditioning, immune changes, and sleep and mood disruption. The indicators the challenge itself proposes are blood pressure, heart rate, blood glucose, temperature, sleep hours and mood.

A dashboard that displays those numbers solves nothing. **The decision is the product, not the figure.**

## 3. What the software does

Three tabs, each with a different job.

### Mission

The crew member's state at a given moment of the mission, replayable day by day through a **mission clock** (launch, month 1, month 3, month 4, month 6, return +29 days).

- **Human figure** with five tappable regions: head (sleep and mood), thorax (pressure, heart rate and temperature), arms (measurement site), legs and eyes (no instrument on board).
- **Indicator table** with value, own baseline, percentage deviation and band.
- **Alarm block**: when a value leaves its band, the action appears in a red block with the value and baseline that fired it.
- **Data quality**: four figures about what the importer found in the original files and what it did with it.
- **Case package**: a file with the measurements, the rules applied and the journal, for the flight surgeon on Earth.

### Library

Everything the system may show as a source, in one place and searchable.

- **OSD-575** — Inspiration4 blood metabolic panel: 4 crew members, 7 samples per analyte, 19 analytes, with the reference ranges the file itself publishes.
- **OSD-656** — urine inflammation panel from the same flight: 4 crew members, 6 timepoints, 404 variables. Described, not charted: its values are normalised NPQ, not clinical concentrations.
- **Evidence library** — 25 curated documents, each with its literal quote in English, a Spanish summary, the link to the document, and who verified it.

### Ask

Eight fixed queries over the data, plus an explicit abstention.

`series` · `alerts` · `baseline` · `missing` · `why` · `radiation` · `provenance` · `clinical_request`

Every answer is built from sentences that **cite the data row they came from**. An independent verifier re-reads the rendered text and compares every printed number against the cited values. If a sentence cannot be anchored, or prints a figure that is not in the data, **it is struck through in red on screen with the reason**.

The query **"am I dehydrated?"** returns an explicit refusal: the system does not diagnose. The query **"what is the capital of France?"** also does: it is not in the corpus.

There is also an optional **local AI** switch. Off by default. When on, a model running on the machine explains the already-computed answer in plain language. It never produces a number, and the system checks every figure in its text against the data before showing it.

## 4. The three things that make it different

### 4.1 Two-layer bands

A value is compared against two different things:

1. **The reference range** — population, or whatever the data file publishes.
2. **The crew member's own baseline** — the median of their pre-flight records.

A value can sit inside the population range and still be a signal for that person. And the reverse: in flight, some indicators **change what normal means**. Core body temperature at rest rises about **1.01 °C** on the ISS compared with the pre-flight measurement. With that shift, almost every crew member would read as febrile against a population threshold of 37.5 °C every day. So the system uses the 38.0 °C ceiling only as an absolute reference, and lets the deviation from the person's own baseline do the real work.

### 4.2 A visible claim verifier

This is not a chat. It is the opposite: **every sentence has to be traceable**.

- Every statement cites an anchor: a data row, an aggregate, or an evidence card.
- The verifier extracts the numbers from the text and compares them against the anchor's values, allowing for display rounding and treating identifiers (`OSD-575`, `R+29`) as identifiers rather than figures.
- What does not verify is struck.

When it was built, **it struck seven sentences written by the system's own author**: counts with no anchor, a `9` that was `8.96`, an `11 %` that was `-11.13`. That is the argument: the system does not trust even its own code.

The verifier almost never rejects anything in normal use — the templates are written to anchor — which would make the most interesting behaviour invisible. So the Ask tab includes its **self-test**: six control sentences, three it must accept and three it must reject, with the result on screen.

### 4.3 Honest data handling

Real NASA files are ingested **with their defects preserved**:

| Defect found | What the system does |
|---|---|
| `N/A`, `NA` and empty cells coexisting in one file | All three are stored as absence; converting them to zero would falsify any average |
| One analyte with no reference range in one sample | The value is shown and declared "sin rango en el archivo" |
| One sample 194 days after return that the study narrative never mentions | It is kept and the discrepancy is flagged |
| Two columns with no header in the second study | Refused and logged; the system does not guess what they contain |
| One study without `R+194` that the other has, for the same four crew members | The difference is recorded; it is not harmonised away |

Nothing is repaired in silence, and **a missing value is never a zero**.

## 5. What backs the numbers

25 evidence cards. **Every quote was verified word by word against its live document.** If the link does not lead to the exact passage, the card does not go in.

| Indicator | Threshold | Source |
|---|---|---|
| Sleep | restriction = under 6 h per 24 h | HRP risk page, i=100 |
| Radiation | 620 mSv career limit at 3 % REID | HRP Evidence Book, Table 4-1 |
| Temperature | 38.0 °C ceiling; +1.01 °C in flight | Stahn et al., *Scientific Reports* 2017 |

Blood pressure, resting heart rate and mood stay marked **provisional**: HRP publishes no numeric threshold for them, and NASA states that its behavioural-health thresholds still have to be normed to the astronaut population. **That absence is recorded in a card instead of being filled with an invented number.**

## 6. What it does NOT do

- It does not diagnose, predict disease, or prescribe.
- It does not simulate physiology.
- It does not transmit anything: the case package is generated and downloaded, never sent.
- It does not **depend** on artificial intelligence: the optional local model rewrites an answer that was already computed, it is off by default, and if the model is missing or wrong the system answers exactly the same.
- It does not generalise: the real studies have four crew members and six to seven discrete samples.

## 7. How it is built

| Layer | Technology | Decision |
|---|---|---|
| Interface | Next.js 16, React 19, TypeScript | One process, no CDN, no remote fonts |
| Data | SQLite (`node:sqlite`) | Database opened **read-only** at runtime, seeded at build time |
| Ingest | Python standard library | One adapter per study, one shared schema |
| Journal | Separate SQLite file | Append-only: triggers reject `UPDATE` and `DELETE` |
| Evidence | JSON, one file per card | Read on every request: dropping a file changes the screen |

**It runs without a network.** There is not a single remote URL in the application code.

## 8. Verification

Three automated suites, all green:

| Suite | What it proves |
|---|---|
| `check_answers.py` | The nine intents answer; no sentence is struck by mistake; the verifier **does** reject the six control sentences; the demo moment (FD180) as well |
| `check_case.py` | The journal accepts no edit or delete; the case package carries the thread; invalid input is rejected |
| `check_cards.py` | 25 cards, 0 errors: structure, quote-first, and agreement between a card's threshold and the value the system uses |

## 9. Why these decisions

**Why no generative AI in the critical path.** The project's requirement is real information, not invented information. A free-text generator is the largest possible source of invention: fluency is gained, verifiability is lost, and here verifiability **is** the product. The local model exists as an optional narrator, never as a source of figures.

**Why the evidence database is immutable.** Nothing at runtime can alter what a mission recorded. Operational comments live in a separate append-only file, because they are context and not evidence.

**Why gaps are shown.** A chart with a gap tells the truth; an interpolated one lies elegantly.

**Why provisional cards stay visible.** If a threshold has no source, the system says so on screen. Hiding the debt is worse than showing it.

## 10. Current state

| | |
|---|---|
| Data | 10,995 measurements: 532 from OSD-575, 8,888 from OSD-656, 1,575 from the synthetic scenario |
| Cards | 25 · every quote verified literally |
| Cited thresholds | 3 of 6 indicators (sleep, radiation, temperature) |
| Queries | 8 intents plus abstention, with a verifier self-test |
| Interface | Three tabs, five body regions, mission clock, animations honouring reduced motion |
| Design | Synced design system and four artboards; the fourth is implemented |

## 11. Minimal glossary

- **Band**: the classification of a value as in range / attention / action / no data.
- **Own baseline**: the median of the crew member's measurements before launch.
- **Anchor**: the data row or card that backs one sentence of an answer.
- **Evidence card**: curated document with a literal quote, a summary and a verifiable link.
- **Provisional**: a band whose threshold has no cited source yet.
- **Case package**: file with the measurements, the rules and the journal, for the flight surgeon.
- **REID**: risk of exposure-induced death, the measure NASA uses to set its radiation limits.
- **NPQ**: normalised protein quantification; useful for comparing a protein with itself, not as a clinical concentration.
