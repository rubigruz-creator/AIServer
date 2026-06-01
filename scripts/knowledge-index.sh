#!/usr/bin/env bash
# Переиндексация prompts/knowledge в RAG (intake-api).
# Использование: ./scripts/knowledge-index.sh
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=common.sh
source "$SCRIPT_DIR/common.sh"

cd_project

if [[ -f "$ROOT_DIR/.env" ]]; then
  # shellcheck disable=SC1091
  set -a
  source "$ROOT_DIR/.env"
  set +a
fi

INTAKE_URL="${INTAKE_URL:-http://127.0.0.1:3101}"
USER="${INTAKE_ADMIN_USER:-admin}"
PASS="${INTAKE_ADMIN_PASSWORD:-}"

if [[ -z "$PASS" ]]; then
  echo "Ошибка: задайте INTAKE_ADMIN_PASSWORD в .env" >&2
  exit 1
fi

echo "==> RAG reindex → ${INTAKE_URL}/api/rag/reindex"
resp=$(curl -sfS -u "${USER}:${PASS}" -X POST "${INTAKE_URL}/api/rag/reindex")
echo "$resp"
echo "==> Готово. При изменении промпта также: ./scripts/model-create.sh"
