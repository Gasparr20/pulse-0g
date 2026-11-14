"use client";

import { useEffect, useRef, useState } from "react";
import BodyMap from "./BodyMap";
import Sparkline from "./Sparkline";
import AskPanel from "./AskPanel";
import CasePackage from "./CasePackage";
import Comments from "./Comments";
import { BAND_ORDER } from "@/lib/bands";
import type {
  Dashboard as DashboardData,
  IndicatorView,
  QualityItem,
  ZoneView,
} from "@/lib/types";

/** Counts the big value up when it changes, so the eye follows the number instead
 *  of finding it already in place. Falls back to the final value when motion is
 *  off, and never runs longer than 700 ms. */
function useCountUp(target: number | null): number | null {
  const [shown, setShown] = useState<number | null>(target);
  const from = useRef<number | null>(target);

  useEffect(() => {
    const reduced =
      typeof window !== "undefined" &&
      window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    if (target === null || reduced) {
      setShown(target);
      from.current = target;
      return;
    }
    const start = from.current ?? 0;
    if (start === target) {
      setShown(target);
      return;
    }
    let frame = 0;
    const t0 = performance.now();
    const step = (now: number) => {
      const p = Math.min((now - t0) / 700, 1);
      const eased = 1 - Math.pow(1 - p, 3);
      setShown(start + (target - start) * eased);
      if (p < 1) frame = requestAnimationFrame(step);
      else from.current = target;
    };
    frame = requestAnimationFrame(step);
    return () => cancelAnimationFrame(frame);
  }, [target]);

  return shown;
}

const MONTHS = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"];

const STEPS = [
  { at: 0, label: "despegue" },
  { at: 30, label: "mes 1" },
  { at: 90, label: "mes 3" },
  { at: 120, label: "mes 4" },
  { at: 180, label: "mes 6" },
  { at: 1000029, label: "tierra" },
];

function clockLabel(clock: number): string {
  if (clock >= 1_000_000) return `R+${clock - 1_000_000}`;
  if (clock < 0) return `L-${Math.abs(clock)}`;
  return `FD${clock}`;
}

function fmt(n: number | null, digits = 1): string {
  if (n === null) return "—";
  return String(Math.round(n * 10 ** digits) / 10 ** digits);
}

function dateOf(ind: IndicatorView | undefined): string {
  const iso = ind?.recordedAt;
  if (!iso) return "";
  const [y, m, d] = iso.split("T")[0].split("-");
  return `${d} ${MONTHS[Number(m) - 1]} ${y}`;
}

/** The row's second line answers "where does this number come from", not
 *  "which internal flags were set". */
function rowDetail(ind: IndicatorView): string {
  const parts: string[] = [];
  if (ind.refMin !== null || ind.refMax !== null) {
    parts.push(
      `rango ${fmt(ind.refMin)}–${fmt(ind.refMax)} ${ind.refSource === "dataset_file" ? "del archivo" : "del escenario"}`,
    );
  } else {
    parts.push("sin rango en el archivo");
  }
  if (ind.missingCount > 0) parts.push(`${ind.missingCount} sin valor`);
  else parts.push(`${ind.series.length} muestras`);
  return parts.join(" · ");
}

function bandLabel(band: IndicatorView["band"]): string {
  if (band === "red") return "acción";
  if (band === "amber") return "atención";
  if (band === "no_data") return "sin dato";
  return "en rango";
}

/* ------------------------------------------------------------------ pieces */

function Quality({ items }: { items: QualityItem[] }) {
  return (
    <div className="quality">
      <p className="panel-title" style={{ margin: "0 0 8px" }}>
        Calidad de datos
      </p>
      <p className="intro">
        Qué encontró el importador en los archivos originales y qué hizo con eso. Nada se corrige
        en silencio.
      </p>
      <ul>
        {items.map((item) => (
          <li key={item.id}>
            <span className="k">{item.label}</span>
            <b>{item.value}</b>
            <span className="d">{item.detail}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}

function ActionBar({ indicator, zone }: { indicator: IndicatorView | null; zone: ZoneView }) {
  const fallback = zone.indicators
    .filter((i) => i.action)
    .sort((a, b) => BAND_ORDER[a.band] - BAND_ORDER[b.band])[0];
  const source = indicator?.action ? indicator : fallback;

  if (!source?.action) {
    return (
      <div
        className="actionbar"
        style={{ background: "transparent", border: "1px solid var(--hair-2)", color: "var(--text-2)" }}
      >
        <span className="k" style={{ color: "var(--text-2)" }}>
          Sin acción requerida
        </span>
        <span className="v" style={{ color: "var(--text)", fontSize: 18 }}>
          Nada fuera de banda en {zone.label.toLowerCase()}. La serie se sigue registrando.
        </span>
      </div>
    );
  }

  return (
    <div className="actionbar" data-band={source.band === "amber" ? "amber" : "red"} role="note">
      <span className="k">Acción requerida</span>
      <span className="v">{source.action}</span>
      <span className="ref">
        {source.label.toLowerCase()} · {fmt(source.value)} {source.unit ?? ""} contra una base de{" "}
        {fmt(source.baseline)} {source.unit ?? ""}
        {source.provisional ? " · umbral provisional" : ""}
      </span>
    </div>
  );
}

function IndicatorCard({
  ind,
  subjectId,
  missionClock,
}: {
  ind: IndicatorView;
  subjectId: string;
  missionClock: string;
}) {
  const counted = useCountUp(ind.value);
  return (
    <article className="card">
      <div className="indicator-title">
        <span className="dot" data-band={ind.band} />
        <span>{ind.label}</span>
        {ind.origin === "synthetic" && <span className="pill synthetic">sintético</span>}
        {ind.provisional && (
          <span className="pill provisional" title={`Tarjeta de evidencia: ${ind.evidenceCardId}`}>
            umbral provisional
          </span>
        )}
      </div>

      <div className="indicator-value">
        {ind.value === null ? (
          <span style={{ fontSize: 20, color: "var(--dim)" }}>sin medición</span>
        ) : (
          <>
            {fmt(counted)}
            {ind.unit && <small>{ind.unit}</small>}
          </>
        )}
      </div>

      <div className="indicator-meta">
        <span>{ind.latestLabel}</span>
        {ind.recordedAtDisplay && <span>{ind.recordedAtDisplay}</span>}
        {ind.baseline !== null && <span>base {fmt(ind.baseline)}</span>}
        {ind.delta !== null && (
          <span style={{ color: ind.baselineShifted ? "var(--amber)" : "var(--text-2)" }}>
            {ind.delta > 0 ? "+" : ""}
            {fmt(ind.delta)} ({fmt(ind.deltaPct, 0)} %)
          </span>
        )}
        {ind.refMin !== null || ind.refMax !== null ? (
          <span>
            rango {fmt(ind.refMin)}–{fmt(ind.refMax)}{" "}
            {ind.refSource === "dataset_file" ? "(archivo)" : "(demo)"}
          </span>
        ) : (
          <span>sin rango en el archivo</span>
        )}
        {ind.missingCount > 0 && <span>{ind.missingCount} faltantes</span>}
      </div>

      <Sparkline series={ind.series} band={ind.band} />

      <p className="indicator-reason">{ind.bandReason}</p>

      {ind.flags.length > 0 && (
        <div className="flags">
          {ind.flags.map((flag) => (
            <span className="pill" key={flag}>
              {flag}
            </span>
          ))}
        </div>
      )}

      {ind.hazards.length > 0 && (
        <div className="hazards">
          <span className="k">Riesgo de referencia</span>
          {ind.hazards.map((h) => (
            <a key={h.id} href={h.url} target="_blank" rel="noreferrer" title={h.source}>
              {h.id} · {h.title}
            </a>
          ))}
        </div>
      )}

      <Comments
        subjectId={subjectId}
        targetId={`${ind.variable}@${ind.latestLabel}`}
        missionClock={missionClock}
      />
    </article>
  );
}

function ZoneDetail({
  zone,
  subjectId,
  missionClock,
}: {
  zone: ZoneView;
  subjectId: string;
  missionClock: string;
}) {
  if (zone.state === "measured") {
    return (
      <>
        {zone.indicators.map((ind) => (
          <IndicatorCard key={ind.variable} ind={ind} subjectId={subjectId} missionClock={missionClock} />
        ))}
      </>
    );
  }
  return (
    <article className="card">
      <div className="indicator-title">
        <span className="dot" data-band="no_data" />
        <span>{zone.label}</span>
        <span className="pill">
          {zone.state === "measurement_site" ? "sitio de medición" : "sin medición"}
        </span>
      </div>
      <p className="teaching" style={{ marginTop: 10 }}>
        {zone.teaching}
      </p>
      {zone.note && <p className="teaching-note">{zone.note}</p>}
      {zone.state === "no_data" && (
        <p className="teaching-note" style={{ marginTop: 8 }}>
          Esta zona no muestra valores a propósito. Un número inventado sería peor que un hueco
          visible.
        </p>
      )}
    </article>
  );
}

function RealPanel({ data }: { data: DashboardData }) {
  const r = data.real;
  return (
    <>
      <div className="panel-head">
        <h2>Datos reales de NASA</h2>
        <span className="pill real">{r.datasetId}</span>
        <span className="chip">{r.license}</span>
      </div>
      <p className="panel-sub">{r.title}</p>

      <article className="card">
        <p className="teaching">{r.note}</p>
        <p className="provenance" style={{ marginTop: 10 }}>
          <b>fuente</b> {r.sourceUrl}
          <br />
          <b>sha256</b> {r.sha256 ?? "—"}
          <br />
          <b>obtenido</b> {r.retrievedAt ?? "—"} · <b>sujeto</b> {r.subjectId}
          <br />
          <b>tiempos</b> {r.timepoints.join(" → ")}
        </p>
        <div className="flags" style={{ marginTop: 12 }}>
          {r.pending > 0 && <span className="pill provisional">{r.pending} valor sin rango en el archivo</span>}
          {r.mismatch && <span className="pill provisional">R+194 fuera de la narrativa</span>}
          <span className="pill">N/A, NA y vacío → faltante</span>
        </div>
      </article>

      <h3 className="section">Panel metabólico · siete muestras por analito</h3>
      <div className="card" style={{ padding: 0 }}>
        <table className="real">
          <thead>
            <tr>
              <th>Analito</th>
              <th>Serie</th>
              <th>Rango del archivo</th>
              <th>Fuera</th>
            </tr>
          </thead>
          <tbody>
            {r.analytes.map((a) => (
              <tr key={a.variable}>
                <td>
                  {a.variable.replace(/_/g, " ")}
                  {a.unit && <span style={{ color: "var(--text-2)", fontSize: 12 }}> {a.unit}</span>}
                </td>
                <td style={{ width: 130 }}>
                  <Sparkline series={a.series} band={a.outOfRange > 0 ? "amber" : "green"} height={26} />
                </td>
                <td className="num">
                  {a.refMin === null && a.refMax === null ? "—" : `${fmt(a.refMin)}–${fmt(a.refMax)}`}
                </td>
                <td className="num">
                  {a.outOfRange > 0 ? (
                    <span className="bad">{a.outOfRange}</span>
                  ) : (
                    <span style={{ color: "var(--text-2)" }}>0</span>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <p className="teaching-note">Las series se dibujan con los huecos reales del archivo. Nada se interpola.</p>
    </>
  );
}

/* ------------------------------------------------------------------- shell */

export default function Dashboard({
  data,
  initialTab = "mission",
  initialQuestion = null,
  clock = 180,
  autoCase = false,
}: {
  data: DashboardData;
  initialTab?: "mission" | "real" | "ask";
  initialQuestion?: string | null;
  clock?: number;
  autoCase?: boolean;
}) {
  const [tab, setTab] = useState<"mission" | "real" | "ask">(initialTab);
  const zones = data.hero.zones;

  const allIndicators = zones.flatMap((z) => z.indicators);
  const worst = [...allIndicators]
    .filter((i) => i.band !== "no_data")
    .sort((a, b) => BAND_ORDER[a.band] - BAND_ORDER[b.band])[0];

  const zoneOf = (variable: string): ZoneView =>
    zones.find((z) => z.indicators.some((i) => i.variable === variable)) ?? zones[0];

  const [selected, setSelected] = useState<string | null>(worst?.variable ?? null);
  const [zoneId, setZoneId] = useState<string>(worst ? zoneOf(worst.variable).id : "thorax");

  function choose(variable: string) {
    setSelected(variable);
    setZoneId(zoneOf(variable).id);
  }

  const zone = zones.find((z) => z.id === zoneId) ?? zones[0];
  const indicator = selected ? allIndicators.find((i) => i.variable === selected) ?? null : null;

  const rad = data.hero.radiation;
  const radMax = rad.max ?? 600;
  const radPct = rad.value === null ? 0 : Math.min(100, (rad.value / radMax) * 100);
  const flagged = allIndicators.filter((i) => i.band === "amber" || i.band === "red");
  const missingTotal = data.quality.find((q) => q.id === "sleep_missing")?.value ?? "0";

  return (
    <div className="shell">
      <header className="top">
        <div className="brand">PULSE·0G</div>
        <span className="chip">
          {data.hero.subjectLabel} · {data.hero.scenarioId}
        </span>
        <span className="spacer" />
        <nav className="clock" aria-label="Momento de la misión">
          <span className="clock-label">momento</span>
          {STEPS.map((step) => (
            <a
              key={step.at}
              href={`/?tab=mission&at=${step.at}`}
              className="clock-step"
              aria-current={clock === step.at ? "true" : undefined}
            >
              <b>{clockLabel(step.at)}</b>
              <i>{step.label}</i>
            </a>
          ))}
        </nav>
        <div className="radiation" title={`Límite de carrera usado: ${radMax} ${rad.unit}`}>
          <span>dosis</span>
          <b>
            {rad.value === null ? "—" : fmt(rad.value, 0)}/{radMax} {rad.unit}
          </b>
          <span className="bar">
            <i data-band={rad.band} style={{ width: `${radPct}%` }} />
          </span>
        </div>
      </header>

      <nav className="tabs" role="tablist">
        <button role="tab" aria-selected={tab === "mission"} onClick={() => setTab("mission")}>
          Misión
        </button>
        <button role="tab" aria-selected={tab === "real"} onClick={() => setTab("real")}>
          Datos reales NASA
        </button>
        <button role="tab" aria-selected={tab === "ask"} onClick={() => setTab("ask")}>
          Consultar
        </button>
      </nav>

      {tab === "mission" ? (
        <main>
          <section className="map">
            <h2>Estado por zona</h2>
            <BodyMap
              key={data.hero.clockLabel}
              zones={zones}
              selected={zone.id}
              onSelect={(id) => {
                setZoneId(id);
                setSelected(null);
              }}
            />
            <div className="legend">
              <div>
                <i style={{ background: "var(--text)", borderColor: "var(--text)" }} /> en rango
              </div>
              <div>
                <i
                  style={{
                    background: "var(--amber)",
                    borderColor: "var(--amber)",
                    transform: "rotate(45deg)",
                  }}
                />{" "}
                atención
              </div>
              <div>
                <i style={{ background: "var(--red)", borderColor: "var(--red)" }} /> acción
              </div>
              <div>
                <i style={{ borderStyle: "dashed", borderColor: "var(--dim)" }} /> sin medición
              </div>
            </div>
            <p className="microcopy">
              Indicadores medidos por zona. No es un diagnóstico por órgano. El escenario es
              sintético; los datos reales viven en su propia pestaña.
            </p>
          </section>

          <aside className="panel">
            <p className="panel-title">
              Indicadores · {data.hero.clockLabel}
              {indicator?.recordedAt ? ` · ${dateOf(indicator)}` : ""}
            </p>

            <table className="indicators">
              <thead>
                <tr>
                  <th>Indicador</th>
                  <th className="n">Valor</th>
                  <th className="n">Base</th>
                  <th className="n">Δ</th>
                  <th>Banda</th>
                </tr>
              </thead>
              <tbody>
                {allIndicators.map((ind) => (
                  <tr
                    key={ind.variable}
                    tabIndex={0}
                    aria-selected={selected === ind.variable}
                    onClick={() => choose(ind.variable)}
                    onKeyDown={(e) => {
                      if (e.key === "Enter" || e.key === " ") {
                        e.preventDefault();
                        choose(ind.variable);
                      }
                    }}
                  >
                    <td>
                      {ind.label}
                      <span className="why">{rowDetail(ind)}</span>
                    </td>
                    <td className="n">{ind.display}</td>
                    <td className="n">{ind.baseline === null ? "—" : fmt(ind.baseline)}</td>
                    <td className="n">
                      {ind.deltaPct === null
                        ? "—"
                        : `${ind.deltaPct > 0 ? "+" : ""}${fmt(ind.deltaPct, 0)} %`}
                    </td>
                    <td>
                      <span className="band" data-band={ind.band}>
                        {bandLabel(ind.band)}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>

            <ActionBar indicator={indicator} zone={zone} />

            <ZoneDetail
              key={`${zone.id}-${selected ?? "zone"}`}
              zone={indicator ? zoneOf(indicator.variable) : zone}
              subjectId={data.hero.subjectId}
              missionClock={data.hero.clockLabel}
            />

            <Quality items={data.quality} />

            <CasePackage
              clock={clock}
              autoOpen={autoCase}
              onOpenComments={() => {
                const first = document.querySelector<HTMLButtonElement>("[data-comments-toggle]");
                if (first && first.getAttribute("aria-expanded") !== "true") first.click();
                first?.scrollIntoView({ block: "center", behavior: "smooth" });
              }}
            />
          </aside>
        </main>
      ) : tab === "real" ? (
        <main>
          <section className="map">
            <h2>Procedencia</h2>
            <p className="microcopy" style={{ marginTop: 0 }}>
              Los datos reales viven en una pestaña aparte y nunca comparten eje con el escenario
              sintético.
            </p>
          </section>
          <aside className="panel">
            <RealPanel data={data} />
          </aside>
        </main>
      ) : (
        <main>
          <section className="map">
            <h2>Consultar</h2>
            <p className="microcopy" style={{ marginTop: 0 }}>
              Cada frase de la respuesta se apoya en un dato o en una tarjeta. La que no puede, se
              tacha.
            </p>
          </section>
          <aside className="panel">
            <AskPanel initialQuestion={initialQuestion} clock={clock} />
          </aside>
        </main>
      )}

      <footer className="console">
        <span>
          <i className="sq" /> <b>{flagged.length}</b> indicadores fuera de banda ·{" "}
          <b>{missingTotal}</b> datos faltantes
        </span>
        <span className="spacer" />
        <span style={{ color: "var(--text-2)", fontSize: 14, fontFamily: "var(--mono)" }}>
          {data.hero.originType === "synthetic" ? "escenario sintético" : data.hero.originType} ·{" "}
          {data.hero.scenarioId}
        </span>
      </footer>
    </div>
  );
}
