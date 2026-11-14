import { DatabaseSync } from "node:sqlite";
import path from "node:path";
import fs from "node:fs";

/** Operational journal, kept apart from the evidence database on purpose.
 *
 *  The evidence database is built at build time, committed, and opened read-only:
 *  nothing at runtime can alter what a mission recorded. Comments are operational
 *  state, so they live in their own file and the only permitted operation against
 *  them is insertion. The triggers below refuse UPDATE and DELETE even if a future
 *  route tried it.
 */
let handle: DatabaseSync | null = null;

const JOURNAL = path.join(process.cwd(), "db", "journal.sqlite");

function journal(): DatabaseSync {
  if (!handle) {
    fs.mkdirSync(path.dirname(JOURNAL), { recursive: true });
    handle = new DatabaseSync(JOURNAL);
    handle.exec("PRAGMA journal_mode = WAL");
    handle.exec(`
      CREATE TABLE IF NOT EXISTS comment (
        id           INTEGER PRIMARY KEY,
        subject_id   TEXT NOT NULL,
        target_type  TEXT NOT NULL CHECK (target_type IN ('measurement','indicator','band_event','case_package')),
        target_id    TEXT NOT NULL,
        author_role  TEXT NOT NULL CHECK (author_role IN ('crew','surgeon')),
        body         TEXT NOT NULL,
        created_at   TEXT NOT NULL,
        mission_clock TEXT NOT NULL,
        revision_of  INTEGER REFERENCES comment(id),
        verified     INTEGER NOT NULL DEFAULT 0 CHECK (verified = 0)
      );
      CREATE INDEX IF NOT EXISTS idx_comment_target ON comment(subject_id, target_id);
      CREATE TRIGGER IF NOT EXISTS comment_no_update
        BEFORE UPDATE ON comment
        BEGIN SELECT RAISE(ABORT, 'comment is append-only'); END;
      CREATE TRIGGER IF NOT EXISTS comment_no_delete
        BEFORE DELETE ON comment
        BEGIN SELECT RAISE(ABORT, 'comment is append-only'); END;
    `);
  }
  return handle;
}

export interface Comment {
  id: number;
  subject_id: string;
  target_type: string;
  target_id: string;
  author_role: string;
  body: string;
  created_at: string;
  mission_clock: string;
  revision_of: number | null;
}

export function listComments(subjectId: string, targetId?: string): Comment[] {
  const db = journal();
  const sql = targetId
    ? "SELECT * FROM comment WHERE subject_id = ? AND target_id = ? ORDER BY id"
    : "SELECT * FROM comment WHERE subject_id = ? ORDER BY id";
  const params = targetId ? [subjectId, targetId] : [subjectId];
  return db.prepare(sql).all(...(params as never[])) as unknown as Comment[];
}

export function addComment(input: {
  subjectId: string;
  targetType: string;
  targetId: string;
  authorRole: string;
  body: string;
  missionClock: string;
}): Comment {
  const db = journal();
  const body = input.body.trim().slice(0, 2000);
  if (!body) throw new Error("comentario vacío");
  const allowed = new Set(["measurement", "indicator", "band_event", "case_package"]);
  if (!allowed.has(input.targetType)) throw new Error("target_type inválido");
  if (!new Set(["crew", "surgeon"]).has(input.authorRole)) throw new Error("rol inválido");

  const result = db
    .prepare(
      `INSERT INTO comment (subject_id, target_type, target_id, author_role, body,
         created_at, mission_clock)
       VALUES (?,?,?,?,?,?,?)`,
    )
    .run(
      input.subjectId,
      input.targetType,
      input.targetId.slice(0, 200),
      input.authorRole,
      body,
      new Date().toISOString(),
      input.missionClock.slice(0, 40),
    );
  const id = Number(result.lastInsertRowid);
  return db.prepare("SELECT * FROM comment WHERE id = ?").get(id) as unknown as Comment;
}
