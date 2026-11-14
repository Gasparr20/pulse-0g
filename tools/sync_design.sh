#!/usr/bin/env bash
# The gentle-design canvas reads design/ from the workspace root, while the
# project keeps its source of truth inside the repository. This copies one to the
# other so the canvas can open it without making the repo depend on the workspace.
set -euo pipefail
WS="${1:-/home/gaspar_22/dev}"
SRC="$(cd "$(dirname "$0")/.." && pwd)/design"
# Canvas-side comment resolutions live in the workspace copy. Bring them back
# into the repository before overwriting, or a sync would erase them.
if [ -d "$WS/design" ]; then
  find "$WS/design" -name comments.json -print0 2>/dev/null | while IFS= read -r -d '' f; do
    rel="${f#"$WS/design/"}"
    mkdir -p "$SRC/$(dirname "$rel")"
    cp "$f" "$SRC/$rel"
  done
fi

rm -rf "$WS/design"
mkdir -p "$WS/design"
cp -a "$SRC"/. "$WS/design"/
echo "design/ sincronizado en $WS/design desde $SRC"
