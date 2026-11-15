import { NextResponse } from "next/server";
import { modelAvailable, warmUp } from "@/lib/narrate";

export const dynamic = "force-dynamic";

export async function POST() {
  // Fire-and-forget load of the weights; the client does not wait for the answer.
  void warmUp();
  return NextResponse.json({ warming: true });
}

export async function GET() {
  return NextResponse.json({ available: await modelAvailable() });
}
