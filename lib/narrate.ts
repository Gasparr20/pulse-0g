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
const TIMEOUT_MS = 25_000;

/** Preference order, best prose first. The first one installed wins, so the app
 *  adapts to the machine instead of failing because a specific tag is missing. */
const PREFERRED = ["qwen2.5:7b", "qwen2.5:latest", "llama3.1:8b", "qwen2.5-coder:7b"];

let cached: { model: string | null; at: number } | null = null;
const CACHE_MS = 20_000;

async function pickModel(): Promise<string | null> {
  const forced = process.env.PULSE_MODEL;
  const now = Date.now();
  if (cached && now - cached.at < CACHE_MS && !forced) return cached.model;
  let names: string[] = [];
  try {
    const res = await fetch(`${BASE}/api/tags`, {
      signal: AbortSignal.timeout(2500),
      cache: "no-store",
    });
    if (!res.ok) return null;
    const data = (await res.json()) as { models?: Array<{ name: string }> };
    names = (data.models ?? []).map((m) => m.name);
  } catch {
    return null;
  }
  const model =
    (forced && names.includes(forced) ? forced : null) ??
    PREFERRED.find((p) => names.includes(p)) ??
    names[0] ??
    null;
  cached = { model, at: now };
  return model;
}

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

export async function modelAvailable(): Promise<{ available: boolean; model: string | null }> {
  const model = await pickModel();
  return { available: Boolean(model), model };
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

export async function narrate(
  sentences: string[],
  question = "",
  moment = "",
): Promise<NarrateResult> {
  const source = sentences.join(" ");
  const model = await pickModel();
  if (!model) {
    return { ok: false, text: null, model: "—", reason: "no hay un modelo local disponible" };
  }
  if (!source.trim()) {
    return { ok: false, text: null, model, reason: "no hay texto para explicar" };
  }

  let raw: string;
  try {
    const res = await fetch(`${BASE}/api/generate`, {
      method: "POST",
      headers: { "content-type": "application/json" },
      signal: AbortSignal.timeout(TIMEOUT_MS),
      cache: "no-store",
      body: JSON.stringify({
        model,
        stream: false,
        prompt: `${INSTRUCTIONS}\n\nMOMENTO DE LA MISIÓN: ${moment || "no especificado"}. No ubiques los hechos en otro momento.\n\nPREGUNTA:\n${question || "(sin pregunta)"}\n\nDATOS:\n${source}\n\nEXPLICACIÓN:`,
        options: { num_predict: 220, temperature: 0.1 },
      }),
    });
    if (!res.ok) {
      return { ok: false, text: null, model, reason: `el modelo respondió ${res.status}` };
    }
    const data = (await res.json()) as { response?: string };
    raw = (data.response ?? "").trim();
  } catch (error) {
    const timedOut = error instanceof Error && error.name === "TimeoutError";
    return {
      ok: false,
      text: null,
      model,
      reason: timedOut ? "el modelo tardó demasiado" : "el modelo no está disponible",
    };
  }

  if (!raw) return { ok: false, text: null, model, reason: "el modelo devolvió vacío" };
  if (/insuficiente/i.test(raw)) {
    return { ok: false, text: null, model, reason: "el modelo no pudo reescribir" };
  }

  if (CAUSAL.test(raw)) {
    return {
      ok: false,
      text: raw,
      model,
      reason: "la IA agregó una interpretación causal que los datos no sostienen",
    };
  }

  if (FORBIDDEN.test(raw)) {
    return {
      ok: false,
      text: raw,
      model,
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
      model,
      reason: `la IA agregó cifras que no están en los datos: ${invented.join(", ")}`,
    };
  }

  return { ok: true, text: raw, model, reason: null };
}

/** Loads the weights so the first real question is not eight seconds of cold start. */
export async function warmUp(): Promise<void> {
  const model = await pickModel();
  if (!model) return;
  try {
    await fetch(`${BASE}/api/generate`, {
      method: "POST",
      headers: { "content-type": "application/json" },
      signal: AbortSignal.timeout(60_000),
      body: JSON.stringify({
        model,
        stream: false,
        prompt: "ok",
        options: { num_predict: 1 },
      }),
    });
  } catch {
    // A warm-up that fails is not an error: the real call will report it.
  }
}
