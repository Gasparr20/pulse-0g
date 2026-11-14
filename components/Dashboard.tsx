"use client";

import { useState } from "react";
import BodyMap, { bandText } from "./BodyMap";
import Sparkline from "./Sparkline";
import AskPanel from "./AskPanel";
import { BAND_ORDER } from "@/lib/bands";
import Comments from "./Comments";
import CasePackage from "./CasePackage";
import type {
  Dashboard as DashboardData,
  IndicatorView,
  ZoneView,
} from "@/lib/types";

function fmt(n: number | null, digits = 1): string {
  if (n === null) return "—";
  return String(Math.round(n * 10 ** digits) / 10 ** digits);
}

function clockLabel(clock: number): string {
  if (clock >= 1_000_000) return `R+${clock - 1_000_000}`;
  if (clock < 0) return `L-${Math.abs(clock)}`;
  return `FD${clock}`;
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
          <span style={{ fontSize: 17, color: "var(--nodata)" }}>sin medición</span>
        ) : (
          <>
            {fmt(ind.value)}
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
            {fmt(ind.delta)} ({ind.deltaPct! > 0 ? "+" : ""}
            {fmt(ind.deltaPct, 0)}%)
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

      {ind.action && (
        <div className="action" data-band={ind.band}>
          {ind.action}
        </div>
      )}

      {ind.flags.length > 0 && (
        <div className="flags">
          {ind.flags.map((f) => (
            <span className="pill" key={f}>
              {f}
            </span>
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

function ZonePanel({
  zone,
  zones,
  subjectId,
  missionClock,
}: {
  zone: ZoneView;
  zones: ZoneView[];
  subjectId: string;
  missionClock: string;
}) {
  if (zone.state === "measured") {
    return (
      <>
        <div className="panel-head">
          <h2>{zone.label}</h2>
          <span className="dot" data-band={zone.band} />
          <span className="chip">{bandText(zone.band)}</span>
        </div>
        <p className="panel-sub">{zone.sublabel}</p>
        {zone.indicators.map((ind) => (
          <IndicatorCard
            key={ind.variable}
            ind={ind}
            subjectId={subjectId}
            missionClock={missionClock}
          />
        ))}
      </>
    );
  }

  const systolic = zones
    .find((z) => z.id === "thorax")
    ?.indicators.find((i) => i.variable === "systolic");

  return (
    <>
      <div className="panel-head">
        <h2>{zone.label}</h2>
        {zone.state === "measurement_site" ? (
          <span className="chip" style={{ color: "#cbd5e1", borderColor: "#cbd5e1" }}>
            sitio de medición
          </span>
        ) : (
          <span className="chip">sin medición</span>
        )}
      </div>
      <p className="panel-sub">{zone.sublabel}</p>
      <article className="card">
        <p className="teaching">{zone.teaching}</p>
        {zone.note && <p className="teaching-note">{zone.note}</p>}
      </article>
      {zone.state === "measurement_site" && systolic && (
        <>
          <h3 className="section">Última toma registrada en esta zona</h3>
          <IndicatorCard ind={systolic} subjectId={subjectId} missionClock={missionClock} />
        </>
      )}
      {zone.state === "no_data" && (
        <article className="card">
          <p className="teaching-note">
            Esta zona no muestra valores a propósito. Un número inventado sería peor
            que un hueco visible.
          </p>
        </article>
      )}
    </>
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
          {r.pending > 0 && (
            <span className="pill provisional">
              {r.pending} valor sin rango en el archivo
            </span>
          )}
          {r.mismatch && <span className="pill provisional">R+194 fuera de la narrativa</span>}
          <span className="pill">N/A, NA y vacío → faltante</span>
        </div>
      </article>

      <h3 className="section">Panel metabólico, siete muestras por analito</h3>
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
                  {a.unit && (
                    <span style={{ color: "var(--text-2)", fontSize: 11 }}> {a.unit}</span>
                  )}
                </td>
                <td style={{ width: 120 }}>
                  <Sparkline
                    series={a.series}
                    band={a.outOfRange > 0 ? "amber" : "green"}
                    height={26}
                  />
                </td>
                <td className="num">
                  {a.refMin === null && a.refMax === null
                    ? "—"
                    : `${fmt(a.refMin)}–${fmt(a.refMax)}`}
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
      <p className="teaching-note">
        Las series se dibujan con los huecos reales del archivo. Nada se interpola.
      </p>
    </>
  );
}

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
  // Open on whatever needs attention, not on a fixed region: at FD180 that is the
  // head, at FD30 nothing is flagged and the thorax stays as a neutral default.
  const [selected, setSelected] = useState<string>(() => {
    const ranked = [...zones]
      .filter((z) => z.state === "measured")
      .sort((a, b) => BAND_ORDER[a.band] - BAND_ORDER[b.band]);
    if (!ranked[0] || ranked[0].band === "green" || ranked[0].band === "no_data") {
      return "thorax";
    }
    return ranked[0].id;
  });
  const zone = zones.find((z) => z.id === selected) ?? zones[0];
  const rad = data.hero.radiation;
  const radMax = rad.max ?? 600;
  const radPct = rad.value === null ? 0 : Math.min(100, (rad.value / radMax) * 100);

  return (
    <div className="shell">
      <header className="top">
        <div className="brand">
          CrewCheck<span>autoevaluación con evidencia</span>
        </div>
        <span className="chip synthetic">escenario sintético</span>
        <span className="chip">
          {data.hero.subjectLabel} · {data.hero.scenarioId}
        </span>
        <span className="spacer" />
        <div className="radiation" title={`Límite de carrera usado: ${radMax} ${rad.unit}`}>
          <span style={{ color: "var(--text-2)" }}>{rad.label}</span>
          <b>
            {rad.value === null ? "—" : fmt(rad.value, 0)} / {radMax} {rad.unit}
          </b>
          <span className="bar">
            <i data-band={rad.band} style={{ width: `${radPct}%` }} />
          </span>
          {rad.provisional && <span className="pill provisional">provisional</span>}
        </div>
      </header>

      <nav className="tabs" role="tablist">
        <button
          role="tab"
          aria-selected={tab === "mission"}
          onClick={() => setTab("mission")}
        >
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
            <div className="clock">
              <span className="clock-label">reloj de misión</span>
              {[
                { at: 0, label: "FD0" },
                { at: 30, label: "FD30" },
                { at: 90, label: "FD90" },
                { at: 120, label: "FD120" },
                { at: 180, label: "FD180" },
                { at: 1000029, label: "R+29" },
              ].map((step) => (
                <a
                  key={step.at}
                  href={`/?tab=mission&at=${step.at}`}
                  className="clock-step"
                  aria-current={clock === step.at ? "true" : undefined}
                >
                  {step.label}
                </a>
              ))}
            </div>
            <BodyMap zones={zones} selected={selected} onSelect={setSelected} />
            <p className="microcopy">
              Este mapa muestra indicadores medidos por zona. No es un diagnóstico
              por órgano.
            </p>
            <div className="legend">
              <div>
                <i style={{ background: "var(--green)" }} /> en rango
              </div>
              <div>
                <i style={{ background: "var(--amber)" }} /> requiere atención
              </div>
              <div>
                <i style={{ background: "var(--red)" }} /> requiere acción
              </div>
              <div>
                <i style={{ background: "var(--nodata)", border: "1px dashed var(--hair)" }} />
                sin medición / sin umbral
              </div>
              <div>
                <i style={{ background: "#cbd5e1" }} /> sitio de medición
              </div>
            </div>
          </section>
          <aside className="panel">
            <ZonePanel
              zone={zone}
              zones={zones}
              subjectId={data.hero.subjectId}
              missionClock={clockLabel(clock)}
            />
            <CasePackage
              clock={clock}
              autoOpen={autoCase}
              onOpenComments={() => {
                const first = document.querySelector<HTMLButtonElement>(
                  "[data-comments-toggle]",
                );
                if (first && first.getAttribute("aria-expanded") !== "true") first.click();
                first?.scrollIntoView({ block: "center", behavior: "smooth" });
              }}
            />
          </aside>
        </main>
      ) : tab === "real" ? (
        <main>
          <section className="map">
            <p className="microcopy" style={{ marginTop: 24 }}>
              Los datos reales viven en una pestaña aparte y nunca comparten eje con
              el escenario sintético.
            </p>
          </section>
          <aside className="panel">
            <RealPanel data={data} />
          </aside>
        </main>
      ) : (
        <main>
          <section className="map">
            <p className="microcopy" style={{ marginTop: 24 }}>
              Cada frase de la respuesta tiene que apoyarse en un dato o en una
              tarjeta. La que no puede, se tacha.
            </p>
          </section>
          <aside className="panel">
            <AskPanel initialQuestion={initialQuestion} clock={clock} />
          </aside>
        </main>
      )}
    </div>
  );
}
