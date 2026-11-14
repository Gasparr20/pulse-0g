import { NextResponse } from "next/server";
import { buildCasePackage } from "@/lib/case";

export const dynamic = "force-dynamic";

export async function GET(request: Request) {
  const url = new URL(request.url);
  const raw = Number(url.searchParams.get("at"));
  const at = Number.isFinite(raw) ? raw : null;
  return NextResponse.json(buildCasePackage(at));
}
