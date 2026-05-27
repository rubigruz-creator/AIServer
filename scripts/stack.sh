#!/usr/bin/env bash
# Управление Docker-стеком: start | stop | status

set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=common.sh
source "$SCRIPT_DIR/common.sh"

require_compose
cd_project

CMD="${1:-status}"

case "$CMD" in
  start)
    docker compose up -d
    echo "==> Стек запущен. Локально: http://127.0.0.1:3000"
    echo "==> Публично: https://\${DOMAIN} (см. .env)"
    docker compose ps
    ;;
  stop)
    docker compose down
    echo "==> Стек остановлен (данные в volumes сохранены)."
    ;;
  status)
    docker compose ps
    ;;
  *)
    echo "Использование: $0 {start|stop|status}" >&2
    exit 1
    ;;
esac
