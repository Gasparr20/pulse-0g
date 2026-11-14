import { assemble } from "@/lib/assemble";
import Dashboard from "@/components/Dashboard";

// The database is seeded at build time; the page still reads it per request so a
// rebuild of the data shows up without restarting the server.
export const dynamic = "force-dynamic";

export default async function Page({
  searchParams,
}: {
  searchParams: Promise<{ tab?: string; q?: string; at?: string; case?: string }>;
}) {
  const { tab, q, at, case: caseParam } = await searchParams;
  const initialTab = tab === "real" || tab === "ask" ? tab : "mission";
  const parsed = Number(at);
  // Default to the last day of the flight: post-return samples are debrief data,
  // not the operational state of a crew still in mission.
  const clock = Number.isFinite(parsed) && at !== undefined ? parsed : 180;
  return (
    <Dashboard
      data={assemble(clock)}
      initialTab={initialTab}
      initialQuestion={q ?? null}
      clock={clock}
      autoCase={caseParam === "1"}
    />
  );
}
