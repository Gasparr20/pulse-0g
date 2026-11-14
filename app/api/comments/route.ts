import { NextResponse } from "next/server";
import { addComment, listComments } from "@/lib/journal";

export const dynamic = "force-dynamic";

export async function GET(request: Request) {
  const url = new URL(request.url);
  const subject = url.searchParams.get("subject") ?? "";
  if (!subject) return NextResponse.json({ error: "falta subject" }, { status: 400 });
  const target = url.searchParams.get("target") ?? undefined;
  return NextResponse.json({ comments: listComments(subject, target) });
}

export async function POST(request: Request) {
  const body = await request.json().catch(() => null);
  if (!body || typeof body.body !== "string") {
    return NextResponse.json({ error: "comentario inválido" }, { status: 400 });
  }
  try {
    const comment = addComment({
      subjectId: String(body.subjectId ?? ""),
      targetType: String(body.targetType ?? "indicator"),
      targetId: String(body.targetId ?? ""),
      authorRole: String(body.authorRole ?? "crew"),
      body: body.body,
      missionClock: String(body.missionClock ?? ""),
    });
    return NextResponse.json({ comment }, { status: 201 });
  } catch (error) {
    const message = error instanceof Error ? error.message : "error";
    return NextResponse.json({ error: message }, { status: 400 });
  }
}
