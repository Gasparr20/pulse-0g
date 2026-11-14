import type { Band, RefSource } from "./types";

export interface ThresholdConfig {
  label: string;
  unit: string;
  direction: "above" | "below";
  amber: number;
  red: number;
  baseline_tolerance_pct: number;
  evidence_card_id: string | null;
  provisional: boolean;
  action_amber: string;
  action_red: string;
}

export interface BandInput {
  value: number | null;
  refMin: number | null;
  refMax: number | null;
  refSource: RefSource;
  baseline: number | null;
  config?: ThresholdConfig;
}

export interface BandVerdict {
  band: Band;
  reason: string;
  provisional: boolean;
  evidenceCardId: string | null;
  delta: number | null;
  deltaPct: number | null;
  baselineShifted: boolean;
  action: string | null;
}

/** Two independent layers.
 *
 *  Layer 1 is the reference range, and it comes from the data file when the file
 *  provides one. That makes the citation the file itself, so no external
 *  threshold table is invented for those variables.
 *
 *  Layer 2 is the deviation from the subject's own pre-flight baseline. It never
 *  changes the band on its own — it is reported alongside, because a value can be
 *  inside the population range and still be a meaningful shift for this person.
 *
 *  A variable with neither a file range nor a cited threshold returns no_data with
 *  the reason "sin umbral citado". It is never guessed.
 */
const n = (v: number) => Math.round(v * 10) / 10;

export function classify(input: BandInput): BandVerdict {
  const { value, refMin, refMax, refSource, baseline, config } = input;
  const fromFile = refSource === "dataset_file" && (refMin !== null || refMax !== null);
  const cfg = fromFile ? undefined : config;

  let delta: number | null = null;
  let deltaPct: number | null = null;
  let baselineShifted = false;
  if (value !== null && baseline !== null && baseline !== 0) {
    delta = value - baseline;
    deltaPct = (delta / baseline) * 100;
    const tol = cfg?.baseline_tolerance_pct ?? 15;
    baselineShifted = Math.abs(deltaPct) >= tol;
  }

  if (value === null) {
    return {
      band: "no_data",
      reason: "sin medición registrada",
      provisional: cfg?.provisional ?? false,
      evidenceCardId: cfg?.evidence_card_id ?? null,
      delta: null,
      deltaPct: null,
      baselineShifted: false,
      action: "Registrar la medición o declararla faltante.",
    };
  }

  if (fromFile) {
    const low = refMin !== null && value < refMin;
    const high = refMax !== null && value > refMax;
    const range = `${refMin ?? "—"}–${refMax ?? "—"}`;
    if (low || high) {
      return {
        band: "amber",
        reason: `${n(value)} fuera del rango del archivo (${range})`,
        provisional: false,
        evidenceCardId: null,
        delta,
        deltaPct,
        baselineShifted,
        action: "Marcar para revisión; el archivo no define gravedad.",
      };
    }
    return {
      band: "green",
      reason: `${n(value)} dentro del rango del archivo (${range})`,
      provisional: false,
      evidenceCardId: null,
      delta,
      deltaPct,
      baselineShifted,
      action: null,
    };
  }

  if (!cfg) {
    return {
      band: "no_data",
      reason: "sin umbral citado",
      provisional: false,
      evidenceCardId: null,
      delta,
      deltaPct,
      baselineShifted,
      action: null,
    };
  }

  const over = cfg.direction === "above" ? value > cfg.amber : value < cfg.amber;
  const critical = cfg.direction === "above" ? value > cfg.red : value < cfg.red;
  const cmp = cfg.direction === "above" ? ">" : "<";

  if (critical) {
    return {
      band: "red",
      reason: `${n(value)} ${cmp} ${cfg.red} (provisional)`,
      provisional: true,
      evidenceCardId: cfg.evidence_card_id,
      delta,
      deltaPct,
      baselineShifted,
      action: cfg.action_red,
    };
  }
  if (over) {
    return {
      band: "amber",
      reason: `${n(value)} ${cmp} ${cfg.amber} (provisional)`,
      provisional: true,
      evidenceCardId: cfg.evidence_card_id,
      delta,
      deltaPct,
      baselineShifted,
      action: cfg.action_amber,
    };
  }
  return {
    band: "green",
    reason: `${n(value)} dentro del umbral ${cfg.amber} (provisional)`,
    provisional: true,
    evidenceCardId: cfg.evidence_card_id,
    delta,
    deltaPct,
    baselineShifted,
    action: null,
  };
}

export const BAND_ORDER: Record<Band, number> = {
  red: 0,
  amber: 1,
  no_data: 2,
  green: 3,
};

export function worst(bands: Band[]): Band {
  if (bands.length === 0) return "no_data";
  return [...bands].sort((a, b) => BAND_ORDER[a] - BAND_ORDER[b])[0];
}
