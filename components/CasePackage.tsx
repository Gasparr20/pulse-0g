"use client";

import { useEffect, useState } from "react";
import type { CasePackage as Package } from "@/lib/case";

/** The escalation path: produce a case file for the flight surgeon.
 *  Nothing is transmitted, and nothing else in the app depends on this. */
export default function CasePackage({
  clock,
  onOpenComments,
  autoOpen = false,
}: {
  clock: number;
  onOpenComments: () => void;
  autoOpen?: boolean;
}) {
  const [pkg, setPkg] = useState<Package | null>(null);
  const [busy, setBusy] = useState(false);

  async function generate() {
    setBusy(true);
    try {
      const res = await fetch(`/api/case?at=${clock}`);
      setPkg(await res.json());
    } finally {
      setBusy(false);
    }
  }

  // Deep link so a demo (or a recording) can land straight on a generated package.
  useEffect(() => {
    if (autoOpen) void generate();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [autoOpen]);

  function download() {
    if (!pkg) return;
    const blob = new Blob([JSON.stringify(pkg, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `crewcheck-case-${pkg.packageId}.json`;
    a.click();
    URL.revokeObjectURL(url);
  }

  const flagged = pkg?.indicators.filter((i) => i.band === "amber" || i.band === "red") ?? [];

  return (
    <article className="card" style={{ marginTop: 18 }}>
      <div className="indicator-title">
        <span className="dot" data-band={pkg ? (flagged.length ? "amber" : "green") : "no_data"} />
        <span>Paquete de caso</span>
        <span className="pill">escalamiento</span>
      </div>
      <p className="teaching-note" style={{ marginTop: 8 }}>
        Arma un archivo con lo medido, las bandas, la calidad de los datos y la
        bitácora, para que el flight surgeon lo lea en Tierra. No envía nada y el
        resto del sistema funciona sin esto.
      </p>

      {!pkg && (
        <button
          onClick={generate}
          disabled={busy}
          style={{
            marginTop: 10,
            background: "var(--surface-2)",
            border: "1px solid var(--hair)",
            borderRadius: 6,
            color: "var(--text)",
            padding: "8px 14px",
            font: "inherit",
            fontSize: 13,
            cursor: busy ? "wait" : "pointer",
          }}
        >
          {busy ? "Generando…" : "Generar paquete"}
        </button>
      )}

      {pkg && (
        <>
          <div className="flags" style={{ marginTop: 10 }}>
            <span className="pill real">id {pkg.packageId}</span>
            <span className="pill">{pkg.missionClock}</span>
            <span className="pill">
              {flagged.length} indicador(es) fuera de banda
            </span>
            <span className="pill">{pkg.comments.length} nota(s)</span>
          </div>

          <pre
            style={{
              marginTop: 12,
              padding: "10px 12px",
              background: "#0d131b",
              border: "1px solid var(--hair)",
              borderRadius: 6,
              fontFamily: "var(--mono)",
              fontSize: 11,
              lineHeight: 1.55,
              maxHeight: 260,
              overflow: "auto",
              whiteSpace: "pre-wrap",
              color: "var(--text-2)",
            }}
          >
            {pkg.report}
          </pre>

          <div style={{ display: "flex", gap: 8, marginTop: 10 }}>
            <button
              onClick={download}
              style={{
                background: "var(--surface-2)",
                border: "1px solid var(--hair)",
                borderRadius: 6,
                color: "var(--text)",
                padding: "7px 12px",
                font: "inherit",
                fontSize: 12,
                cursor: "pointer",
              }}
            >
              Descargar JSON
            </button>
            <button
              onClick={onOpenComments}
              style={{
                background: "none",
                border: "1px solid var(--hair)",
                borderRadius: 6,
                color: "var(--text-2)",
                padding: "7px 12px",
                font: "inherit",
                fontSize: 12,
                cursor: "pointer",
              }}
            >
              Ver bitácora
            </button>
          </div>
        </>
      )}
    </article>
  );
}
