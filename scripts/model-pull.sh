#!/usr/bin/env bash
# Скачивание базовой модели в Ollama.
# Использование: ./scripts/model-pull.sh [имя_модели]

set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=common.sh
source "$SCRIPT_DIR/common.sh"

MODEL="${1:-$(default_base_model)}"

require_ollama

echo "==> Скачиваем модель: ${MODEL}"
docker exec ollama ollama pull "${MODEL}"

echo "==> Установленные модели:"
docker exec ollama ollama list
