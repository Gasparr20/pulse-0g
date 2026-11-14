# Dónde salen los documentos y qué hay que buscar

Esta lista es el trabajo completo. Son **18 tarjetas**. Cada fila dice qué buscar y en qué sitio. No hay que decidir nada médico: se copia la cita y se sigue el protocolo de `evidence/README.md`.

## Paso 1 — Los seis lugares donde están todas las fuentes

Todos verificados hoy. Solo estos alcanzan.

| Sitio | Para qué sirve | Link |
|---|---|---|
| **NASA Human Research Program — Evidence Book** | **El documento principal.** Es un PDF enorme con un capítulo por riesgo: cardiovascular, hueso, sueño, conducta, radiación. De acá salen casi todas las citas. | https://humanresearchroadmap.nasa.gov/evidence/reports/Evidence-Book.pdf |
| HRP — página de evidencia | Lo mismo que el PDF pero navegable por riesgo, en capítulos. Más fácil para buscar. | https://humanresearchroadmap.nasa.gov/evidence/ |
| HRP — Risks | La lista oficial de los riesgos de salud en vuelo espacial. Sirve para las tarjetas de contexto. | https://humanresearchroadmap.nasa.gov/risks/ |
| HRP — Gaps | Preguntas abiertas de investigación. Sirve para el slide de "qué falta". | https://humanresearchroadmap.nasa.gov/gaps/ |
| NASA OSDR | Los datos reales que ya usa el software (OSD-575, OSD-656). | https://osdr.nasa.gov/bio/repo/ |
| NASA NTRS | Buscador de papers y reportes técnicos de NASA. | https://ntrs.nasa.gov/ |

Extra si hace falta: los estándares de NASA se buscan por número dentro de https://standards.nasa.gov/ (buscá "NASA-STD-3001"). Y para papers revisados por pares: Google Scholar con `spaceflight + <palabra clave>`.

## Paso 2 — Las 18 tarjetas

La columna **Buscar** son las palabras exactas en inglés para poner en el buscador del documento (Ctrl+F) o en Google Scholar.

### Tipo A — `threshold` (las 5 más importantes: sin estas no hay colores)

Estas cinco hacen que el chip "UMBRAL PROVISIONAL" desaparezca de la pantalla.

| ID | Tema | Buscar | Dónde |
|---|---|---|---|
| `EVD-CARDIO-001` | Presión arterial en vuelo | `orthostatic intolerance`, `cardiovascular deconditioning`, `blood pressure` | Evidence Book, capítulo Cardiovascular |
| `EVD-CARDIO-002` | Frecuencia cardíaca en reposo | `resting heart rate`, `cardiac deconditioning` | Evidence Book, Cardiovascular |
| `EVD-SLEEP-001` | Horas de sueño y restricción | `sleep duration`, `sleep restriction`, `circadian misalignment` | Evidence Book, capítulo Sleep |
| `EVD-BEHAV-001` | Estado de ánimo y monitoreo conductual | `behavioral health`, `mood`, `psychological countermeasures` | Evidence Book, BHP |
| `EVD-RAD-001` | Dosis acumulada y límite de carrera | `radiation career limit`, `effective dose`, `galactic cosmic radiation` | Evidence Book, Radiation / NASA-STD-3001 |

### Tipo B — `measurement` (5): cómo se mide cada cosa

| ID | Tema | Buscar | Dónde |
|---|---|---|---|
| `EVD-MEAS-001` | Toma de presión en microgravedad | `blood pressure measurement`, `cuff`, `arm position` | Evidence Book / NTRS |
| `EVD-MEAS-002` | Dispositivos y kit médico a bordo | `medical kit`, `onboard biomonitoring`, `wearable sensor` | NTRS |
| `EVD-MEAS-003` | Registro de sueño | `actigraphy`, `wrist actigraph`, `sleep log` | Evidence Book, Sleep |
| `EVD-MEAS-004` | Dosimetría de radiación | `passive dosimeter`, `radiation monitoring`, `crew dose` | Evidence Book, Radiation |
| `EVD-MEAS-005` | Evaluación ocular (SANS) — para la zona gris de los ojos | `SANS`, `spaceflight associated neuro-ocular syndrome`, `OCT fundus` | Evidence Book, SANS |

### Tipo C — `protocol` (3): qué acción tomar

| ID | Tema | Buscar | Dónde |
|---|---|---|---|
| `EVD-PROT-001` | Sueño insuficiente sostenido | `sleep countermeasures`, `lighting`, `melatonin` | Evidence Book, Sleep |
| `EVD-PROT-002` | Contramedidas de ejercicio | `exercise countermeasures`, `resistance exercise`, `ARED` | Evidence Book, Muscle/Bone |
| `EVD-PROT-003` | Cuándo escalar al flight surgeon | `flight surgeon`, `medical operations`, `private medical conference` | NTRS / HRP |

### Tipo D — `hazard` (5): una por cada hazard del desafío

Estas son las más fáciles: cada una es un párrafo de contexto.

| ID            | Hazard                      | Buscar                                                       | Dónde     |
| ------------- | --------------------------- | ------------------------------------------------------------ | --------- |
| `EVD-HAZ-001` | Radiación espacial          | `space radiation`, `GCR`, `solar particle event`             | HRP Risks |
| `EVD-HAZ-002` | Aislamiento y confinamiento | `isolation and confinement`, `behavioral health`             | HRP Risks |
| `EVD-HAZ-003` | Campos gravitatorios        | `bone loss`, `muscle atrophy`, `fluid shift`                 | HRP Risks |
| `EVD-HAZ-004` | Distancia a la Tierra       | `communication delay`, `autonomy`, `medical operations Mars` | HRP Risks |
| `EVD-HAZ-005` | Ambiente cerrado hostil     | `closed environment`, `CO2`, `air quality`                   | HRP Risks |

## Paso 3 — Cómo se hace una, en cuatro gestos

1. Abrís el link de la fila y hacés **Ctrl+F** con la palabra de la columna "Buscar".
2. **Copiás el párrafo en inglés tal cual** (sin traducir) → va en `quote`.
3. Le pasás **solo ese párrafo** a la IA con el mensaje que está en `evidence/README.md`.
4. Guardás el archivo `evidence/cards/EVD-XXXX-000.json` copiando `_TEMPLATE.json`.

**El orden importa:** primero la cita, después la IA. Nunca al revés.

## Paso 4 — Si no hay PDF

El Evidence Book completo es un PDF: bajalo una vez y corré `sha256sum Evidence-Book.pdf`. Ese hash va en las tarjetas que salgan de ahí.

Si la fuente es una página web sin PDF, guardá el HTML con Ctrl+S y calculá el hash de ese archivo. Si no podés guardarlo, poné `"sha256": "webpage"` y dejá la fecha real en `retrieved_at`. No inventes un hash.

## Orden de trabajo sugerido

1. Las **5 de tipo A** (threshold). Son las que cambian la pantalla.
2. Las **5 de tipo D** (hazard). Son las más rápidas y sirven para el pitch.
3. Las **5 de tipo B** (measurement). Alimentan el panel del brazo y de los ojos.
4. Las **3 de tipo C** (protocol). Son las que dan las acciones sugeridas.

Con las 5 de tipo A y las 5 de tipo D ya hay producto presentable.
