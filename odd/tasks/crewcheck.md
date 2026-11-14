# Pulse-0G — health self-assessment with evidence

NASA Space Apps Córdoba 2026 · Challenge: *Create Health Monitoring Software for Astronauts on Space Missions*.
Team: 2 people, one technical. Budget: 48 h. Deliverables: 30 s video (burnt-in yellow subtitles) + 4 min live deck.
Status: specs under review by owner. Stack decision open (D1).

## Specs

**S1 — Real and synthetic data are never in the same series.**
Requirement source: "Sintético como hero, datos reales aparte".
Every series on screen carries a visible `origin_type` label. A synthetic series and a real OSDR series never share an axis or a line. Synthetic data is never described as a NASA record.
Check: for each rendered chart the DOM exposes `data-origin-type`; no chart contains two distinct origin types.

**S2 — Every measurement carries provenance.**
Mandatory fields: `dataset_id, dataset_version, subject_id, variable, value, unit, time_label, time_anchor, phase, origin_type, scenario_id, source_file, source_row, hazard, quality_flags`.
Check: a row without `origin_type` or `source_file` is rejected by the importer and recorded in the rejection log; the DB refuses the insert.

**S3 — Ingest OSD-575 without inventing values.**
`N/A`, `NA` and empty cells are stored as missing, never as 0. `R+194` is kept and flagged as a discrepancy against the study narrative, never deleted. Time ordering is semantic (`L-92` < `L-3` < `R+1`), never alphabetical. Missing counts are reported per column.
Check: after ingest, (a) missing-cell count matches the raw file, (b) `L-92` sorts before `L-3`, (c) `R+194` exists and carries a provenance flag.

**S4 — Bands need a citation to exist.**
Two layers: population reference range and deviation from the subject's own pre-flight baseline. The engine returns reference, value, baseline, delta and band as separate fields.
Check: the band registry fails to load if any band lacks an existing `evidence_card_id`.

**S5 — Four states, never colour alone.**
`green / amber / red / no_data`. Each state renders colour + shape + text label.
Check: with the page rendered in greyscale, every state is still distinguishable.

**S6 — Body map: five regions plus two out-of-body elements.**
Regions: head (sleep, mood), thorax (blood pressure, resting heart rate), arm (measurement site), legs (bone/muscle, no data), eyes (SANS, no data). Out-of-body: a docked "blood panel" chip (real OSD-575 analytes) and a persistent radiation dose gauge. Radiation is not a body region and the blood panel is not an organ.
Check: each region is a keyboard-focusable element; selecting one opens a side panel without moving or re-scaling the figure; the figure shows the microcopy "Este mapa muestra indicadores medidos por zona. No es un diagnóstico por órgano."

**S7 — A region without data is grey and teaches.**
Requirement source: "la idea no es abarcar todo el cuerpo porque entiendo que hay muchos datos que no tengo y no podria ver datos del ojo por ejemplo".
Regions with no measurement show a hatched grey state, the text "sin medición en esta demo", and a cited `measurement` evidence card explaining how that would be measured on a real mission. No placeholder value is ever displayed.
Check: legs and eyes render zero numeric values.

**S8 — Indicator panel.**
Shows value, unit, band, delta against own baseline, trend with visible gaps, a one-line action, the supporting evidence cards and the comment thread.
Check: clicking any measured indicator opens a panel where all six elements are present.

**S9 — No interpolation. Ever.**
No point is generated between two observations. Gaps are drawn as gaps.
Check: a two-point series renders two marks and no line segment between non-adjacent samples.

**S10 — Evidence cards are curated, quoted and hashed.**
Minimum 18 cards as JSON, one file per card, under `evidence/cards/`. Mandatory fields per card: `id, kind, title_es, summary_es, quote, source_label, url, retrieved_at, sha256, applies_to, license`. `kind` is one of `threshold | hazard | protocol | measurement`. `quote` is the literal source text, untranslated.
Check: a card with `kind: threshold` and no `thresholds` object fails validation; a card with an empty `sha256` fails validation.

**S11 — Deterministic first; the model is optional.**
A fixed set of 8 answerable intents plus one explicit refusal answers completely with the language model switched off. The model never produces, adjusts or rounds a number.
Check: with the model flag off, every intent returns a complete answer with citations; `tools/check_answers.py` asserts this.

**S12 — The verifier is visible.**
Every sentence in an answer is anchored to a result row or an evidence card. A sentence without an anchor is rendered struck through and recorded in the rejection log.
Check: injecting an unanchored sentence into a response produces a struck-through line and one rejection-log entry.

**S13 — Explicit abstention.**
A question outside the card corpus returns "no tengo evidencia para esto" plus what is missing. No plausible unsourced answer is ever produced.
Check: an out-of-corpus question returns the abstention text and zero cited claims.

**S14 — Comments are append-only context, never evidence.**
Requirement source: "podria agregarse comentarios a ciertos reportes y quede registrado por si en un futuro necesitan consultar ciertos datos este el comentario y tener mas contexto".
Comments attach to a measurement, indicator, band event or case package. There is no update or delete; an edit creates a new revision pointing at the previous one. Each comment stores `author_role`, `created_at`, `mission_clock`. Comments travel inside the case package. They are labelled "observación de la tripulación (no verificada)" and never feed the verifier or the cited claims.
Check: (a) no DELETE or UPDATE path exists for comments, (b) an exported case package contains the thread, (c) removing all comments changes no number in any answer.

**S15 — The case package is independent.**
Requirement source: "cuando hayan datos inusuales que puedan mandarlo a especialistas de la nasa o a una ia mas potente, pero este sistema tiene que ser independiente a eso".
Export produces a JSON plus a human-readable report: indicators, bands fired, rules, cited cards, data-quality issues, comment thread, `scenario_id`. There is no real transmission and no integration. If the export is never used, every other feature still works.
Check: with the export module disabled, the full demo script completes.

**S16 — Local first, no network.**
Requirement source: "prefiero priorizar que funcione en mi compu y poder presentarlo aca".
The seeded database is committed to the repository; the demo starts from it and never runs an import live. No CDN, no remote fonts, no remote assets.
Check: with networking disabled, the full demo script completes and the browser console reports zero failed requests.

**S17 — The language model is secondary.**
Requirement source: "necesito que sea secundario, no desarrolles mas de esto ya que necesito la parte principal".
The model flag is off by default. Its absence changes no figure and blocks no screen.
Check: deleting the model configuration entirely leaves the app fully functional.

**S18 — The synthetic scenario is labelled and reproducible.**
Requirement source: "Sintético como hero, datos reales aparte".
The scenario records seed, generator version, parameters and a manifest of transformations. The label SINTÉTICO is visible wherever its data appears.
Check: regenerating from the manifest produces byte-identical values.

**S19 — Presentation deliverables.**
Requirement source: "el video tiene que ser de 30 segundos, tiene que ser tipico subtitulos en amarillo para que se vean bien, en formato de video esta bien, tambien se poria hacer una presentacion tipo powerpoint para acompañar la explicacion de 4 minutos de forma presencial".
Video: MP4 H.264 1920×1080, ≤29.5 s, burnt-in yellow subtitles, understandable with sound off. Deck: 8 slides, ≤20 words each, timing plan for 4 minutes.
Check: the video plays with the audio muted and the story is still complete.

## Tasks

| ID | Task | Specs | Route | Commit |
|---|---|---|---|---|
| T1 | Freeze stack decision, create project skeleton, seeded DB schema | S2, S16 | inline | a1202a0 |
| T2 | Synthetic mission scenario generator with manifest and labels | S18, S1 | inline | a1202a0 |
| T3 | OSD-575 importer with traps and rejection log | S3, S2 | inline | a1202a0 |
| T4 | Band engine, two layers, cited thresholds | S4, S5 | inline | a1202a0 |
| T5 | Body map SVG: 5 regions, radiation gauge | S6, S7 | inline | a1202a0 |
| T6 | Indicator panel: value, band, baseline delta, gapped trend, action | S8, S9 | inline | a1202a0 |
| T15 | Contract checks: intents, verifier, journal, case package | S3, S4, S12, S14, S15 | inline | e4e4e62 |
| T7 | 18 evidence cards, quoted and hashed (owner's partner) | S10 | parallel, separate files | — |
| T16 | Card loader: a valid threshold card replaces the provisional chip | S10, S4 | inline | dcdcdde |
| T17 | `tools/check_cards.py` gate: structure, quote-first rule, config cross-check | S10 | inline | dcdcdde |
| T8 | Query intents, tag retrieval, deterministic templates | S11 | inline | — |
| T9 | Claim verifier and rejection log | S12, S13 | inline | — |
| T10 | Append-only comment thread into case package | S14 | inline | e4e4e62 |
| T11 | Case package export, JSON + readable report | S15 | inline | e4e4e62 |
| T12 | Offline hardening and demo seeding | S16 | inline | a6ace3e |
| T13 | 30 s video with burnt-in subtitles and 8-slide deck | S19 | inline | — |
| T14 | Optional local model narrator, only if time remains | S17 | inline, droppable | — |

## Log

**L1 — original request (verbatim).**
"estoy haciendo un proyecto para un hackaton de la nasa en cordoba compitiendo en el desafio de create health monitoring software for astronauts on space missions, tiene esta descripcion para que estes al tanto: [desafío Space Apps 2026 «Create Health Monitoring Software for Astronauts on Space Missions», pegado completo por el usuario: cinco hazards —radiación, aislamiento y confinamiento, distancia a la Tierra, gravedad, ambiente cerrado hostil—; indicadores útiles: presión arterial, frecuencia cardíaca, glucemia, temperatura corporal, horas de sueño y ánimo; objetivos y consideraciones sobre UI, gamificación, gráficos dinámicos, código de colores, figura humana clickeable y explicaciones para tripulantes sin formación médica]. Ahora mismo se nos ocurrio esta idea para desarrollar un software que verifique datos biomedicos que nos den los sensores para medir la salud que la nasa ya tiene y pueda cargarlos en una base de datos con un sistema rag que pueda tener los datos con informacion extra de si la verifiacion fue buena, si falto algo, etc, para que con una ia poder consultarle sobre algun dato y me pueda brindar informacion real (no inventada) pero en lenguaje humano para que los astronautas puedan consultar cuando sea necesario, y cuando hayan datos inusuales que puedan mandarlo a especialistas de la nasa o a una ia mas potente, pero este sistema tiene que ser independiente a eso. esta es la idea completa: /home/gaspar_22/Descargas/Pulse-0G sin sensores  auditoría de fuentes y simulación.pdf analiza toda esta propuesta, decime si es posible hacerse, que fallas o errores encontras y si encontras mejores soluciones o mejoras al software, la idea es hacerlo en 48 horas ayudado de agentes de ia"

**L2 — decisions after the audit review.**
Hero narrative: "Sintético como hero, datos reales aparte". Model scope: "la idea es usar el llm para que sea algo distintivo, pero antes quiero que con todo esto me armes un resumen completo de como funcionaria antes de empezar a hacer algo". Strategic finding recorded: the PDF optimises for data integrity while the challenge scores impact and relevance, so triage bands and actions must exist; OSD-575 (4 subjects, 7 discrete timepoints) cannot carry the hero screen.

**L3 — body map scope and comments.**
"la idea no es abarcar todo el cuerpo porque entiendo que hay muchos datos que no tengo y no podria ver datos del ojo por ejemplo". Comments: "podria agregarse comentarios a ciertos reportes y quede registrado por si en un futuro necesitan consultar ciertos datos este el comentario y tener mas contexto".

**L4 — team, evidence cards, deliverables.**
Team: "somos dos, yo soy el mas tecnico y la otra chica es menor y va al secundario, pero me ayuda con ideas y para explicar cosas menos tecnicas". Cards: "las tarjetas las voy a hacer usando ia, mi compañera se encargara de eso de resumir los articulos y papers usando ia para mejorar la velocidad". Deliverables: "el video tiene que ser de 30 segundos, tiene que ser tipico subtitulos en amarillo para que se vean bien, en formato de video esta bien, tambien se poria hacer una presentacion tipo powerpoint para acompañar la explicacion de 4 minutos de forma presencial". Deployment: local machine first; packaged desktop app and downloadable local model explicitly secondary.

**L5 — repository location.**
Chosen: `/home/gaspar_22/dev/crewcheck`, independent git repo, ignored by the enclosing `/home/gaspar_22/dev` repository.

**D1 — open: stack.** `node` is currently unusable on the target machine (`libsimdjson.so.34` missing; installed `simdjson` provides `.so.36`; `nodejs 26.13.0-2` from cachyos, `nodejs-lts-krypton 24.22.3-1` available in extra). Python 3.14.9 works. Decision required before T1: repair node and use a single-process TypeScript stack, or use a Python stack with a build-free frontend.
