#!/usr/bin/env python3
"""Gate for the evidence cards. Offline, no server needed.

    python3 tools/check_cards.py

Errors block a card from being used. Warnings do not, but they name the exact
defect, and the two most common ones (a link to an index page instead of the
passage, and a placeholder hash) are the ones that make a citation unverifiable.
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CARDS = ROOT / "evidence" / "cards"
CONFIG = ROOT / "config" / "bands.json"

KINDS = {"threshold", "hazard", "protocol", "measurement"}
REQUIRED = ["id", "kind", "title_es", "summary_es", "quote", "source_label",
            "url", "retrieved_at", "sha256", "applies_to", "license"]
ID_RE = re.compile(r"^EVD-[A-Z]+-\d{3}$")
NUM = re.compile(r"\d+(?:[.,]\d+)?")


def numbers(text):
    return {n.replace(",", ".") for n in NUM.findall(text or "")}


def is_index_url(url):
    return bool(re.search(r"/(risks|evidence|gaps|risks/)\/?$", url, re.I)) or \
        bool(re.search(r"/risks/?$", url, re.I))


def check_card(path, config):
    errors, warnings = [], []
    try:
        card = json.loads(path.read_text())
    except json.JSONDecodeError as e:
        return [f"JSON inválido: {e}"], []

    for field in REQUIRED:
        if not card.get(field):
            errors.append(f"campo obligatorio vacío: {field}")

    cid = card.get("id", "")
    if not ID_RE.match(cid):
        errors.append(f"id con formato inválido: {cid!r} (esperado EVD-AREA-000)")
    elif path.stem != cid:
        errors.append(f"el archivo se llama {path.stem}.json pero el id es {cid}")

    kind = card.get("kind")
    if kind not in KINDS:
        errors.append(f"kind inválido: {kind!r}")

    applies = card.get("applies_to") or []
    if not applies:
        errors.append("applies_to vacío")
    for a in applies:
        # An entry is either a bare indicator variable (systolic, sleep_hours) or a
        # prefixed tag (hazard:radiation). Anything else is a typo.
        if not re.fullmatch(r"(hazard:[a-z]+|[a-z0-9_]+)", str(a)):
            errors.append(f"applies_to inválido: {a!r} (usá 'systolic' o 'hazard:radiation')")

    # quote-first rule: the summary may not introduce a number the quote lacks
    invented = numbers(card.get("summary_es")) - numbers(card.get("quote"))
    if invented:
        errors.append(f"el resumen agrega números que la cita no tiene: {sorted(invented)}")

    if kind == "threshold":
        th = card.get("thresholds")
        if not isinstance(th, dict):
            errors.append("kind=threshold sin objeto thresholds")
        else:
            for key in ("variable", "value"):
                if key not in th:
                    errors.append(f"thresholds sin {key}")
            if not isinstance(th.get("value"), (int, float)):
                errors.append("thresholds.value no es numérico")

    if is_index_url(card.get("url", "")):
        warnings.append(
            "la URL parece un índice, no el pasaje: un clic debe llevar al párrafo citado")
    if card.get("sha256") in ("", "webpage"):
        warnings.append(
            "sha256 es un marcador, no un hash: guardá el archivo y hashealo si la fuente puede cambiar")
    if not card.get("verified_by"):
        warnings.append("verified_by vacío: falta quién verificó la cita")

    # a config rule that cites a card must agree with that card
    for variable, entry in config.items():
        if not isinstance(entry, dict):
            continue
        if entry.get("evidence_card_id") == cid:
            th = card.get("thresholds") or {}
            value = th.get("value")
            if kind != "threshold":
                errors.append(f"config/bands.json cita {cid} para {variable} pero no es threshold")
            elif value not in (entry.get("amber"), entry.get("red")):
                errors.append(
                    f"{cid} declara {value} pero config/bands.json usa "
                    f"amber={entry.get('amber')} red={entry.get('red')} para {variable}")

    return errors, warnings


def main():
    try:
        config = json.loads(CONFIG.read_text())
    except Exception:
        config = {}

    files = sorted(p for p in CARDS.glob("EVD-*.json"))
    if not files:
        print("no hay tarjetas todavía en evidence/cards/ (EVD-*.json)")
        return 0

    total_errors = total_warnings = 0
    seen = {}
    for path in files:
        errors, warnings = check_card(path, config)
        cid = path.stem
        if cid in seen:
            errors.append(f"id duplicado: también aparece en {seen[cid]}")
        seen[cid] = path.name
        status = "FAIL" if errors else ("warn" if warnings else "ok  ")
        print(f"{status} {cid}")
        for e in errors:
            print(f"       error:   {e}")
            total_errors += 1
        for w in warnings:
            print(f"       aviso:   {w}")
            total_warnings += 1

    print(f"\n{len(files)} tarjeta(s) · {total_errors} error(es) · {total_warnings} aviso(s)")
    if total_errors:
        print("Hay que corregir los errores antes de cargar estas tarjetas.")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
