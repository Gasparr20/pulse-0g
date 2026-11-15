import { NextResponse } from "next/server";
import { answer } from "@/lib/answer";
import { narrate } from "@/lib/narrate";

export const dynamic = "force-dynamic";

export async function POST(request: Request) {
  const body = await request.json().catch(() => null);
  const question = typeof body?.q === "string" ? body.q.slice(0, 300).trim() : "";
  if (!question) {
    return NextResponse.json({ error: "pregunta vacía" }, { status: 400 });
  }
  const mode = body?.mode === "ai" ? "ai" : "plain";
  const rawAt = body?.at;
  const at = typeof rawAt === "number" && Number.isFinite(rawAt) ? rawAt : null;
  const result = answer(question, at);

  // The model only rewrites sentences that are already anchored. If it fails or
  // drifts, the deterministic answer stands and the response says why.
  if (mode === "ai" && !result.refused) {
    const narration = await narrate(result.sentences.map((s) => s.text), question);
    return NextResponse.json({ ...result, narrated: narration });
  }

  return NextResponse.json(result);
}
