"use client";

import { useCallback, useEffect, useState } from "react";
import { SUGGESTED } from "@/lib/questions";
import type { Answer } from "@/lib/types";

function AnchorChip({ anchor }: { anchor: Answer["sentences"][number]["anchors"][number] }) {
  const tone = anchor.kind === "card" ? "provisional" : "real";
  return (
    <span className={`pill ${tone}`} title={anchor.ref}>
      {anchor.kind === "card" ? "tarjeta" : "dato"} · {anchor.label}
    </span>
  );
}

interface ProbeCase {
  text: string;
  why: string;
  expected: string;
  actual: string;
  pass: boolean;
  reason: string | null;
}

/** The verifier almost never rejects anything in normal use, because the templates
 *  are written to anchor. That makes the most interesting behaviour in the product
 *  invisible, so the probe cases that prove it can reject are shown on demand. */
function VerifierProbe() {
  const [cases, setCases] = useState<ProbeCase[] | null>(null);
  const [open, setOpen] = useState(false);

  const load = useCallback(async () => {
    setOpen(true);
    const res = await fetch("/api/verify-probe");
    setCases((await res.json()).results);
  }, []);

  // ?probe=1 opens it, so a demo or a recording can land straight on the proof.
  useEffect(() => {
    if (new URLSearchParams(window.location.search).get("probe") === "1") void load();
  }, [load]);

  return (
    <div style={{ marginTop: 18, borderTop: "2px solid var(--hair)", paddingTop: 12 }}>
      <button
        onClick={() => (open ? setOpen(false) : load())}
        className="ghost"
        aria-expanded={open}
      >
        {open ? "▾" : "▸"} Autoprueba del verificador
      </button>

      {open && (
        <div style={{ marginTop: 12, display: "grid", gap: 10 }}>
          <p className="teaching-note">
            Frases de control que el verificador tiene que aceptar o rechazar. Si alguna
            falla, el sistema está mintiendo sobre su propia fiabilidad.
          </p>
          {!cases && <p className="teaching-note">Cargando…</p>}
          {cases?.map((c) => (
            <div key={c.text} style={{ display: "grid", gap: 4 }}>
              <p
                className={c.actual === "tachada" ? "teaching claim-struck" : "teaching"}
                style={{
                  margin: 0,
                  fontSize: 15,
                  color: c.actual === "tachada" ? "var(--dim)" : "var(--text)",
                }}
              >
                {c.text}
              </p>
              <div className="flags" style={{ marginTop: 2 }}>
                <span className="pill">{c.actual}</span>
                <span className="pill" style={{ color: c.pass ? "var(--text)" : "var(--red)" }}>
                  {c.pass ? "correcto" : "FALLA"}
                </span>
                <span className="pill">{c.why}</span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export default function AskPanel({
  initialQuestion = null,
  clock = 180,
}: {
  initialQuestion?: string | null;
  clock?: number;
}) {
  const [question, setQuestion] = useState(initialQuestion ?? "");
  const [result, setResult] = useState<Answer | null>(null);
  const [busy, setBusy] = useState(false);

  async function ask(q: string) {
    setBusy(true);
    setQuestion(q);
    try {
      const res = await fetch("/api/ask", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ q, at: clock }),
      });
      setResult(await res.json());
    } finally {
      setBusy(false);
    }
  }

  // A question can be deep-linked so a demo can jump straight to a prepared answer.
  useEffect(() => {
    if (initialQuestion) void ask(initialQuestion);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [initialQuestion]);

  const struck = result?.sentences.filter((s) => s.struck).length ?? 0;

  return (
    <>
      <div className="panel-head">
        <h2>Consulta</h2>
        <span className="chip">plantillas determinísticas</span>
      </div>
      <p className="panel-sub">
        8 consultas fijas sobre los datos cargados, más una abstención explícita. No
        hay traducción libre a SQL ni ejecución de código: lo que no está cubierto
        se rechaza.
      </p>

      <div className="flags" style={{ marginBottom: 14 }}>
        {SUGGESTED.map((q) => (
          <button
            key={q}
            className="pill"
            style={{ cursor: "pointer", background: "transparent", fontFamily: "inherit" }}
            onClick={() => ask(q)}
          >
            {q}
          </button>
        ))}
      </div>

      <form
        onSubmit={(e) => {
          e.preventDefault();
          if (question.trim()) ask(question.trim());
        }}
        style={{ display: "flex", gap: 8, marginBottom: 16 }}
      >
        <input
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          placeholder="Escribí una pregunta…"
          style={{
            flex: 1,
            background: "var(--surface)",
            border: "1px solid var(--hair)",
            borderRadius: 6,
            color: "var(--text)",
            padding: "9px 12px",
            font: "inherit",
          }}
        />
        <button
          type="submit"
          disabled={busy}
          style={{
            background: "var(--surface-2)",
            border: "1px solid var(--hair)",
            borderRadius: 6,
            color: "var(--text)",
            padding: "9px 16px",
            font: "inherit",
            cursor: busy ? "wait" : "pointer",
          }}
        >
          {busy ? "…" : "Preguntar"}
        </button>
      </form>

      {!result && (
        <article className="card">
          <p className="teaching-note">
            Elegí una de las preguntas de arriba para ver cómo responde el sistema.
          </p>
        </article>
      )}

      {result && (
        <article className="card" data-refused={result.refused}>
          <div className="indicator-title">
            <span
              className="dot"
              data-band={result.refused ? "amber" : "green"}
            />
            <span>{result.title}</span>
            <span className="pill">{result.intent}</span>
          </div>

          <div style={{ marginTop: 12, display: "grid", gap: 10 }}>
            {result.sentences.map((s, i) => (
              <div key={i}>
                <p
                  className={s.struck ? "teaching claim-struck" : "teaching"}
                  style={{
                    margin: 0,
                    color: s.struck ? "var(--dim)" : "var(--text)",
                  }}
                >
                  {s.text}
                </p>
                <div className="flags" style={{ marginTop: 5 }}>
                  {s.struck ? (
                    <span className="pill provisional answer-chip">{s.struckReason}</span>
                  ) : (
                    s.anchors.map((a) => (
                      <span className="answer-chip" key={a.ref}>
                        <AnchorChip anchor={a} />
                      </span>
                    ))
                  )}
                </div>
              </div>
            ))}
          </div>

          {result.note && (
            <p className="teaching-note" style={{ marginTop: 14 }}>
              {result.note}
            </p>
          )}

          <div className="flags" style={{ marginTop: 12 }}>
            <span className="pill">
              {struck === 0
                ? "verificador: todas las frases respaldadas"
                : `verificador: ${struck} frases tachadas`}
            </span>
            {result.cards.length === 0 && (
              <span className="pill">sin tarjetas de evidencia cargadas</span>
            )}
          </div>

          <VerifierProbe />
        </article>
      )}
    </>
  );
}
