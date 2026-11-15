import { assemble } from "./assemble";
import { verify } from "./verify";
import type {
  Answer,
  Anchor,
  Dashboard,
  IndicatorView,
  Sentence,
  ZoneView,
} from "./types";

/** 8 answerable intents plus an explicit refusal. The model never turns a
 *  question into SQL, and there is no free-form query path: an unmatched
 *  question is refused, not guessed. */

const fmt = (n: number | null, digits = 1): string =>
  n === null ? "—" : String(Math.round(n * 10 ** digits) / 10 ** digits);

function normalise(text: string): string {
  return text
    .toLowerCase()
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "");
}

function labelNumber(label: string): number {
  const match = label.match(/\d+/);
  return match ? Number(match[0]) : 0;
}

function anchorFor(ind: IndicatorView): Anchor {
  const values = [
    ind.value,
    ind.baseline,
    ind.delta,
    ind.deltaPct,
    ind.refMin,
    ind.refMax,
    ind.missingCount,
    ind.series.length,
    labelNumber(ind.latestLabel),
    ind.ruleAmber,
    ind.ruleRed,
  ].filter((v): v is number => v !== null && Number.isFinite(v));
  return {
    kind: "measurement",
    ref: `${ind.variable}@${ind.latestLabel}`,
    label: `${ind.label} · ${ind.latestLabel}`,
    values,
  };
}

function seriesAnchor(ind: IndicatorView): Anchor {
  const values = ind.series
    .map((p) => p.value)
    .filter((v): v is number => v !== null);
  return {
    kind: "aggregate",
    ref: `series:${ind.variable}`,
    label: `${ind.series.length} muestras de ${ind.label}`,
    values: [ind.series.length, values.length, ...values],
  };
}

const POLICY_NO_DIAGNOSIS: Anchor = {
  kind: "policy",
  ref: "policy:no-diagnosis",
  label: "política del sistema: sin diagnóstico",
  values: [],
};

function say(text: string, anchors: Anchor[]): Sentence {
  return { text, anchors };
}

function allIndicators(dash: Dashboard): IndicatorView[] {
  return dash.hero.zones.flatMap((z) => z.indicators);
}

const SYNONYMS: Array<[RegExp, string]> = [
  [/presion|sistolica|diastolica|tension/, "systolic"],
  [/pulso|cardiaca|corazon|frecuencia/, "resting_hr"],
  [/suen|dormir|descanso|descansé/, "sleep_hours"],
  [/animo|humor|emocional|conduct/, "mood"],
  [/glucosa|azucar|metabolic/, "glucose"],
  [/radiacion|dosis|dosimetro/, "radiation_dose_cumulative"],
];

const ZONES: Array<[RegExp, string]> = [
  [/cabeza|neuro|mental|conductual/, "head"],
  [/torax|pecho|cardio|circulat/, "thorax"],
  [/brazo|manguito|medicion|medir/, "arm"],
  [/pierna|hueso|musculo/, "legs"],
  [/ojo|ocular|vision|vista/, "eyes"],
];

function findIndicator(dash: Dashboard, q: string): IndicatorView | null {
  for (const [pattern, variable] of SYNONYMS) {
    if (pattern.test(q)) {
      const found = allIndicators(dash).find((i) => i.variable === variable);
      if (found) return found;
    }
  }
  return null;
}

function findZone(dash: Dashboard, q: string): ZoneView | null {
  for (const [pattern, id] of ZONES) {
    if (pattern.test(q)) {
      const found = dash.hero.zones.find((z) => z.id === id);
      if (found) return found;
    }
  }
  return null;
}

type Handler = (dash: Dashboard, q: string) => Omit<Answer, "question"> | null;

function refuse(title: string, reason: string, note: string | null = null) {
  return {
    intent: "abstain",
    title,
    refused: true,
    note,
    cards: [] as string[],
    sentences: [say(reason, [
      {
        kind: "aggregate" as const,
        ref: "corpus:coverage",
        label: "alcance del corpus cargado",
        values: [],
      },
    ])],
  };
}

/* ------------------------------------------------------------------ intents */

const clinical: Handler = (dash, q) => {
  if (!/deshidrat|diagnostic|tengo |padezco|infecc|enfermedad|medicament|recet|tratamiento|curar/.test(q)) {
    return null;
  }
  const ind = findIndicator(dash, q);
  const anchors = ind ? [anchorFor(ind), POLICY_NO_DIAGNOSIS] : [POLICY_NO_DIAGNOSIS];
  return {
    intent: "clinical_request",
    title: "No puedo responder eso, y esa es la respuesta correcta",
    refused: true,
    note: "El sistema no diagnostica, no receta y no infiere estados clínicos. Puede mostrar el dato y la fuente; la interpretación es del flight surgeon.",
    cards: [],
    sentences: [
      say(
        "Un valor medido no equivale a un diagnóstico, y este software no tiene la información necesaria para sostener uno.",
        anchors,
      ),
      say(
        "Lo que sí puedo hacer es mostrarte el valor, el rango aplicable y la evidencia disponible para esa medición.",
        anchors,
      ),
    ],
  };
};

const radiation: Handler = (dash, q) => {
  if (!/radiacion|dosis|dosimetro|mSv/.test(q)) return null;
  const rad = dash.hero.radiation;
  if (rad.value === null) {
    return refuse(
      "Dosis de radiación",
      "No hay lecturas de dosímetro registradas en este escenario.",
    );
  }
  const anchor: Anchor = {
    kind: "measurement",
    ref: `radiation_dose_cumulative@latest`,
    label: "dosis acumulada",
    values: [rad.value, rad.max ?? 0],
  };
  return {
    intent: "radiation",
    title: "Dosis acumulada",
    refused: false,
    note: rad.provisional
      ? "El límite usado es un parámetro del escenario, todavía sin tarjeta de evidencia."
      : null,
    cards: [],
    sentences: [
      say(`La dosis acumulada es ${fmt(rad.value, 0)} ${rad.unit}.`, [anchor]),
      say(
        `El límite configurado para este escenario es ${fmt(rad.max, 0)} ${rad.unit}.`,
        [anchor],
      ),
      say(
        "La acumulada no se reinicia: cualquier lectura nueva se suma a la anterior.",
        [anchor],
      ),
    ],
  };
};

const series: Handler = (dash, q) => {
  const ind = findIndicator(dash, q);
  if (!ind) return null;
  const values = ind.series.filter((p) => p.value !== null).map((p) => p.value as number);
  const anchor = anchorFor(ind);
  const sAnchor = seriesAnchor(ind);
  const min = values.length ? Math.min(...values) : null;
  const max = values.length ? Math.max(...values) : null;
  const sentences: Sentence[] = [
    say(
      `La serie de ${ind.label} tiene ${ind.series.length} muestras, ${values.length} con valor.`,
      [sAnchor, anchor],
    ),
  ];
  if (min !== null && max !== null) {
    sentences.push(
      say(
        `El mínimo registrado es ${fmt(min)} ${ind.unit ?? ""} y el máximo ${fmt(max)} ${ind.unit ?? ""}.`,
        [{ ...sAnchor, values: [...sAnchor.values, min, max] }],
      ),
    );
  }
  if (ind.missingCount > 0) {
    sentences.push(
      say(
        `Hay ${ind.missingCount} muestras sin valor, y se muestran como huecos en la serie.`,
        [anchor],
      ),
    );
  }
  if (ind.baseline !== null && ind.value !== null) {
    sentences.push(
      say(
        `La base previa al vuelo es ${fmt(ind.baseline)} y la última lectura es ${fmt(ind.value)}.`,
        [anchor],
      ),
    );
  }
  return {
    intent: "series",
    title: `Serie de ${ind.label}`,
    refused: false,
    note: ind.provisional
      ? "La clasificación de esta serie usa un umbral provisional."
      : null,
    cards: ind.evidenceCardId && ind.evidenceCardId !== "PENDING" ? [ind.evidenceCardId] : [],
    sentences,
  };
};

const baseline: Handler = (dash, q) => {
  if (!/base|baseline|habitual|normal para mi|respecto a mi/.test(q)) return null;
  // If the question names an indicator, answer for that one. Listing four when one
  // was asked is noise, and it is what let the model mix blood pressure with mood.
  const named = findIndicator(dash, q);
  const shifted = (named ? [named] : allIndicators(dash)).filter((i) => i.delta !== null);
  if (shifted.length === 0) return null;
  const sentences = shifted.slice(0, 4).map((ind) => {
    const direction = (ind.delta ?? 0) >= 0 ? "por encima" : "por debajo";
    return say(
      `${ind.label}: ${fmt(ind.value)} contra una base de ${fmt(ind.baseline)}, ${Math.abs(ind.deltaPct ?? 0) === 0 ? "" : `${fmt(Math.abs(ind.deltaPct ?? 0), 0)} %`} ${direction} de tu propio registro previo al vuelo.`.replace("  ", " "),
      [anchorFor(ind)],
    );
  });
  return {
    intent: "baseline",
    title: named
      ? `Desvío de ${named.label.toLowerCase()} respecto de tu base`
      : "Desvío respecto de tu propia base",
    refused: false,
    note: "La base es la mediana de tus registros previos al lanzamiento, no un rango de población.",
    cards: [],
    sentences,
  };
};

const alerts: Handler = (dash, q) => {
  if (!/atencion|alerta|preocup|riesgo|fuera de rango|semaforo/.test(q)) return null;
  const flagged = allIndicators(dash).filter(
    (i) => i.band === "amber" || i.band === "red",
  );
  if (flagged.length === 0) {
    return {
      intent: "alerts",
      title: "Nada fuera de banda",
      refused: false,
      note: null,
      cards: [],
      sentences: [
        say(
          "Ningún indicador medido está fuera de su banda en este momento.",
          [
            {
              kind: "aggregate",
              ref: "count:out_of_band",
              label: "indicadores fuera de banda",
              values: [0],
            },
          ],
        ),
      ],
    };
  }
  return {
    intent: "alerts",
    title: `${flagged.length} indicadores requieren atención`,
    refused: false,
    note: "Una banda ámbar no es un diagnóstico: pide repetir la medición y registrar contexto.",
    cards: [],
    sentences: flagged.slice(0, 5).map((ind) =>
      say(`${ind.label}: ${ind.display} — ${ind.bandReason}.`, [anchorFor(ind)]),
    ),
  };
};

const missing: Handler = (dash, q) => {
  if (!/falta|faltante|sin dato|hueco|vacio|no registro/.test(q)) return null;
  const withGaps = allIndicators(dash).filter((i) => i.missingCount > 0);
  if (withGaps.length === 0) {
    return {
      intent: "missing",
      title: "Sin faltantes en los indicadores medidos",
      refused: false,
      note: null,
      cards: [],
      sentences: [
        say("Ningún indicador medido tiene muestras faltantes.", [
          {
            kind: "aggregate",
            ref: "count:missing",
            label: "indicadores con faltantes",
            values: [0],
          },
        ]),
      ],
    };
  }
  return {
    intent: "missing",
    title: "Datos faltantes",
    refused: false,
    note: "Un faltante declarado es información: se muestra como hueco y nunca como cero.",
    cards: [],
    sentences: withGaps.map((ind) =>
      say(
        `${ind.label} tiene ${ind.missingCount} muestras sin valor de ${ind.series.length} registradas.`,
        [
          {
            kind: "aggregate",
            ref: `missing:${ind.variable}`,
            label: `faltantes de ${ind.label}`,
            values: [ind.missingCount, ind.series.length],
          },
        ],
      ),
    ),
  };
};

const why: Handler = (dash, q) => {
  if (!/por que|porque/.test(q)) return null;
  if (!/clasifica|gris|umbral|provisional|banda|color|no aparece/.test(q)) return null;
  const ind = findIndicator(dash, q) ?? allIndicators(dash)[0];
  return {
    intent: "why",
    title: `Por qué ${ind.label} se clasifica así`,
    refused: false,
    note: ind.evidenceCardId === "PENDING"
      ? "Esta clasificación no tiene todavía una tarjeta de evidencia: el chip de la pantalla lo declara."
      : null,
    cards: ind.evidenceCardId && ind.evidenceCardId !== "PENDING" ? [ind.evidenceCardId] : [],
    sentences: [
      say(`La regla aplicada fue: ${ind.bandReason}.`, [anchorFor(ind)]),
      say(
        ind.refMin !== null || ind.refMax !== null
          ? `El rango usado viene de ${ind.refSource === "dataset_file" ? "el archivo de datos" : "un parámetro del escenario"} y sus extremos son ${fmt(ind.refMin)} y ${fmt(ind.refMax)}.`
          : "Esta variable no tiene rango de referencia en el archivo, así que sin umbral citado queda en gris.",
        [anchorFor(ind)],
      ),
    ],
  };
};

const provenance: Handler = (dash, q) => {
  if (!/de donde|fuente|origen|procedencia|real o simulado|es real/.test(q)) return null;
  const real = dash.real;
  return {
    intent: "provenance",
    title: "De dónde sale cada dato",
    refused: false,
    note: real.note,
    cards: [],
    sentences: [
      say(
        `El escenario de la misión es sintético: ${dash.hero.subjectId} no es una persona real.`,
        [
          {
            kind: "aggregate",
            ref: "dataset:SYNTHETIC-DEMO",
            label: "escenario sintético",
            values: [],
          },
        ],
      ),
      say(
        `Los datos reales son ${real.datasetId}, ${real.license}, con ${real.analytes.length} analitos y ${real.timepoints.length} tiempos por analito.`,
        [
          {
            kind: "aggregate",
            ref: `dataset:${real.datasetId}`,
            label: "inventario del dataset real",
            values: [real.analytes.length, real.timepoints.length],
          },
        ],
      ),
      say(
        "Los dos nunca comparten una serie ni un eje: el sintético vive en la pestaña de misión y el real en su propia pestaña.",
        [
          {
            kind: "aggregate",
            ref: "separation",
            label: "separación de fuentes",
            values: [],
          },
        ],
      ),
    ],
  };
};

// Order is deliberate: the specific intents must win over the generic ones.
const HANDLERS: Handler[] = [clinical, why, baseline, alerts, missing, provenance, radiation, series];

/* -------------------------------------------------------------- entry point */

export function answer(question: string, at: number | null = null): Answer {
  const q = normalise(question).trim();
  const dash = assemble(at);

  for (const handler of HANDLERS) {
    const result = handler(dash, q);
    if (result) {
      return {
        question,
        ...result,
        sentences: verify(result.sentences),
      };
    }
  }

  const fallback = refuse(
    "No tengo evidencia para responder esto",
    "Ninguna de las ocho consultas disponibles cubre esta pregunta.",
    "Prefiero abstenerme antes que producir una respuesta plausible sin respaldo.",
  );
  return {
    question,
    ...fallback,
    sentences: verify(fallback.sentences),
  };
}
