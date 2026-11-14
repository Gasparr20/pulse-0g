import { DatabaseSync } from "node:sqlite";
import path from "node:path";

let handle: DatabaseSync | null = null;

/** Read-only handle to the seeded database. The application never writes:
 *  the database is produced at build time by tools/build_db.py. */
export function db(): DatabaseSync {
  if (!handle) {
    const file = path.join(process.cwd(), "db", "crewcheck.sqlite");
    handle = new DatabaseSync(file, { readOnly: true });
  }
  return handle;
}

export function all<T>(sql: string, ...params: unknown[]): T[] {
  return db().prepare(sql).all(...(params as never[])) as T[];
}

export function one<T>(sql: string, ...params: unknown[]): T | undefined {
  return db().prepare(sql).get(...(params as never[])) as T | undefined;
}
