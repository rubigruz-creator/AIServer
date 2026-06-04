#!/usr/bin/env bash
# Прогрев модели Ollama в RAM (снижает задержку первого ответа виджета).
# Использование: ./scripts/model-warmup.sh [модель]
# Вызывается из stack.sh start и widget-deploy.sh после docker compose up.

set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=common.sh
source "$SCRIPT_DIR/common.sh"

MODEL="${1:-${OLLAMA_WARMUP_MODEL:-truck-service:latest}}"
OLLAMA_URL="${OLLAMA_URL:-http://127.0.0.1:11434}"
KEEP_ALIVE="${OLLAMA_KEEP_ALIVE:--1}"

require_ollama

echo "==> Прогрев Ollama: ${MODEL} (keep_alive=${KEEP_ALIVE})"

payload=$(cat <<EOF
{
  "model": "${MODEL}",
  "stream": false,
  "keep_alive": "${KEEP_ALIVE}",
  "messages": [{"role": "user", "content": "."}],
  "options": {"num_predict": 1}
}
EOF
)

if curl -sfS "${OLLAMA_URL}/api/chat" \
  -H 'Content-Type: application/json' \
  -d "${payload}" \
  -o /dev/null; then
  echo "==> Модель в памяти, первый ответ виджета должен быть быстрее."
else
  echo "Предупреждение: прогрев не удался (модель не создана?). Запустите:" >&2
  echo "  ./scripts/model-create.sh" >&2
  exit 1
fi
