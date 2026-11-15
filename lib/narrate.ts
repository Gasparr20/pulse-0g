/** Local model narrator.
 *
 *  The model never produces a number: it rewrites sentences that a deterministic
 *  engine already built and anchored. Its output is then checked against the same
 *  numbers the input carried, because a fluent paraphrase that invents a figure is
 *  exactly the failure this product exists to prevent.
 *
 *  Nothing here is on the critical path. If Ollama is slow, missing or wrong, the
 *  caller keeps the deterministic answer and says so. */

const BASE = process.env.OLLAMA_URL ?? "http://127.0.0.1:11434";
const MODEL = process.env.PULSE_MODEL ?? "qwen2.5-coder:7b";
const TIMEOUT_MS = 25_000;

export interface NarrateResult {
  ok: boolean;
  text: string | null;
  model: string;
  reason: string | null;
}

const NUMERIC = /\d+(?:[.,]\d+)?/g;

function numbers(text: string): Set<string> {
  return new Set(
    (text.match(NUMERIC) ?? []).map((t) => String(Number(t.replace(",", ".")))),
  );
}

export async function modelAvailable(): Promise<boolean> {
  try {
    const res = await fetch(`${BASE}/api/tags`, {
      signal: AbortSignal.timeout(2500),
      cache: "no-store",
    });
    if (!res.ok) return false;
    const data = (await res.json()) as { models?: Array<{ name: string }> };
    return (data.models ?? []).some((m) => m.name === MODEL);
  } catch {
    return false;
  }
}

const INSTRUCTIONS = `Sos un redactor. Recibís frases que ya están respaldadas por datos y las reescribís en castellano rioplatense claro y natural, en dos o tres oraciones.

Reglas estrictas:
- No agregues ningún número que no esté en el texto original.
- No agregues afirmaciones nuevas: no interpretes, no diagnostiques, no recomiendes.
- Mantené todos los números y las unidades exactamente como aparecen.
- Devolvé solamente el texto reescrito, sin comentarios, sin comillas y sin listas.`;

export async function narrate(sentences: string[]): Promise<NarrateResult> {
  const source = sentences.join(" ");
  if (!source.trim()) {
    return { ok: false, text: null, model: MODEL, reason: "no hay texto para reescribir" };
  }

  let raw: string;
  try {
    const res = await fetch(`${BASE}/api/generate`, {
      method: "POST",
      headers: { "content-type": "application/json" },
      signal: AbortSignal.timeout(TIMEOUT_MS),
      cache: "no-store",
      body: JSON.stringify({
        model: MODEL,
        stream: false,
        prompt: `${INSTRUCTIONS}\n\nTEXTO:\n${source}\n\nREESCRITURA:`,
        options: { num_predict: 220, temperature: 0.1 },
      }),
    });
    if (!res.ok) {
      return { ok: false, text: null, model: MODEL, reason: `el modelo respondió ${res.status}` };
    }
    const data = (await res.json()) as { response?: string };
    raw = (data.response ?? "").trim();
  } catch (error) {
    const timedOut = error instanceof Error && error.name === "TimeoutError";
    return {
      ok: false,
      text: null,
      model: MODEL,
      reason: timedOut ? "el modelo tardó demasiado" : "el modelo no está disponible",
    };
  }

  if (!raw) return { ok: false, text: null, model: MODEL, reason: "el modelo devolvió vacío" };
  if (/insuficiente/i.test(raw)) {
    return { ok: false, text: null, model: MODEL, reason: "el modelo no pudo reescribir" };
  }

  // The check that matters: a paraphrase may not introduce a number the source did
  // not carry. Everything else the model does is style, and style is allowed.
  const allowed = numbers(source);
  const invented = [...numbers(raw)].filter((n) => !allowed.has(n));
  if (invented.length > 0) {
    return {
      ok: false,
      text: raw,
      model: MODEL,
      reason: `la IA agregó cifras que no están en los datos: ${invented.join(", ")}`,
    };
  }

  return { ok: true, text: raw, model: MODEL, reason: null };
}

/** Loads the weights so the first real question is not eight seconds of cold start. */
export async function warmUp(): Promise<void> {
  try {
    await fetch(`${BASE}/api/generate`, {
      method: "POST",
      headers: { "content-type": "application/json" },
      signal: AbortSignal.timeout(60_000),
      body: JSON.stringify({
        model: MODEL,
        stream: false,
        prompt: "ok",
        options: { num_predict: 1 },
      }),
    });
  } catch {
    // A warm-up that fails is not an error: the real call will report it.
  }
}
