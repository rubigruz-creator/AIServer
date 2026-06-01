#!/usr/bin/env bash
# Экспорт отчёта для разбора диалогов (ежемесячный цикл улучшения FAQ).
# Использование: ./scripts/knowledge-feedback-export.sh [output.json]
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=common.sh
source "$SCRIPT_DIR/common.sh"

cd_project

if [[ -f "$ROOT_DIR/.env" ]]; then
  set -a
  # shellcheck disable=SC1091
  source "$ROOT_DIR/.env"
  set +a
fi

OUT="${1:-$ROOT_DIR/prompts/knowledge/feedback-export.json}"
INTAKE_URL="${INTAKE_URL:-http://127.0.0.1:3101}"
USER="${INTAKE_ADMIN_USER:-admin}"
PASS="${INTAKE_ADMIN_PASSWORD:-}"

if [[ -z "$PASS" ]]; then
  echo "Ошибка: задайте INTAKE_ADMIN_PASSWORD в .env" >&2
  exit 1
fi

mkdir -p "$(dirname "$OUT")"
curl -sfS -u "${USER}:${PASS}" \
  "${INTAKE_URL}/api/admin/feedback-report?limit=100&min_user_messages=2" \
  -o "$OUT"
echo "==> Сохранено: $OUT"
echo "    Ревью → дополните prompts/knowledge/faq.md → ./scripts/knowledge-index.sh"
