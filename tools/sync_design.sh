#!/usr/bin/env bash
# The gentle-design canvas reads design/ from the workspace root, not from the
# repository. This copies the versioned artboards into that location.
#
# comments.json is NOT copied: the canvas owns that file, and overwriting it erases
# the user's comments and their resolutions. It is gitignored for the same reason.
set -euo pipefail
WS="${1:-/home/gaspar_22/dev}"
SRC="$(cd "$(dirname "$0")/.." && pwd)/design"

find "$SRC" -type d | while IFS= read -r d; do
  mkdir -p "$WS/design${d#"$SRC"}"
done
find "$SRC" -type f ! -name 'comments.json' | while IFS= read -r f; do
  cp -f "$f" "$WS/design${f#"$SRC"}"
done
echo "artboards sincronizados en $WS/design (comments.json intacto)"
