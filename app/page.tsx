import { assemble } from "@/lib/assemble";
import Dashboard from "@/components/Dashboard";

// The database is seeded at build time; the page still reads it per request so a
// rebuild of the data shows up without restarting the server.
export const dynamic = "force-dynamic";

export default function Page() {
  return <Dashboard data={assemble()} />;
}
