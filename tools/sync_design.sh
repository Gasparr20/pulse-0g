#!/usr/bin/env bash
# The gentle-design canvas reads design/ from the workspace root, while the
# project keeps its source of truth inside the repository. This copies one to the
# other so the canvas can open it without making the repo depend on the workspace.
set -euo pipefail
WS="${1:-/home/gaspar_22/dev}"
SRC="$(cd "$(dirname "$0")/.." && pwd)/design"
rm -rf "$WS/design"
mkdir -p "$WS/design"
cp -a "$SRC"/. "$WS/design"/
echo "design/ sincronizado en $WS/design desde $SRC"
