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
| T18 | Implement the console artboard in the real stack: table of indicators, alarm block, data-quality block, plain-language clock | S5, S6, S8, S16 | inline | — |
| T19 | Implement artboard 04: weight 800, NASA blue, and the four movement effects | S5, S8, S16 | inline | — |
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

**L6 — three visual directions for the product shell.**
`design/pulse-0g-style/` holds three artboards over the same FD180 data: `01-consola-de-vuelo.html` (MOCR instrument console, amber on warm black), `02-plano-tecnico.html` (engineering sheet with numbered callouts and hatched no-data zones), `03-manual-identidad.html` (1975 graphics-standards discipline: one hero number, red accent, white space). They differ in structure, not colour: rows, callouts, and editorial respectively. `design/system.md` syncs the current tokens from `app/globals.css` so each direction departs from it deliberately. No NASA mark is reproduced in any artboard: typography and grid discipline only, because implying endorsement is not available to this project.

**L7 — handoff: artboard 01 (consola de vuelo) implemented in the stack.**
`design/pulse-0g-style/01-consola-de-vuelo.html` is now the product shell, not a picture. What changed in `components/Dashboard.tsx` and `app/globals.css`: the per-indicator card stack became a selectable table (Indicador · Valor · Base · Δ · Banda) whose rows drive the alarm block and the detail card; the palette moved off teal to warm black with phosphor amber, so nominal is the quiet default and colour only appears when something needs a decision; the mission clock prints plain language (despegue, mes 1 … tierra) with the FD/R code kept for the technical reader; the action became a filled master-caution block; and the four data-quality figures now come from SQL counts in `lib/assemble.ts` instead of being typed into the component. Verified by build, by the two contract suites (`tools/check_answers.py`, `tools/check_case.py`), and by rendering at 1440x1024.

**L8 — 21 hazard cards received and verified.**
Every quote in the batch was searched literally on its own risk page: 21 of 21 found. Both URL shapes (`/Risks/?i=NN` and `/Risks/risk.aspx?i=NN`) resolve to the same document, so the cards' links are valid. `tools/import_cards.py` splits a pasted blob into one file per card, last id winning, so a corrected card placed after its original replaces it. Two cards are already in the repo as the reference format (`EVD-HAZ-001`, `EVD-HAZ-002`); the remaining 19 are pending import. Every hazard card still carries `sha256: webpage`, which the gate reports as a warning because the pages are versioned by NASA and will change.

**L9 — first threshold card, and the finding that beats it.**
`EVD-SLEEP-001` cites the HRP operational definition of sleep restriction ("total sleep time >0 and <6 hours per 24-hour period"), so the amber boundary at 6 h is now published rather than assumed. `EVD-BEHAV-001` records the opposite result: the same risk page states that behavioral-health thresholds still have to be set and normed to the astronaut population, so the mood rule keeps saying provisional and the card explains why. The band engine now compares strictly, matching the published "<6" (5.9 flags, 6.0 does not). A first version of the citation logic cleared the chip for the whole variable; it now clears only the boundary that fired, because citing the 6 h line does not license the 5 h line.

**L10 — handoff: artboard 04 (consola animada) implemented.**
`design/pulse-0g-style/04-consola-animada.html` is now the product. Type moved to weight 800 across labels, table, values and headings, with zero radius, 2px rules and a single hard shadow reserved for the alarm block. The header carries Pantone 286 (`#0B3D91`) from the NASA insignia on the identity chip and the 3px signature rule, with a lighter companion (`#3B7BD4`) because the pure value is invisible on near-black. Blue marks identity only; the dose gauge keeps its neutral frame because it reads status.
Four effects are live, all under 900 ms and none looping: the value counts up on change, the series draws itself, the claim strike draws, and red or amber zones flash once when the clock moves. All of it sits behind `prefers-reduced-motion`, and the final state is identical to the static layout, so the contract suites are unaffected.
Two decisions worth recording. The artboard's 900 ms "verificando" spinner was **not** implemented: the verification is instantaneous, and delaying it would fake work that already happened, so the effect only reveals the result. And the strike is almost never visible in production because the templates always anchor, so the verifier's own probe cases are now shown in the Consultar tab behind "Autoprueba del verificador" (`?probe=1` opens it): three sentences sustained and three struck, live.

**L11 — the handoff was re-sent, so it was re-verified, and the comparison found a bug.**
Rendering the implemented console next to the artboard at the same size showed the sleep series blank in the product and drawn in the spec. The cause: the draw-in hid the line with `stroke-dashoffset` and relied on a CSS transition to bring it back, so any interrupted or skipped transition left the chart permanently invisible. A chart that can stay hidden is a bug, not an animation. The effect now clears its inline dash styles after 1.2 s unconditionally, so the final state does not depend on the transition running. Re-verified by render and by both contract suites.

**L12 — the alert answer was being struck, and the suite did not notice.**
Asked at FD180, "¿qué está pidiendo atención?" printed "2.9 < 5 (provisional)" and the verifier struck it: the 5 is the rule boundary, and it was not among the anchored values. The rule's own numbers are data, so `IndicatorView` now exposes `ruleAmber` and `ruleRed` and the anchor includes them. The contract suite missed it because it queried with no mission clock, where nothing is out of band and the alert branch never runs; it now also probes FD180. Separately, the Consultar and Datos reales tabs gained a lead paragraph explaining what they do, and blue marks the system describing itself (panel rule, question catalogue, verifier self-test) while data and verdicts keep their status colours.

**L13 — second real dataset, and the evidence library in the product.**
`OSD-656` (urine inflammation panel) is now ingested: 8,888 measurements, 404 named variables, 4 subjects, 6 timepoints, and its two headerless columns refused and logged instead of guessed. The file also lacks `R+194`, which `OSD-575` has for the same four crew members; that cross-file discrepancy is recorded in the ingest audit and stated in the interface rather than harmonised away. The dataset is described, not charted: its values are normalised NPQ, so plotting them beside the metabolic panel would invite a comparison the units do not support.
The real-data tab also lists the evidence library: every card the system is allowed to cite, with its source link and verifier, so the tab answers "which documents back this?" as well as "what data is there?".

**L14 — the 19 remaining hazard cards are in, and every quote was re-verified.**
The category is complete: `EVD-HAZ-001` to `EVD-HAZ-021` plus `EVD-BEHAV-001`, 22 hazard cards, alongside the two threshold cards. Because the batch was transcribed into files rather than pasted from a saved blob, each quote was checked **in full** against its live risk page instead of by keyword: 23 of 23 found, no truncation at either end. The gate reports 24 cards, 0 errors, and 24 warnings that all say the same thing — `sha256` is still the placeholder `webpage`, so the cards record where a claim comes from but not which version of the page was read.
In the product, an indicator now cites the hazards that speak to its own hazard tag: the sleep card lists four, and the real-data tab carries the whole library as a table.

**L15 — the tab is now a library, and it is searchable.**
`Datos reales NASA` is renamed `Biblioteca` because it holds both halves of the same question: what was measured (the two published studies) and what backs each claim (the 24 cards). Search is lexical and client-side over id, kind, title, summary, source and tags, with kind filters and a visible `n de 24` counter; `?lib=<term>` preloads a query so a demo or a check can land on a result. Verified: "radiación" narrows 24 to 3 and surfaces `EVD-RAD-002` together with the two hazard cards that mention radiation in their summary, which is the behaviour a keyword match on titles would have missed.

**L16 — temperature becomes the third cited indicator, and the reasoning behind it is the project's best argument.**
`EVD-THERMO-001` quotes Stahn et al. 2017 (Scientific Reports): "At rest CBT was increased by about 1.01 °C on the ISS compared to baseline". The scenario already carried 194 temperature readings that no zone displayed; the thorax now shows them, classified against a cited 38.0 °C ceiling with the deviation-from-own-baseline layer doing the real work, because a 1 °C shift makes almost every crew member look febrile against a population threshold of 37.5 °C. Verified in the app: at FD120 the injected 38.4 °C artifact reads amber and cited; at FD180 36.49 °C reads green.
The ESA/CSA source list that prompted this was checked first: all seven DOIs resolve to the papers claimed, but the PMID given for Stahn (29170585) belongs to a different article — the correct one is 29170507 — and both Canadian Space Agency links are dead. Recorded so nobody repeats the wrong identifier in a slide.
Also written: `docs/PROJECT.md` (complete description for the team's presentation) and `docs/ARQUITECTURA-Y-CRECIMIENTO.md` (how a measurement flows end to end, how sensors would connect, what role an LLM could take, and the four growth paths).

**L17 — the optional local model exists now, with the check after it.**
A toggle in the Consultar tab switches between template answers and a local model (`qwen2.5-coder:7b` on Ollama) that rewrites the sentences the deterministic engine already anchored. It is off by default; the button reads `IA local: activa / apagada / no disponible`, colours itself with the NASA blue when on, and explains the state in one line. Turning it on fires a warm-up so the first question is not eight seconds of cold start.
The safety property is the same one the docs promised: after the model writes, every number in its paragraph is compared against the numbers of the source sentences. A wrong figure discards the paragraph, shows the reason, and leaves the engine's version standing underneath. Verified in three states — model present (2.5 s warm, all figures preserved), model missing (`nodo disponible`, answers unchanged), and the deterministic path with the toggle off, which all three contract suites still cover.

**L18 — the model rewrites too little, then explains too much, and both are informative.**
The first version asked the model to rewrite the anchored sentences; the output was a paraphrase of what was already on screen, so the toggle showed no difference worth seeing. The instruction is now to *explain*, which is the thing the templates cannot do and which the challenge explicitly asks for ("do not assume astronauts know how to assess their health").
Two guards had to be added because a number check was not enough: one rejects causal language ("esto indica", "debido a") and one rejects diagnostic wording. Both were earned, not guessed — the first explanation produced ("esto indica que el tripulante ha estado teniendo dificultades para dormir") was an interpretation the data does not contain.
Then the number check earned itself too: asked about sleep, the model wrote "menos de 2 horas" and "casi 10 horas" when the data says 1.7 and 9. The paragraph was discarded with its reason and the engine's version stood. That failure is the demo, not a bug: a guard that only works on canned examples is not a guard.

**L19 — a prose model, and the two real defects it exposed.**
Installed `qwen2.5:7b` and made the narrator pick the best installed model from a preference list instead of hardcoding a tag, so the app adapts to the machine. The prose is markedly better than the coder model's, and it immediately surfaced two defects the previous model had hidden: the `baseline` intent answered about four indicators even when the question named one (which is why an answer about blood pressure mentioned mood), and the model placed FD180 facts "before the flight" because nothing told it which moment it was describing. The first is now scoped to the named indicator; the second is fixed by passing the mission moment into the prompt.
GitHub: `gh` 2.104.0 is installed, the repository has no remote, and the CLI is not authenticated, so a repository cannot be created until the human logs in.
