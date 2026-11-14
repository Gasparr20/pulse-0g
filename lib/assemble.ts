import bandsJson from "@/config/bands.json";
import { all, one } from "./db";
import { classify, worst, type ThresholdConfig } from "./bands";
import type {
  Dashboard,
  IndicatorView,
  MeasurementRow,
  OriginType,
  RealAnalyte,
  RealPanel,
  SeriesPoint,
  ZoneId,
  ZoneState,
  ZoneView,
} from "./types";

const CONFIG = bandsJson as unknown as Record<string, ThresholdConfig | string>;

function thresholdFor(variable: string): ThresholdConfig | undefined {
  const entry = CONFIG[variable];
  return entry && typeof entry === "object" ? entry : undefined;
}

const HERO_SUBJECT = "SYNTH:ASTRO-01";
const REAL_SUBJECT = "OSD-575:C001";

const ZONES: Array<{
  id: ZoneId;
  label: string;
  sublabel: string;
  variables: string[];
  state: ZoneState;
  teaching?: string;
}> = [
  {
    id: "head",
    label: "Neuroconductual",
    sublabel: "Sueño y estado de ánimo",
    variables: ["sleep_hours", "mood"],
    state: "measured",
  },
  {
    id: "thorax",
    label: "Cardiovascular",
    sublabel: "Presión y frecuencia en reposo",
    variables: ["systolic", "diastolic", "resting_hr"],
    state: "measured",
  },
  {
    id: "arm",
    label: "Sitio de medición",
    sublabel: "Manguito y sensor de muñeca",
    variables: [],
    state: "measurement_site",
    teaching:
      "Sentado o sujeto con la correa de pies. Brazo apoyado a la altura del corazón. Cinco minutos de reposo. Dos tomas separadas por un minuto. La calidad de la señal se registra con la lectura, no después.",
  },
  {
    id: "legs",
    label: "Hueso y músculo",
    sublabel: "Sin medición en esta demo",
    variables: [],
    state: "no_data",
    teaching:
      "En una misión real esta región se evalúa con densitometría ósea, ultrasonido muscular y marcadores de recambio en sangre. Esta demostración no incluye esos instrumentos, así que no muestra valores.",
  },
  {
    id: "eyes",
    label: "Neuro-ocular (SANS)",
    sublabel: "Sin medición en esta demo",
    variables: [],
    state: "no_data",
    teaching:
      "El síndrome neuro-ocular asociado al vuelo espacial se evalúa con fondo de ojo, tomografía de coherencia óptica y ecografía ocular. Ninguna de esas mediciones está en esta demostración.",
  },
];

function median(values: number[]): number | null {
  if (values.length === 0) return null;
  const s = [...values].sort((a, b) => a - b);
  const mid = Math.floor(s.length / 2);
  return s.length % 2 ? s[mid] : (s[mid - 1] + s[mid]) / 2;
}

const MONTHS = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"];

/** Formats an ISO stamp without touching the timezone: the stored value is
 *  already mission-local and must be shown exactly as recorded. */
function stamp(iso: string | null): string | null {
  if (!iso) return null;
  const [date, time] = iso.split("T");
  const [y, m, d] = date.split("-");
  return `${d} ${MONTHS[Number(m) - 1]} ${y} · ${time.slice(0, 5)}`;
}

function round(n: number, digits = 1): number {
  const f = 10 ** digits;
  return Math.round(n * f) / f;
}

function flagsOf(row: MeasurementRow): string[] {
  try {
    return JSON.parse(row.quality_flags) as string[];
  } catch {
    return [];
  }
}

function buildIndicator(rows: MeasurementRow[]): IndicatorView {
  const ordered = [...rows].sort((a, b) => a.sort_key - b.sort_key);
  const last = ordered[ordered.length - 1];
  const cfg = thresholdFor(last.variable);
  const preflight = ordered
    .filter((r) => r.phase === "preflight" && r.value !== null)
    .map((r) => r.value as number);
  const baseline = median(preflight);
  const verdict = classify({
    value: last.value,
    refMin: last.ref_min,
    refMax: last.ref_max,
    refSource: last.ref_source,
    baseline,
    config: cfg,
  });
  const series: SeriesPoint[] = ordered.map((r) => ({
    label: r.time_label,
    sortKey: r.sort_key,
    value: r.value,
  }));
  const unit = last.unit ?? "";
  return {
    variable: last.variable,
    label: cfg?.label ?? last.variable.replace(/_/g, " "),
    unit: last.unit,
    value: last.value,
    display:
      last.value === null
        ? "sin medición"
        : `${round(last.value, 1)}${unit ? ` ${unit}` : ""}`,
    band: verdict.band,
    bandReason: verdict.reason,
    provisional: verdict.provisional,
    evidenceCardId: verdict.evidenceCardId,
    refMin: last.ref_min,
    refMax: last.ref_max,
    refSource: last.ref_source,
    baseline: baseline === null ? null : round(baseline, 2),
    delta: verdict.delta === null ? null : round(verdict.delta, 2),
    deltaPct: verdict.deltaPct === null ? null : round(verdict.deltaPct, 0),
    baselineShifted: verdict.baselineShifted,
    origin: last.origin_type,
    hazard: last.hazard,
    latestLabel: last.time_label,
    recordedAt: last.recorded_at,
    recordedAtDisplay: stamp(last.recorded_at),
    action: verdict.action,
    flags: flagsOf(last),
    series,
    missingCount: ordered.filter((r) => r.value === null).length,
  };
}

function heroZones(): ZoneView[] {
  const rows = all<MeasurementRow>(
    "SELECT * FROM measurement WHERE subject_id = ? ORDER BY sort_key",
    HERO_SUBJECT,
  );
  const byVariable = new Map<string, MeasurementRow[]>();
  for (const r of rows) {
    const list = byVariable.get(r.variable) ?? [];
    list.push(r);
    byVariable.set(r.variable, list);
  }
  return ZONES.map((zone) => {
    const indicators = zone.variables
      .map((v) => byVariable.get(v))
      .filter((list): list is MeasurementRow[] => Boolean(list && list.length))
      .map(buildIndicator);
    return {
      id: zone.id,
      label: zone.label,
      sublabel: zone.sublabel,
      state: zone.state,
      band: zone.state === "measured" ? worst(indicators.map((i) => i.band)) : "no_data",
      indicators,
      note:
        zone.state === "no_data" ? "sin instrumento en esta demo" : null,
      teaching: zone.teaching ?? null,
    };
  });
}

function radiation(): Dashboard["hero"]["radiation"] {
  const rows = all<MeasurementRow>(
    "SELECT * FROM measurement WHERE subject_id = ? AND variable = 'radiation_dose_cumulative' ORDER BY sort_key",
    HERO_SUBJECT,
  );
  if (rows.length === 0) {
    return {
      value: null,
      unit: "mSv",
      max: null,
      band: "no_data",
      action: null,
      provisional: false,
      label: "Dosis acumulada",
    };
  }
  const last = rows[rows.length - 1];
  const cfg = thresholdFor("radiation_dose_cumulative");
  const verdict = classify({
    value: last.value,
    refMin: null,
    refMax: null,
    refSource: "demo_parameter",
    baseline: 0,
    config: cfg,
  });
  return {
    value: last.value,
    unit: last.unit ?? "mSv",
    max: cfg?.red ?? null,
    band: verdict.band,
    action: verdict.action,
    provisional: verdict.provisional,
    label: "Dosis acumulada",
  };
}

function realPanel(): RealPanel {
  const dataset = one<{
    id: string;
    title: string;
    license: string;
    source_url: string;
    sha256: string | null;
    retrieved_at: string | null;
  }>("SELECT * FROM dataset WHERE id = 'OSD-575'");

  const rows = all<MeasurementRow>(
    "SELECT * FROM measurement WHERE subject_id = ? ORDER BY sort_key",
    REAL_SUBJECT,
  );
  const byVariable = new Map<string, MeasurementRow[]>();
  for (const r of rows) {
    const list = byVariable.get(r.variable) ?? [];
    list.push(r);
    byVariable.set(r.variable, list);
  }
  const analytes: RealAnalyte[] = [...byVariable.entries()]
    .sort((a, b) => a[0].localeCompare(b[0]))
    .map(([variable, list]) => {
      const ordered = [...list].sort((a, b) => a.sort_key - b.sort_key);
      const first = ordered[0];
      let outOfRange = 0;
      for (const r of ordered) {
        if (r.value === null) continue;
        if ((r.ref_min !== null && r.value < r.ref_min) ||
            (r.ref_max !== null && r.value > r.ref_max)) outOfRange += 1;
      }
      return {
        variable,
        unit: first.unit,
        refMin: first.ref_min,
        refMax: first.ref_max,
        series: ordered.map((r) => ({
          label: r.time_label,
          sortKey: r.sort_key,
          value: r.value,
        })),
        missing: ordered.filter((r) => r.value === null).length,
        outOfRange,
      };
    });

  const pending =
    one<{ c: number }>(
      "SELECT COUNT(*) AS c FROM measurement WHERE dataset_id='OSD-575' AND ref_source='absent'",
    )?.c ?? 0;
  const mismatch =
    (one<{ c: number }>(
      "SELECT COUNT(*) AS c FROM ingest_audit WHERE dataset_id='OSD-575' AND kind='discrepancy'",
    )?.c ?? 0) > 0;

  return {
    datasetId: dataset?.id ?? "OSD-575",
    title: dataset?.title ?? "OSD-575",
    license: dataset?.license ?? "CC0-1.0",
    sourceUrl: dataset?.source_url ?? "",
    sha256: dataset?.sha256 ?? null,
    retrievedAt: dataset?.retrieved_at ?? null,
    subjectId: REAL_SUBJECT,
    timepoints: rows
      .map((r) => r.time_label)
      .filter((v, i, a) => a.indexOf(v) === i)
      .sort((a, b) => {
        const sa = rows.find((r) => r.time_label === a)?.sort_key ?? 0;
        const sb = rows.find((r) => r.time_label === b)?.sort_key ?? 0;
        return sa - sb;
      }),
    analytes,
    pending,
    mismatch,
    note:
      "Cuatro tripulantes, siete muestras puntuales. No es una señal continua: no hay pulso, sueño ni ánimo en este archivo. El estudio publica tiempos relativos (L-92, R+1) y ninguna fecha calendario, así que acá no se inventa una.",
  };
}

export function assemble(): Dashboard {
  return {
    hero: {
      subjectLabel: "ASTRO-01",
      subjectId: HERO_SUBJECT,
      scenarioId: "SCN-MARS-180",
      originType: "synthetic" as OriginType,
      zones: heroZones(),
      radiation: radiation(),
    },
    real: realPanel(),
    generatedAt: new Date().toISOString(),
  };
}
