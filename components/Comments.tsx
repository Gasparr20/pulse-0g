"use client";

import { useCallback, useEffect, useState } from "react";

interface Note {
  id: number;
  author_role: string;
  body: string;
  created_at: string;
  mission_clock: string;
}

/** Append-only thread. There is no edit and no delete, here or in the API:
 *  a correction is a new note that points at the previous one. */
export default function Comments({
  subjectId,
  targetId,
  missionClock,
}: {
  subjectId: string;
  targetId: string;
  missionClock: string;
}) {
  const [open, setOpen] = useState(false);
  const [notes, setNotes] = useState<Note[]>([]);
  const [body, setBody] = useState("");
  const [role, setRole] = useState<"crew" | "surgeon">("crew");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    const res = await fetch(
      `/api/comments?subject=${encodeURIComponent(subjectId)}&target=${encodeURIComponent(targetId)}`,
    );
    if (res.ok) setNotes((await res.json()).comments);
  }, [subjectId, targetId]);

  useEffect(() => {
    if (open) void load();
  }, [open, load]);

  async function save() {
    if (!body.trim()) return;
    setBusy(true);
    setError(null);
    try {
      const res = await fetch("/api/comments", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({
          subjectId,
          targetType: "indicator",
          targetId,
          authorRole: role,
          body,
          missionClock,
        }),
      });
      const payload = await res.json();
      if (!res.ok) throw new Error(payload.error ?? "no se pudo guardar");
      setBody("");
      await load();
    } catch (e) {
      setError(e instanceof Error ? e.message : "error");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div style={{ marginTop: 10, borderTop: "1px solid var(--hair)", paddingTop: 10 }}>
      <button
        data-comments-toggle
        onClick={() => setOpen((v) => !v)}
        style={{
          background: "none",
          border: "none",
          color: "var(--text-2)",
          font: "inherit",
          fontSize: 12,
          cursor: "pointer",
          padding: 0,
        }}
      >
        {open ? "▾" : "▸"} Bitácora {notes.length > 0 ? `(${notes.length})` : ""}
      </button>

      {open && (
        <div style={{ marginTop: 10, display: "grid", gap: 8 }}>
          {notes.length === 0 && (
            <p className="teaching-note">
              Sin notas. Las notas son contexto para quien lea este dato después; no
              son evidencia clínica y no alimentan las respuestas del sistema.
            </p>
          )}
          {notes.map((n) => (
            <div key={n.id} className="card" style={{ padding: "8px 10px", margin: 0 }}>
              <div className="indicator-meta" style={{ marginTop: 0 }}>
                <span>{n.mission_clock}</span>
                <span>{n.author_role === "crew" ? "tripulación" : "flight surgeon"}</span>
                <span>{n.created_at.slice(0, 16).replace("T", " ")}</span>
              </div>
              <p style={{ margin: "6px 0 0", fontSize: 13 }}>{n.body}</p>
            </div>
          ))}

          <div style={{ display: "flex", gap: 6, alignItems: "flex-start" }}>
            <select
              value={role}
              onChange={(e) => setRole(e.target.value as "crew" | "surgeon")}
              style={{
                background: "var(--surface)",
                border: "1px solid var(--hair)",
                borderRadius: 6,
                color: "var(--text)",
                padding: "7px 8px",
                font: "inherit",
                fontSize: 12,
              }}
            >
              <option value="crew">tripulación</option>
              <option value="surgeon">surgeon</option>
            </select>
            <input
              value={body}
              onChange={(e) => setBody(e.target.value)}
              placeholder="Agregar una nota al registro…"
              style={{
                flex: 1,
                background: "var(--surface)",
                border: "1px solid var(--hair)",
                borderRadius: 6,
                color: "var(--text)",
                padding: "7px 10px",
                font: "inherit",
                fontSize: 13,
              }}
            />
            <button
              onClick={save}
              disabled={busy}
              style={{
                background: "var(--surface-2)",
                border: "1px solid var(--hair)",
                borderRadius: 6,
                color: "var(--text)",
                padding: "7px 12px",
                font: "inherit",
                fontSize: 12,
                cursor: busy ? "wait" : "pointer",
              }}
            >
              {busy ? "…" : "Guardar"}
            </button>
          </div>
          {error && <p className="teaching-note" style={{ color: "var(--red)" }}>{error}</p>}
        </div>
      )}
    </div>
  );
}
