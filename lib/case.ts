import { createHash } from "node:crypto";
import { readdirSync, readFileSync } from "node:fs";
import path from "node:path";
import { assemble } from "./assemble";
import { listComments } from "./journal";

export interface CasePackage {
  packageId: string;
  generatedAt: string;
  subject: string;
  scenarioId: string | null;
  originType: string;
  missionClock: string;
  indicators: Array<{
    variable: string;
    label: string;
    value: number | null;
    unit: string | null;
    band: string;
    reason: string;
    action: string | null;
    baseline: number | null;
    deltaPct: number | null;
    refRange: [number | null, number | null];
    refSource: string;
    flags: string[];
    evidenceCardId: string | null;
  }>;
  dataQuality: string[];
  comments: Array<{
    id: number;
    authorRole: string;
    body: string;
    createdAt: string;
    missionClock: string;
  }>;
  evidenceCards: string[];
  report: string;
  warning: string;
}

function clockLabel(clock: number | null): string {
  if (clock === null) return "—";
  if (clock >= 1_000_000) return `R+${clock - 1_000_000}`;
  if (clock < 0) return `L-${Math.abs(clock)}`;
  return `FD${clock}`;
}

function cardsOnDisk(): string[] {
  try {
    return readdirSync(path.join(process.cwd(), "evidence", "cards"))
      .filter((f) => f.startsWith("EVD-") && f.endsWith(".json"))
      .map((f) => f.replace(".json", ""));
  } catch {
    return [];
  }
}

/** The case package is deliberately independent: it reads what is already
 *  computed, writes nothing, sends nothing, and nothing else depends on it. */
export function buildCasePackage(at: number | null): CasePackage {
  const dash = assemble(at);
  const indicators = dash.hero.zones
    .flatMap((zone) => zone.indicators)
    .map((ind) => ({
      variable: ind.variable,
      label: ind.label,
      value: ind.value,
      unit: ind.unit,
      band: ind.band,
      reason: ind.bandReason,
      action: ind.action,
      baseline: ind.baseline,
      deltaPct: ind.deltaPct,
      refRange: [ind.refMin, ind.refMax] as [number | null, number | null],
      refSource: ind.refSource,
      flags: ind.flags,
      evidenceCardId: ind.evidenceCardId,
    }));

  const dataQuality = [
    ...indicators
      .filter((i) => i.flags.length > 0 || i.value === null)
      .map((i) =>
        `${i.variable}: ${i.value === null ? "sin valor" : "valor presente"}${
          i.flags.length ? ` [${i.flags.join(", ")}]` : ""
        }`,
      ),
    `dataset real OSD-575: ${dash.real.pending} valor(es) sin rango en el archivo`,
    dash.real.mismatch ? "OSD-575: R+194 presente y fuera de la narrativa del estudio" : "",
  ].filter(Boolean);

  const comments = listComments(dash.hero.subjectId).map((c) => ({
    id: c.id,
    authorRole: c.author_role,
    body: c.body,
    createdAt: c.created_at,
    missionClock: c.mission_clock,
  }));

  const warning =
    "El escenario es sintético y los umbrales marcados como provisionales no tienen todavía tarjeta de evidencia. Este paquete no es un diagnóstico.";

  const lines: string[] = [];
  const clock = clockLabel(at);
  lines.push("CREWCHECK — PAQUETE DE CASO");
  lines.push("===========================");
  lines.push(`Tripulante: ${dash.hero.subjectLabel} (${dash.hero.subjectId})`);
  lines.push(`Escenario:  ${dash.hero.scenarioId} · origen: ${dash.hero.originType}`);
  lines.push(`Momento:    ${clock}`);
  lines.push(`Generado:   ${new Date().toISOString()}`);
  lines.push("");
  lines.push("INDICADORES");
  for (const i of indicators) {
    const range =
      i.refRange[0] === null && i.refRange[1] === null
        ? "sin rango"
        : `${i.refRange[0]}–${i.refRange[1]}`;
    lines.push(
      `  ${i.label}: ${i.value ?? "sin medición"} ${i.unit ?? ""} — banda ${i.band}`,
    );
    lines.push(`    regla:   ${i.reason}`);
    lines.push(`    rango:   ${range} (${i.refSource})`);
    if (i.action) lines.push(`    acción:  ${i.action}`);
    if (i.evidenceCardId === "PENDING") lines.push("    evidencia: pendiente");
  }
  lines.push("");
  lines.push("CALIDAD DE DATOS");
  for (const q of dataQuality) lines.push(`  - ${q}`);
  lines.push("");
  lines.push("BITÁCORA DE LA TRIPULACIÓN (no verificada)");
  if (comments.length === 0) {
    lines.push("  sin comentarios registrados");
  } else {
    for (const c of comments) {
      lines.push(`  [${c.missionClock}] ${c.authorRole}: ${c.body}`);
    }
  }
  lines.push("");
  lines.push(`HECHO: ${warning}`);

  const report = lines.join("\n");
  const packageId = createHash("sha256")
    .update(JSON.stringify({ indicators, comments, at }))
    .digest("hex")
    .slice(0, 16);

  return {
    packageId,
    generatedAt: new Date().toISOString(),
    subject: dash.hero.subjectId,
    scenarioId: dash.hero.scenarioId,
    originType: dash.hero.originType,
    missionClock: clock,
    indicators,
    dataQuality,
    comments,
    evidenceCards: cardsOnDisk(),
    report,
    warning,
  };
}
