#!/usr/bin/env python3
"""Contract check for the query intents and the claim verifier.

Run with the app up:  python3 tools/check_answers.py [base_url]
Exits non-zero on the first violated assertion.
"""
import json
import sys
import urllib.request

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:3210"

QUESTIONS = [
    "¿Cómo viene el sueño?",
    "¿Qué está pidiendo atención?",
    "¿Cómo cambió la presión respecto a mi base?",
    "¿Qué datos faltan?",
    "¿Por qué la presión está en gris?",
    "¿Cómo va la dosis de radiación?",
    "¿De dónde sale este dato?",
    "¿Estoy deshidratado?",
    "¿Cuál es la capital de Francia?",
]


def ask(q: str) -> dict:
    req = urllib.request.Request(
        f"{BASE}/api/ask",
        data=json.dumps({"q": q}).encode(),
        headers={"content-type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.load(r)


def main() -> int:
    failures = 0
    seen_intents = set()
    for q in QUESTIONS:
        a = ask(q)
        struck = [s for s in a["sentences"] if s.get("struck")]
        seen_intents.add(a["intent"])
        ok_verify = len(struck) == 0
        # A refused answer must say so; a normal answer must not be empty.
        ok_shape = a["refused"] is True or len(a["sentences"]) > 0
        status = "ok" if ok_verify and ok_shape else "FAIL"
        if status == "FAIL":
            failures += 1
        print(f"{status:4} intent={a['intent']:<18} refused={str(a['refused']):<5} "
              f"struck={len(struck)}  {q}")
        for s in struck:
            print(f"      tachada: {s['text'][:80]} -> {s.get('struckReason')}")

    # The demo moment is FD180, where alerts actually fire. Testing only the
    # default clock hid a struck sentence there, because at the end of the mission
    # nothing is out of band and the alert branch never ran.
    probe_at = {"q": "¿Qué está pidiendo atención?", "at": 180}
    req = urllib.request.Request(
        f"{BASE}/api/ask",
        data=json.dumps(probe_at).encode(),
        headers={"content-type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=20) as r:
        demo = json.load(r)
    struck_demo = [s for s in demo["sentences"] if s.get("struck")]
    print(f"\n{'ok  ' if not struck_demo else 'FAIL'} FD180 · alerts · "
          f"{len(demo['sentences'])} frase(s) · {len(struck_demo)} tachada(s)")
    for s in struck_demo:
        print(f"      {s['text'][:70]} -> {s.get('struckReason')}")
    if struck_demo:
        failures += 1

    clinical = ask("¿Estoy deshidratado?")
    assert clinical["refused"] is True, "a clinical question must be refused"
    assert clinical["intent"] == "clinical_request", "clinical intent not detected"

    outside = ask("¿Cuál es la capital de Francia?")
    assert outside["refused"] is True, "an out-of-corpus question must be refused"
    assert outside["intent"] == "abstain", "fallback intent not reached"

    probe = json.load(urllib.request.urlopen(f"{BASE}/api/verify-probe", timeout=20))
    print("\nverificador (autoprueba):")
    for r in probe["results"]:
        print(f"  {'ok  ' if r['pass'] else 'FAIL'} esperado={r['expected']:<9} "
              f"obtenido={r['actual']:<9} {r['text']}")
    if not probe["pass"]:
        print("  el verificador aceptó una frase que debía rechazar")
        failures += 1

    required = {"series", "alerts", "baseline", "missing", "why", "radiation", "provenance"}
    missing_intents = required - seen_intents
    print(f"\nintents cubiertas: {len(seen_intents)} -> {sorted(seen_intents)}")
    if missing_intents:
        print(f"FALTAN: {sorted(missing_intents)}")
        failures += 1
    print(f"\n{'PASS' if failures == 0 else 'FAIL'} ({failures} fallas)")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
