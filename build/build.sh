#!/usr/bin/env bash
# SPDX-License-Identifier: MIT
# Build a single-file TiddlyWiki from ~/PGA/wiki/. No server, no Python runtime, no Bun.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
TW="$ROOT/build/tw"
BIN="${TIDDLYWIKI:-$HOME/node_modules/.bin/tiddlywiki}"

[ -x "$BIN" ] || { echo "tiddlywiki not found at $BIN (set \$TIDDLYWIKI)"; exit 1; }

if [ ! -f "$TW/tiddlywiki.info" ]; then
  "$BIN" "$TW" --init empty
  python3 - "$TW/tiddlywiki.info" <<'PY'
import json, sys
p = sys.argv[1]
info = json.load(open(p))
info["plugins"] = ["tiddlywiki/markdown", "tiddlywiki/katex"]
json.dump(info, open(p, "w"), indent=4)
PY
fi

python3 "$ROOT/build/make_tiddlers.py"
"$BIN" "$TW" --build index
cp "$TW/output/index.html" "$ROOT/HeimWiki.html"
printf '\nbuilt: %s (%s)\n' "$ROOT/HeimWiki.html" "$(du -h "$ROOT/HeimWiki.html" | cut -f1)"
