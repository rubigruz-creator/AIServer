#!/usr/bin/env bash
# Деплой embed-виджета на VPS (после git push на rubigruz-creator/AIServer).
# Запуск на сервере: cd /root/AIServer && ./scripts/widget-deploy.sh
#
# Опционально перед запуском (ключ не сохраняется в git):
#   export WIDGET_API_KEY='sk-...'
#   ./scripts/widget-deploy.sh

set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=common.sh
source "$SCRIPT_DIR/common.sh"

cd_project

GITHUB_REPO="${AISERVER_GITHUB_REPO:-https://github.com/rubigruz-creator/AIServer.git}"
NGINX_KEY_CONF="/etc/nginx/conf.d/aiserver-widget-api-key.conf"
NGINX_AGENT_CONF="/etc/nginx/conf.d/zz-agent-webui.conf"
VPS_IP="${AISERVER_VPS_IP:-90.156.171.36}"
EMBED_PUBLIC_DIR="/var/www/aiserver/embed"

echo "==> AIServer widget deploy"

# --- 1. Обновление кода ---
if [[ -d .git ]]; then
  echo "==> git pull..."
  git remote set-url origin "$GITHUB_REPO" 2>/dev/null || true
  if ! git pull origin main 2>/dev/null; then
    echo "    git pull не удался (приватный репо?). Обновите код вручную: git pull или scp embed/"
  fi
else
  echo "==> Нет .git — пропуск pull (ожидается код в $ROOT_DIR)"
fi

if [[ ! -f embed/widget.js ]]; then
  echo "Ошибка: нет embed/widget.js в $ROOT_DIR" >&2
  exit 1
fi

echo "==> Публикация embed-статики в $EMBED_PUBLIC_DIR"
mkdir -p "$EMBED_PUBLIC_DIR"
cp -f embed/* "$EMBED_PUBLIC_DIR"/
chmod 644 "$EMBED_PUBLIC_DIR"/*

# --- 2. API key для nginx ---
if [[ -n "${WIDGET_API_KEY:-}" ]]; then
  echo "==> Запись API key в $NGINX_KEY_CONF"
  cat >"$NGINX_KEY_CONF" <<EOF
map \$host \$widget_api_key {
    default "${WIDGET_API_KEY}";
}
EOF
  chmod 600 "$NGINX_KEY_CONF"
elif [[ -f "$NGINX_KEY_CONF" ]]; then
  if grep -q 'REPLACE_WITH_OPEN_WEBUI_API_KEY' "$NGINX_KEY_CONF" 2>/dev/null; then
    echo "Ошибка: в $NGINX_KEY_CONF остался placeholder." >&2
    echo "  export WIDGET_API_KEY='sk-...' && $0" >&2
    exit 1
  fi
  echo "==> Используется существующий $NGINX_KEY_CONF"
else
  echo "==> Копирование шаблона API key..."
  cp nginx/widget-api-key.conf.example "$NGINX_KEY_CONF"
  echo "Ошибка: задайте ключ: export WIDGET_API_KEY='sk-...' && $0" >&2
  exit 1
fi

# --- 3. Nginx agent vhost ---
echo "==> Обновление $NGINX_AGENT_CONF"
if [[ -f nginx/hestia-zz-agent-webui.conf.example ]]; then
  cp nginx/hestia-zz-agent-webui.conf.example "$NGINX_AGENT_CONF"
else
  echo "Ошибка: нет nginx/hestia-zz-agent-webui.conf.example" >&2
  exit 1
fi

# --- 4. Проверка и reload ---
echo "==> nginx -t"
nginx -t

echo "==> systemctl reload nginx"
systemctl reload nginx

# --- 5. Docker (без сброса данных) ---
if command -v docker >/dev/null 2>&1 && [[ -f docker-compose.yml ]]; then
  echo "==> docker compose build intake-api (если нужно)..."
  docker compose build intake-api 2>/dev/null || true
  echo "==> docker compose up -d (ollama, open-webui, intake-api)..."
  docker compose up -d ollama open-webui intake-api 2>/dev/null || docker compose up -d
fi

# --- 6. Проверки ---
echo ""
echo "==> Проверки (localhost / public)"
curl -s -o /dev/null -w "  embed/widget.js     → HTTP %{http_code}\n" \
  "https://agent.remont-gazon.ru/embed/widget.js" || true
curl -s -o /dev/null -w "  embed/chat.html     → HTTP %{http_code}\n" \
  "https://agent.remont-gazon.ru/embed/chat.html" || true
curl -s -o /dev/null -w "  Open WebUI local    → HTTP %{http_code}\n" \
  "http://127.0.0.1:3000/" || true
curl -s -o /dev/null -w "  intake-api health   → HTTP %{http_code}\n" \
  "http://127.0.0.1:3101/health" || true

echo ""
echo "==> Готово."
echo "  1) Откройте https://agent.remont-gazon.ru/embed/chat.html — тест чата"
echo "  2) Админ диалогов: https://agent.remont-gazon.ru/intake/admin (INTAKE_ADMIN_* в .env)"
echo "  3) Snippet для сайта: embed/snippet.html"
echo "  4) Если API 401 — проверьте widget user и sk-... в $NGINX_KEY_CONF"
