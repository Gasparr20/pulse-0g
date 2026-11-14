"use client";

import { useEffect, useState } from "react";
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
                  className="teaching"
                  style={{
                    margin: 0,
                    textDecoration: s.struck ? "line-through" : "none",
                    color: s.struck ? "var(--red)" : "var(--text)",
                  }}
                >
                  {s.text}
                </p>
                <div className="flags" style={{ marginTop: 5 }}>
                  {s.struck ? (
                    <span className="pill provisional">{s.struckReason}</span>
                  ) : (
                    s.anchors.map((a) => <AnchorChip key={a.ref} anchor={a} />)
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
        </article>
      )}
    </>
  );
}
