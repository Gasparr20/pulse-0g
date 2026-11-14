#!/usr/bin/env python3
"""Contract check for the append-only journal and the case package.

Run with the app up:  python3 tools/check_case.py [base_url]
"""
import json
import sqlite3
import sys
import urllib.error
import urllib.request

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:3210"
SUBJECT = "SYNTH:ASTRO-01"
TARGET = "sleep_hours@FD180"


def post(path, payload):
    req = urllib.request.Request(
        f"{BASE}{path}",
        data=json.dumps(payload).encode(),
        headers={"content-type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            return r.status, json.load(r)
    except urllib.error.HTTPError as e:
        return e.code, json.load(e)


def get(path):
    with urllib.request.urlopen(f"{BASE}{path}", timeout=20) as r:
        return json.load(r)


def main() -> int:
    failures = 0

    # 1. a valid note is stored and comes back
    status, payload = post("/api/comments", {
        "subjectId": SUBJECT, "targetType": "indicator", "targetId": TARGET,
        "authorRole": "crew", "body": "Dormí mal por ruido de la bomba de calor.",
        "missionClock": "FD180",
    })
    assert status == 201, f"expected 201, got {status}: {payload}"
    note_id = payload["comment"]["id"]
    print(f"ok   nota creada id={note_id}")

    threads = get(f"/api/comments?subject={SUBJECT}&target={TARGET}")["comments"]
    assert any(c["id"] == note_id for c in threads), "the note is not listed"
    print(f"ok   listada ({len(threads)} nota(s) en ese indicador)")

    # 2. invalid input is rejected
    for bad, why in [
        ({"authorRole": "admin"}, "rol inválido"),
        ({"targetType": "organ"}, "target_type inválido"),
        ({"body": "   "}, "cuerpo vacío"),
    ]:
        payload = {"subjectId": SUBJECT, "targetType": "indicator", "targetId": TARGET,
                   "authorRole": "crew", "body": "x", "missionClock": "FD180"}
        payload.update(bad)
        status, _ = post("/api/comments", payload)
        ok = status == 400
        print(f"{'ok  ' if ok else 'FAIL'} rechaza {why} -> {status}")
        if not ok:
            failures += 1

    # 3. the package carries the thread and the bands
    pkg = get(f"/api/case?at=180")
    assert pkg["comments"], "the case package has no comment thread"
    assert "Dormí mal" in pkg["report"], "the report does not print the note"
    assert any(i["band"] == "red" for i in pkg["indicators"]), "no red band at FD180"
    print(f"ok   paquete {pkg['packageId']} · {pkg['missionClock']} · "
          f"{len(pkg['indicators'])} indicadores · {len(pkg['comments'])} notas")

    # 4. the journal refuses UPDATE and DELETE even from SQL
    con = sqlite3.connect("db/journal.sqlite")
    for statement, label in [
        ("UPDATE comment SET body='mutado' WHERE id=?", "UPDATE"),
        ("DELETE FROM comment WHERE id=?", "DELETE"),
    ]:
        try:
            con.execute(statement, (note_id,))
            con.commit()
            print(f"FAIL {label} fue aceptado")
            failures += 1
        except sqlite3.IntegrityError as e:
            print(f"ok   {label} bloqueado -> {e}")
    con.close()

    print(f"\n{'PASS' if failures == 0 else 'FAIL'} ({failures} fallas)")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
