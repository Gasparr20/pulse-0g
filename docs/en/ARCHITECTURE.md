# Pulse-0G — how it works, how it would connect, and how far it can grow

Technical and explanatory document. It separates what **is built**, what is **designed and not implemented**, and what **would be needed** to take it to flight.

> Spanish version: [`docs/ARQUITECTURA-Y-CRECIMIENTO.md`](../ARQUITECTURA-Y-CRECIMIENTO.md)

---

## 1. What happens when the astronaut touches the screen

The full path of one datum, end to end.

### Step 1 · The measurement arrives

Today it arrives three ways, all archived:

- A **file published by NASA** (OSD-575, OSD-656), downloaded and stored unedited in `data/raw/`.
- A **synthetic scenario** generated from a fixed seed, with a manifest and explicit parameters.
- The **journal**, which is free text and is never treated as a measurement.

### Step 2 · The adapter normalises it

Each study has its own adapter, because each file has its own oddities. The adapter:

1. Reads subject, matrix and timepoint from the sample identifier (`C001_serum_L-3`).
2. Detects which missing token that file uses: `N/A`, `NA`, empty cell. **All three are stored as absence.**
3. Splits the reference into two columns, minimum and maximum. If the file does not carry one, it is `absent`.
4. Computes **semantic** time ordering (`L-92` before `L-3`, not alphabetical).
5. Refuses what it cannot identify: a column with no header is not guessed, it is logged in the rejection table.

### Step 3 · It is stored with provenance

Every row carries:

```
dataset · version · subject · variable · value · unit
reference minimum and maximum · where the range came from
labelled timepoint · phase · day offset · sort order
origin type (real / replayed / injected fault / synthetic)
hazard tag · source file · source row · source column
missing token · quality flags
```

That last block is what lets the system answer **"where does this datum come from"** without inventing anything.

### Step 4 · The band engine classifies

Three paths, and none of them guesses:

| Situation | What it does |
|---|---|
| The file carries a reference range | Classifies against it and cites the file |
| An evidence card exists for that limit | Classifies and cites the card |
| Neither a range nor a card | **Grey: "sin umbral citado"** (no cited threshold) |

Coverage is tracked **per boundary, not per variable**. Citing the 6-hour sleep line does not license the 5-hour one: if a value trips the 5-hour boundary, the indicator goes back to "provisional". That prevents the easiest mistake available, which is declaring a whole rule covered by citing one of its two edges.

### Step 5 · The interface shows the decision

Figure, table, band and action. The deviation from the person's own baseline is shown **even when the band is green**, because a person can be inside the range and still have moved.

### Step 6 · The verifier controls the answer

When the astronaut asks, the answer is not written by a model: it is assembled by a template engine that knows eight intents. Every sentence comes out with its anchor. Then an independent verifier:

1. Extracts the numbers from the already rendered text.
2. Compares them against the anchor's values, accepting rounding (`76.4` sanctions `76`).
3. Ignores identifiers, which contain digits but are not figures.
4. Strikes whatever does not match.

The optional local model, when switched on, runs **before** this step: it explains the anchored sentences, and the verifier checks its output against the same numbers. A figure that was not in the source discards the model's paragraph and leaves the engine's version standing.

### Step 7 · The decision is recorded

The journal stores notes with role, mission clock and wall clock. It is **append-only**: no editing, no deleting, and a correction is a new note pointing at the previous one. Database triggers reject `UPDATE` and `DELETE` even if someone tries them through raw SQL.

### Step 8 · If needed, it escalates

The case package gathers the measurements, the bands that fired, the rules, the data quality and the journal. It downloads as JSON and previews as a readable report. **Nothing is sent.** If that feature is never used, everything else works the same.

---

## 2. How sensors would connect

There are no sensors today: there are files and a scenario. The reasonable question is what would change if there were, and the short answer is **the ingestion layer, and nothing else**.

### 2.1 The contract already exists

The database schema is, in practice, the integration contract. A new sensor contributes rows with the same fields that already exist. Everything above — bands, verifier, journal, case package — is untouched.

```
Reader → Adapter → measurement → [band engine] → screen
```

The adapter is the only device-specific part. That is deliberate: adapters are cheap and disposable; the band engine and the verifier are the asset.

### 2.2 What a real adapter would have to solve

| Problem | Why it matters | How it is handled |
|---|---|---|
| **Signal quality** | A PPG with movement gives a false pulse | Quality flags per sample; a poor-quality value cannot fire a red band |
| **Sensor drift** | An uncalibrated thermometer lies systematically | Calibration declared per device and stored with the series |
| **Connection gaps** | A patch falls off and comes back | The gap is stored as a gap; never interpolated |
| **Clock** | Off Earth, device time and mission time differ | Both are stored: device time and mission time |
| **Units** | mg/dL and mmol/L coexist in the literature | Unit mandatory per sample; the engine converts, never guesses |
| **Provenance** | A manual value and a sensor value are not comparable | `origin_type` separates sensor, manual, replayed and synthetic |

### 2.3 The systems that exist and what they would contribute

No new hardware is needed: the station and the agencies already have these. What is missing — and what this project proposes — is the layer that **interprets** that data against the crew member's own baseline and shows where each claim comes from.

| System | What it measures | What it would contribute to Pulse-0G |
|---|---|---|
| **Bio-Monitor / Astroskin** (CSA) | ECG, heart rate and variability, blood pressure, respiration, SpO₂, skin temperature, actigraphy | A continuous series for the cardiac and sleep variables that are synthetic today |
| **EveryWear** (CNES/MEDES/ESA) | Hub for questionnaires, nutrition, medication and wearables | The manual input channel — mood, adherence, symptoms — with a timestamp |
| **Double Sensor / Thermo-Mini** (ESA/DLR) | Non-invasive core temperature at the forehead, and circadian rhythms | Would turn temperature into a continuous series and make the in-flight baseline shift visible |
| **Passive dosimeters** | Cumulative radiation dose | The only input needed today is manual, and it is already supported |

The design consequence is worth stating: **this project does not need a new sensor**. It needs the data already generated in flight to have a verifiable interpretation layer. That positions it as a complement to existing systems, not as competition.

### 2.4 What a real device could NOT do

It could not improve the quality of the evidence. A sensor delivers numbers with uncertainty; the threshold that decides whether that number matters still needs a source. **More data does not fix a lack of criteria.**

---

## 3. How AI would connect

There is **an optional local model, off by default**, and the rule has not changed: the model never produces a number. What does not exist is any dependency on it: without a model, the product answers exactly the same.

It is implemented like this: when the switch is turned on, the query is resolved first by the deterministic engine; then the model explains those already-anchored sentences; then a control compares **every number in the explained text against the numbers of the original text**, rejects causal language, and rejects diagnostic wording. If any of those appear, the paragraph is discarded, the reason is shown, and the engine's version stays. The call has a 25-second ceiling and any failure returns the deterministic answer with a visible note.

### 3.1 The role that makes sense

A **narrator**. Nothing more.

```
question → [deterministic engine computes] → structured results
         → [card retrieval]              → evidence
         → [model]                       → explains it in plain language
         → [verifier]                    → checks numbers, causality, diagnosis
         → answer, or struck
```

Three rules that are not negotiated:

1. **The model never produces a number.** It does not compute, average or round.
2. **The model does not add claims.** Its job is to phrase what is already anchored.
3. **The verifier runs after the model, not before.** The text being checked is the one the user will read.

### 3.2 What is gained and what is lost

| Gained | Lost |
|---|---|
| Explanations a non-medical crew member can read | Full determinism of the answer |
| Possibly freer questions than the eight fixed intents | A dependency on hardware or network |
| Fewer template-sounding sentences | Cold start and latency |

That is why the design keeps it **off by default** with the model-free path always available. If the model fails, the screen does not fall over: it degrades.

### 3.3 Where a model would genuinely help today

- Explaining a band in plain language to a crew member without medical training.
- Mapping free questions onto one of the eight intents instead of rejecting anything that does not match literally.
- Drafting the case-package report for the flight surgeon from results already computed.

### 3.4 Where it would not

- **Deciding a band.** That is a rule with a source, not an opinion.
- **Interpreting an image** without a validated model and without declaring its uncertainty.
- **Completing a missing datum.** A gap is information.
- **Talking about diagnosis.** The system does not diagnose, and a model does not change that.

---

## 4. Growth beyond the prototype

Four directions, ordered by the ratio between effort and value. The first three are natural extensions of what is built; the fourth is a different category of project.

### 4.1 More evidence coverage (days)

Today's bottleneck is not technical: it is documentary. Every indicator needs its card with a literal quote. With the validator and the protocol already written, adding coverage is reading work, not engineering.

- Pressure and heart-rate thresholds against clinical guidelines, **labelled as a terrestrial standard** and not as a flight criterion.
- Behavioural thresholds when NASA publishes them: the card that records their absence becomes the card that cites them.
- Action protocols per band, with their source, which today are scenario parameters.

### 4.2 More real data (weeks)

- A dataset with a continuous signal — for example a terrestrial PPG collection with an ECG reference — to test waveform processing, always labelled terrestrial and never presented as NASA.
- Longer mission series, if access to controlled data from other missions is opened.
- Environmental telemetry (cabin CO₂, radiation dose) to complete the closed-environment hazard.

### 4.3 From one crew member to a mission (months)

- **Roles**: crew and flight surgeon, with different permissions over the case package and the journal.
- **Multi-crew**: comparison across people without merging identities, which is exactly the error the system avoids by design today.
- **Mission phase**: different thresholds before, during and after flight, with the baseline computed per phase.
- **True disconnected mode**: it works without a network today; the next step is deferred synchronisation when the link returns, with explicit conflict resolution instead of "last write wins".

### 4.4 From tool to clinical system (years)

This requires things a prototype does not have and cannot fake: clinical validation, certification, identity management, formal audit and a medical programme behind it. The honest way to say it is this: **Pulse-0G is the interpretation and traceability layer, not the complete medical system.** Its value is that, when that system exists, the hardest part will already be solved: every claim about a person can be traced to its source.

---

## 5. The three decisions that hold everything up

1. **The number is not the product; the decision is.** That is why there are bands, actions and an alarm block instead of a wall of figures.
2. **No claim without a source.** That is why there are cards, a verifier and abstention instead of a chat.
3. **No invented data, not even to fill a gap.** That is why a missing value is drawn as a gap, a column with no name is refused, and a threshold with no source is marked provisional in front of the user.

Any future feature that breaks one of those three stops being this project.
