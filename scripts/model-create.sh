#!/usr/bin/env bash
# Создание модели truck-service (промпт + параметры Ollama).
# Использование: ./scripts/model-create.sh [базовая_модель]
# Пример:      ./scripts/model-create.sh qwen2.5:1.5b

set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=common.sh
source "$SCRIPT_DIR/common.sh"

BASE_MODEL="${1:-$(default_base_model)}"
PROMPT_FILE="$ROOT_DIR/prompts/truck-service-system.txt"
PARAMS_FILE="$ROOT_DIR/ollama/Modelfile.params"
BUILD_FILE="/tmp/Modelfile.truck-service.build"

require_ollama

if [[ ! -f "$PROMPT_FILE" ]]; then
  echo "Ошибка: не найден $PROMPT_FILE" >&2
  exit 1
fi

if ! docker exec ollama ollama list | grep -q "${BASE_MODEL%%:*}"; then
  echo "==> Базовая модель не найдена. Скачиваем ${BASE_MODEL}..."
  docker exec ollama ollama pull "${BASE_MODEL}"
fi

{
  echo "FROM ${BASE_MODEL}"
  echo 'SYSTEM """'
  cat "$PROMPT_FILE"
  echo '"""'
  echo ""
  cat "$PARAMS_FILE"
} > "$BUILD_FILE"

docker cp "$BUILD_FILE" ollama:/tmp/Modelfile.truck-service.build

echo "==> Создаём модель truck-service (база: ${BASE_MODEL})..."
docker exec ollama ollama create truck-service -f /tmp/Modelfile.truck-service.build

echo "==> Готово:"
docker exec ollama ollama list
