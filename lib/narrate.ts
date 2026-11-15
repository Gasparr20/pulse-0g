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

const INSTRUCTIONS = `Sos un asistente de salud de misión. Recibís hechos ya verificados sobre un tripulante y la pregunta que hizo. Escribí tres oraciones en castellano rioplatense que expliquen qué significan esos hechos para esa persona, como se lo explicarías a alguien sin formación médica.

Reglas estrictas:
- Usá solamente los hechos del bloque DATOS. No agregues nada que no esté ahí.
- No agregues ningún número que no aparezca en DATOS.
- No diagnostiques, no nombres enfermedades y no inventes causas.
- No expliques el por qué ni el para qué: prohibido "esto indica", "esto significa", "esto sugiere", "debido a", "por eso".
- Describí solo lo que los datos dicen, con palabras simples. Nada de adjetivos sobre el estado de la persona.
- Si los datos no alcanzan para responder la pregunta, decí exactamente qué falta.
- Devolvé solamente las tres oraciones, sin títulos, sin listas y sin comillas.`;

// The model must not slide into diagnosis. A number check does not catch that.
const FORBIDDEN = /\b(diagn[oó]stic|padec|enfermedad|infecci[oó]n|ten[eé]s|sufr[ií]s|deshidratad)/i;
// Causal claims are the second way a model slips past a number check.
const CAUSAL = /\b(esto indica|esto significa|esto sugiere|debido a|por eso|a causa de|lo que indica|lo que muestra)/i;

export async function narrate(sentences: string[], question = ""): Promise<NarrateResult> {
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
        prompt: `${INSTRUCTIONS}\n\nPREGUNTA:\n${question || "(sin pregunta)"}\n\nDATOS:\n${source}\n\nEXPLICACIÓN:`,
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

  if (CAUSAL.test(raw)) {
    return {
      ok: false,
      text: raw,
      model: MODEL,
      reason: "la IA agregó una interpretación causal que los datos no sostienen",
    };
  }

  if (FORBIDDEN.test(raw)) {
    return {
      ok: false,
      text: raw,
      model: MODEL,
      reason: "la IA se puso a diagnosticar, y este sistema no diagnostica",
    };
  }

  // The check that matters: the explanation may not introduce a number the source
  // did not carry. Everything else the model does is phrasing, and phrasing is free.
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
