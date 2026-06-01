#!/usr/bin/env bash
# Скрейп whitelist → prompts/knowledge/sites-scraped.md (черновик для ревью)
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$ROOT_DIR"
python3 "$SCRIPT_DIR/knowledge-scrape.py" "$@"
