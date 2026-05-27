#!/usr/bin/env bash
# Выгрузить модель из RAM (освободить память на слабом VPS).

set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=common.sh
source "$SCRIPT_DIR/common.sh"

MODEL="${1:-truck-service}"

require_ollama

docker exec ollama ollama stop "${MODEL}" 2>/dev/null || true
echo "==> Модель ${MODEL} выгружена из памяти (если была загружена)."
