#!/usr/bin/env bash
# Полное применение изменений в prompts/ (RAG + модель + виджет).
# Запуск на VPS: cd /root/AIServer && ./scripts/knowledge-apply.sh
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=common.sh
source "$SCRIPT_DIR/common.sh"

cd_project

echo "==> 1/4 Проверка файлов знаний на диске"
for f in prompts/truck-service-system.txt prompts/knowledge/faq.md prompts/knowledge/services.md; do
  if [[ ! -f "$f" ]]; then
    echo "Ошибка: нет $f" >&2
    exit 1
  fi
  echo "    $f ($(wc -c <"$f") bytes)"
done
if grep -qi "кузов" prompts/knowledge/services.md && grep -qi "не делаем\|не выполняем" prompts/knowledge/services.md; then
  echo "    OK: services.md упоминает кузов в блоке ограничений"
fi

echo "==> 2/4 RAG reindex"
"$SCRIPT_DIR/knowledge-index.sh"

echo "==> 3/4 Пересборка модели truck-service"
"$SCRIPT_DIR/model-create.sh"

echo "==> 4/4 Деплой embed (chat.js → /intake/api/chat)"
"$SCRIPT_DIR/widget-deploy.sh"

echo ""
echo "==> Проверка RAG status (нужен INTAKE_ADMIN_PASSWORD в .env)"
if [[ -f "$ROOT_DIR/.env" ]]; then
  set -a
  # shellcheck disable=SC1091
  source "$ROOT_DIR/.env"
  set +a
fi
if [[ -n "${INTAKE_ADMIN_PASSWORD:-}" ]]; then
  curl -sfS -u "${INTAKE_ADMIN_USER:-admin}:${INTAKE_ADMIN_PASSWORD}" \
    "http://127.0.0.1:3101/api/rag/status" | head -c 500
  echo ""
fi

if grep -q "intake/api/chat" /var/www/aiserver/embed/chat.js 2>/dev/null; then
  echo "==> OK: продакшен chat.js использует /intake/api/chat (RAG)"
else
  echo "==> ВНИМАНИЕ: /var/www/aiserver/embed/chat.js без intake/api/chat — виджет без RAG!" >&2
fi

echo "==> Готово. Тест: https://agent.remont-gazon.ru/embed/chat.html"
echo "    Вопрос: «Делаете кузовные работы?» — ожидается «Нет»."
