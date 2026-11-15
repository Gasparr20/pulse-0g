#!/usr/bin/env python3
"""Verify every external link the project cites.

    python3 tools/check_links.py

Scans the evidence cards and the documentation, requests each distinct URL, and
reports the ones that do not serve a usable page. A 200 is not enough: NASA's site
returns its own error page with status 200, which is exactly how a dead link can hide
for weeks. The script therefore also looks for error markers in the body.

Exit code is non-zero when any link fails, so it can be wired into a check.
"""
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SOURCES = [ROOT / "evidence" / "cards", ROOT / "docs", ROOT / "evidence"]
URL = re.compile(r"https?://[^\s\"'<>)\]]+")
ERROR_MARKERS = ("Error Occurred", "Page Lost", "404 Not Found", "Page Not Found")
SKIP = ("127.0.0.1", "localhost", "registry.npmjs.org", "opencollective.com",
        "tidelift.com", "github.com/sponsors", "w3.org", "example.invalid")


def collect() -> dict[str, set[str]]:
    found: dict[str, set[str]] = {}
    for base in SOURCES:
        for path in base.rglob("*"):
            if not path.is_file() or path.suffix not in {".md", ".json"}:
                continue
            for url in URL.findall(path.read_text(encoding="utf-8", errors="replace")):
                url = url.rstrip(".,;:)")
                if any(s in url for s in SKIP) or url.endswith("/file="):
                    continue
                found.setdefault(url, set()).add(str(path.relative_to(ROOT)))
    return found


def check(url: str) -> tuple[bool, str]:
    request = urllib.request.Request(
        url, headers={"User-Agent": "Mozilla/5.0 (Pulse-0G link check)"}
    )
    try:
        with urllib.request.urlopen(request, timeout=40) as response:
            body = response.read(200_000).decode("utf-8", errors="replace")
            for marker in ERROR_MARKERS:
                if marker.lower() in body.lower():
                    return False, f"{response.status} pero sirve una página de error"
            if len(body.strip()) < 200:
                return False, f"{response.status} pero el cuerpo está vacío"
            return True, str(response.status)
    except urllib.error.HTTPError as error:
        return False, str(error.code)
    except Exception as error:  # noqa: BLE001 - any network failure is a failure
        return False, type(error).__name__


def main() -> int:
    links = collect()
    bad = 0
    for url in sorted(links):
        ok, detail = check(url)
        used = ", ".join(sorted(links[url]))
        if ok:
            print(f"ok   {detail:>4}  {url}")
        else:
            bad += 1
            print(f"FAIL {detail:>22}  {url}\n       citado en: {used}")
    print(f"\n{len(links)} enlaces · {bad} con problemas")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
