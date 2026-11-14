import { NextResponse } from "next/server";
import { answer } from "@/lib/answer";

export const dynamic = "force-dynamic";

export async function POST(request: Request) {
  const body = await request.json().catch(() => null);
  const question = typeof body?.q === "string" ? body.q.slice(0, 300).trim() : "";
  if (!question) {
    return NextResponse.json({ error: "pregunta vacía" }, { status: 400 });
  }
  const rawAt = body?.at;
  const at = typeof rawAt === "number" && Number.isFinite(rawAt) ? rawAt : null;
  return NextResponse.json(answer(question, at));
}
