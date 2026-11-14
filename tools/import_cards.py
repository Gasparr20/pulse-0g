#!/usr/bin/env python3
"""Split a pasted blob of card JSON into one file per card.

Usage:
    python3 tools/import_cards.py evidence/cards/_incoming.txt

The input may be any text containing complete JSON objects, pretty-printed or not,
one after another. Duplicated ids keep the LAST version, so a corrected card placed
after its original wins. Nothing is written for an object that has no `id`.

After importing, run:  python3 tools/check_cards.py
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CARDS = ROOT / "evidence" / "cards"


def extract_objects(text: str):
    """Yield every complete top-level JSON object found in the text."""
    depth = 0
    start = None
    in_string = False
    escape = False
    for i, ch in enumerate(text):
        if in_string:
            if escape:
                escape = False
            elif ch == "\\":
                escape = True
            elif ch == '"':
                in_string = False
            continue
        if ch == '"':
            in_string = True
        elif ch == "{":
            if depth == 0:
                start = i
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0 and start is not None:
                yield text[start : i + 1]
                start = None


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    source = Path(sys.argv[1])
    if not source.exists():
        print(f"no existe: {source}")
        return 2

    cards: dict[str, dict] = {}
    order: list[str] = []
    for chunk in extract_objects(source.read_text(encoding="utf-8")):
        try:
            card = json.loads(chunk)
        except json.JSONDecodeError:
            continue
        cid = card.get("id")
        if not isinstance(cid, str) or not cid:
            continue
        if cid not in cards:
            order.append(cid)
        cards[cid] = card  # last wins

    if not cards:
        print("no se encontró ninguna tarjeta con id en el archivo")
        return 1

    CARDS.mkdir(parents=True, exist_ok=True)
    for cid in order:
        path = CARDS / f"{cid}.json"
        path.write_text(json.dumps(cards[cid], ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"escrita {path.name}")

    print(f"\n{len(cards)} tarjeta(s) importada(s). Ahora: python3 tools/check_cards.py")
    return 0


if __name__ == "__main__":
    sys.exit(main())
