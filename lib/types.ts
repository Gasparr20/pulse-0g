export type Phase = "preflight" | "inflight" | "postflight";

export type OriginType =
  | "observed_real"
  | "replayed"
  | "injected_fault"
  | "synthetic";

/** Four states only. A missing threshold and a missing value are both "no_data",
 *  distinguished by the reason string so the UI can teach the difference. */
export type Band = "green" | "amber" | "red" | "no_data";

export type RefSource =
  | "dataset_file"
  | "demo_parameter"
  | "evidence_card"
  | "absent";

export type ZoneId = "head" | "thorax" | "arm" | "legs" | "eyes";

export interface MeasurementRow {
  id: number;
  dataset_id: string;
  subject_id: string;
  scenario_id: string | null;
  variable: string;
  value: number | null;
  unit: string | null;
  ref_min: number | null;
  ref_max: number | null;
  ref_source: RefSource;
  raw_value: string | null;
  time_label: string;
  recorded_at: string | null;
  recorded_at_source: string;
  phase: Phase;
  offset_days: number;
  sort_key: number;
  origin_type: OriginType;
  hazard: string | null;
  source_file: string;
  source_row: number | null;
  missing_token: string | null;
  quality_flags: string;
}

export interface SeriesPoint {
  label: string;
  sortKey: number;
  value: number | null;
}

export interface IndicatorView {
  variable: string;
  label: string;
  unit: string | null;
  value: number | null;
  display: string;
  band: Band;
  bandReason: string;
  provisional: boolean;
  evidenceCardId: string | null;
  refMin: number | null;
  refMax: number | null;
  refSource: RefSource;
  baseline: number | null;
  delta: number | null;
  deltaPct: number | null;
  baselineShifted: boolean;
  origin: OriginType;
  hazard: string | null;
  latestLabel: string;
  recordedAt: string | null;
  recordedAtDisplay: string | null;
  action: string | null;
  hazards: Array<{ id: string; title: string; url: string; source: string }>;
  /** The rule boundaries that produced this verdict, so a sentence that prints
   *  "2.9 < 5" can cite the 5 instead of being struck for it. */
  ruleAmber: number | null;
  ruleRed: number | null;
  flags: string[];
  series: SeriesPoint[];
  missingCount: number;
}

export type ZoneState = "measured" | "no_data" | "measurement_site";

export interface ZoneView {
  id: ZoneId;
  label: string;
  sublabel: string;
  state: ZoneState;
  band: Band;
  indicators: IndicatorView[];
  note: string | null;
  teaching: string | null;
}

export interface RadiationView {
  value: number | null;
  unit: string;
  max: number | null;
  band: Band;
  action: string | null;
  provisional: boolean;
  label: string;
}

export interface RealAnalyte {
  variable: string;
  unit: string | null;
  refMin: number | null;
  refMax: number | null;
  series: SeriesPoint[];
  missing: number;
  outOfRange: number;
}

export interface RealPanel {
  datasetId: string;
  title: string;
  license: string;
  sourceUrl: string;
  sha256: string | null;
  retrievedAt: string | null;
  subjectId: string | null;
  timepoints: string[];
  analytes: RealAnalyte[];
  pending: number;
  mismatch: boolean;
  note: string;
}

export interface QualityItem {
  id: string;
  label: string;
  value: string;
  detail: string;
}

export interface Dashboard {
  quality: QualityItem[];
  hero: {
    subjectLabel: string;
    clockLabel: string;
    subjectId: string;
    scenarioId: string;
    originType: OriginType;
    zones: ZoneView[];
    radiation: RadiationView;
  };
  real: RealPanel;
  missionClock: number | null;
  generatedAt: string;
}

/* ------------------------------------------------------------------ answers */

export type AnchorKind = "measurement" | "aggregate" | "card" | "policy";

export interface Anchor {
  kind: AnchorKind;
  ref: string;
  label: string;
  /** Every numeric value the anchor can legitimise. The verifier compares the
   *  numbers inside the sentence against this pool. */
  values: number[];
}

export interface Sentence {
  text: string;
  anchors: Anchor[];
  struck?: boolean;
  struckReason?: string;
}

export interface Answer {
  intent: string;
  question: string;
  title: string;
  sentences: Sentence[];
  cards: string[];
  refused: boolean;
  note: string | null;
}
