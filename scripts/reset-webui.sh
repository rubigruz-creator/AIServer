#!/usr/bin/env bash
# Сброс базы Open WebUI (пользователи и чаты). Модели Ollama не удаляются.

set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=common.sh
source "$SCRIPT_DIR/common.sh"

require_compose
cd_project

echo "==> Останавливаем стек..."
docker compose down

VOLUME=$(docker volume ls -q | grep open_webui_data | head -1 || true)
if [[ -n "${VOLUME}" ]]; then
  echo "==> Удаляем volume: ${VOLUME}"
  docker volume rm "${VOLUME}"
else
  echo "==> Volume open_webui_data не найден."
fi

docker compose up -d
sleep 20
docker compose ps
echo ""
echo "Войдите через «Войти» (не «Регистрация») с WEBUI_ADMIN_EMAIL / WEBUI_ADMIN_PASSWORD из .env"
