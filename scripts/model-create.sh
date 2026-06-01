#!/usr/bin/env bash
# Создание модели truck-service (промпт + база знаний + параметры Ollama).
# Использование: ./scripts/model-create.sh [базовая_модель]
# Пример:      ./scripts/model-create.sh qwen2.5:1.5b

set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=common.sh
source "$SCRIPT_DIR/common.sh"

BASE_MODEL="${1:-$(default_base_model)}"
PROMPT_FILE="$ROOT_DIR/prompts/truck-service-system.txt"
KNOWLEDGE_DIR="$ROOT_DIR/prompts/knowledge"
PARAMS_FILE="$ROOT_DIR/ollama/Modelfile.params"
BUILD_FILE="/tmp/Modelfile.truck-service.build"
# Лимит символов для markdown-базы (≈1500–2000 токенов); не раздувать на 1.5B
KNOWLEDGE_MAX_CHARS="${KNOWLEDGE_MAX_CHARS:-6000}"

require_ollama

if [[ ! -f "$PROMPT_FILE" ]]; then
  echo "Ошибка: не найден $PROMPT_FILE" >&2
  exit 1
fi

if ! docker exec ollama ollama list | grep -q "${BASE_MODEL%%:*}"; then
  echo "==> Базовая модель не найдена. Скачиваем ${BASE_MODEL}..."
  docker exec ollama ollama pull "${BASE_MODEL}"
fi

append_knowledge() {
  if [[ ! -d "$KNOWLEDGE_DIR" ]]; then
    return 0
  fi
  local files=()
  local f
  shopt -s nullglob
  for f in "$KNOWLEDGE_DIR"/*.md; do
    [[ "$(basename "$f")" == "README.md" ]] && continue
    files+=("$f")
  done
  shopt -u nullglob
  if [[ ${#files[@]} -eq 0 ]]; then
    return 0
  fi
  IFS=$'\n' files=($(printf '%s\n' "${files[@]}" | sort))
  unset IFS

  echo ""
  echo "--- База знаний (автосборка из prompts/knowledge/) ---"
  local total=0
  local chunk
  for f in "${files[@]}"; do
    chunk=$(cat "$f")
    if [[ $((total + ${#chunk})) -gt $KNOWLEDGE_MAX_CHARS ]]; then
      local remain=$((KNOWLEDGE_MAX_CHARS - total))
      if [[ $remain -gt 200 ]]; then
        head -c "$remain" "$f"
        echo ""
        echo "[... обрезано, лимит KNOWLEDGE_MAX_CHARS=$KNOWLEDGE_MAX_CHARS; доп. факты — через RAG ...]"
      fi
      break
    fi
    echo "$chunk"
    total=$((total + ${#chunk}))
  done
}

{
  echo "FROM ${BASE_MODEL}"
  echo 'SYSTEM """'
  cat "$PROMPT_FILE"
  append_knowledge
  echo '"""'
  echo ""
  cat "$PARAMS_FILE"
} > "$BUILD_FILE"

docker cp "$BUILD_FILE" ollama:/tmp/Modelfile.truck-service.build

echo "==> Создаём модель truck-service (база: ${BASE_MODEL})..."
docker exec ollama ollama create truck-service -f /tmp/Modelfile.truck-service.build

echo "==> Готово:"
docker exec ollama ollama list
