# Pulse-0G explained simply

For anyone who does not program and does not know medicine. No technical words.

> Spanish version: [`docs/RESUMEN-SIMPLE.md`](../RESUMEN-SIMPLE.md)

---

## What it is

A **health check sheet for astronauts** that the astronaut fills in alone, and which — beyond showing the number — tells them three things: whether that number is normal **for them**, what they have to do, and where that conclusion comes from.

The comparison that explains everything: when a doctor says "140/90, you're high", that is high compared with a general table. But if you have always been 110/70, a 140 is a huge jump. And if you have always been 135, a 140 is nothing.

On a Mars mission there is no doctor to say anything. And Earth's answer takes up to 22 minutes. So the astronaut needs something that says **"this is unusual for you"**, not "this is unusual in general".

## What it does

Three screens, each with a different job.

### Screen 1: how you are right now

There is a drawing of a person. The astronaut taps a region and sees the numbers for that part of the body.

- The **head** shows how long they slept and how their mood is.
- The **chest** shows pressure, pulse and temperature.
- The **arms** show how blood pressure is taken (where the cuff goes, how long to rest first).
- The **legs** and the **eyes** are grey and say "no measurement". That is deliberate: in this demonstration there is no instrument to measure them, and **no number is invented**.

Every number comes with a colour and a word. And underneath, in a single line, what to do: *"revisar el ciclo de sueño con el médico de vuelo"* (review the sleep cycle with the flight surgeon).

At the top there is a mission timeline: launch, month 1, month 3, month 4, month 6, and the return. You can go back and see how the person was at each moment. **On an ordinary day everything is green. By month 6 sleep collapses and the head turns red.**

### Screen 2: where all of it comes from

This is the library. It holds two things:

- **Real NASA data** from the Inspiration4 mission: blood and urine analyses from the four crew members, published and free to use.
- **Backing cards**: 25 documents where each one has a sentence copied word for word from the original, a summary in Spanish, and the link to go read it.

Those cards are what let the program say where each claim comes from. If a limit has no card, the program says so on screen: **"umbral provisional"** (provisional threshold).

And a nice part: real NASA files have errors. Missing values written in three different ways, a column with no name, a sample the study never mentions in its description. The program **does not fix them in silence**: it shows them as they are and notes what it found. A missing value looks like a gap, never like a zero.

### Screen 3: asking

The astronaut types a question and the program answers.

But it is not just any chat. It answers **nine things and nothing else**, and every sentence carries a tag saying where it came from. For example:

> **How is sleep going?**
> The series has 194 samples, 190 with a value. · The minimum is 1.7 h and the maximum 9 h. · Four samples have no value and are shown as gaps. · The pre-flight baseline is 7.3 and the latest reading is 2.9.
> *Every sentence, with its tag saying where it comes from.*

And when you ask something it cannot answer, **it says so**:

> **Am I dehydrated?**
> I cannot answer that, and that is the correct answer. A measured value is not a diagnosis.

There is also an optional switch that turns on a **local AI**, for comparison. With it on, a model running on the computer explains the same answer in plainer language. It is off by default, and the program checks every number the model writes against the data before showing it.

## How it does it: the three ideas that matter

### 1. It compares against you, not against the table

Every value is measured against two things: the normal range for any person **and** that person's average before launch. The second one is what almost nobody does.

A real example, from a paper: on the Space Station, resting core body temperature rises **one degree** compared with before the flight. One degree. If you use the normal table, where 37.5 already counts as fever, **every astronaut has a fever every day**. So the program does not use only that number: it compares against the person's own in-flight temperature, and reserves 38 as an absolute ceiling.

### 2. It does not trust itself

This is the strangest part and the strongest one.

Every sentence the program shows has to be **tied to a datum**. After building the answer, an independent check re-reads the text, finds every number and verifies that each one really exists in the data.

If a sentence cannot be backed, or carries a number that is not in the data, **the program strikes it in red, on screen, in front of the user**, and says why.

And it happened to the program itself: when it was built, it struck **seven sentences written by the person who made it**. A `9` that was really `8.96`. An `11 %` that was `-11`. That is what makes it trustworthy: it does not even believe itself.

### 3. If a datum is missing, it says so

It never fills a gap with an invented number. It never turns "no data" into zero. It never interpolates a line between two measurements to make the chart look nice.

A chart with a gap tells the truth. A completed chart lies elegantly.

## And artificial intelligence?

### Without AI: it works completely

Today the program **does not depend on AI**, and that is a decision. It answers with nine fixed recipes that query the data. Nothing is left to a model.

Why: the most important thing about this project is that it **does not invent**. A language model is precisely a machine for sounding convincing. And on a spacecraft — or at a hackathon with the event's laptop — you cannot depend on something that sometimes fails to start.

### With AI: a translator, not a doctor

The optional local model has a narrow role, and a comparison makes it clear:

- The AI **is not the doctor**. The doctor is already there: it is the data and the backing cards.
- The AI would be **the translator**: it takes the conclusion the program already computed and writes it more plainly, more naturally, easier to read.

Three rules that are not broken:

1. The AI **never invents a number**. Every number is put there by the program.
2. The AI **does not add new claims**. It is checked for numbers, for causal language and for diagnostic wording.
3. The control runs **after** the AI, on the final text the user is going to read.

What it gains: plainer explanations. What it risks: the model slipping in an interpretation, which is why it is off by default and why the version from the engine always stays underneath.

## Potential

**Short term.** More backing cards: it is a matter of reading and verifying documents, not writing new code. Every new indicator is one more card.

**Medium term.** Connecting real sensors. And here there is good news: **none need to be invented**. Canada already has a shirt that measures ECG, respiration, oxygen and temperature. Europe already has an app that gathers questionnaires, nutrition, medication and sensors. What is missing is not hardware: it is the layer that **interprets** that data against each person's own baseline and shows where each conclusion comes from. That is what this project proposes.

**Long term.** Serving a whole crew, with different permissions for the astronaut and for the flight surgeon on Earth. And, much further out, being part of a real medical system, which needs clinical validation and certification: things a prototype cannot fake.

## What it is NOT

- It does not diagnose disease.
- It does not replace the doctor.
- It does not invent data.
- It does not simulate the human body.
- It does not send information anywhere (the report for the doctor is generated and downloaded).

## What to remember from all of this

Three sentences:

1. **It does not show numbers: it shows decisions.**
2. **It does not trust itself: if it cannot back a sentence, it strikes it.**
3. **It does not fill gaps: if a datum is missing, it says so.**
