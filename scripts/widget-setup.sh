#!/usr/bin/env bash
# Настройка публичного чата для embed-виджета (Phase 2).
# Запуск на VPS из каталога AIServer после деплоя embed/ и обновления nginx.

set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=common.sh
source "$SCRIPT_DIR/common.sh"

cd_project

echo "==> AIServer widget setup (Phase 2a–2b)"
echo ""
echo "Phase 2a — вывод discovery:"
echo "  • Open WebUI не имеет встроенного anonymous guest mode."
echo "  • /s/{share_id} — только read-only снимок, не интерактивный чат."
echo "  • WEBUI_AUTH=false работает только на пустой БД (не подходит для prod с админом)."
echo "  • Решение: сервисный пользователь + API key, ключ в nginx (не в JS)."
echo ""
echo "Phase 2b — шаги на сервере:"
echo ""
echo "1) Open WebUI → Admin Panel → Users → Add User"
echo "   Email: widget@remont-gazon.ru (или свой)"
echo "   Role: user"
echo "   Permissions: отключить workspace; включить Temporary Chat (Enforced — по желанию)"
echo ""
echo "2) Войти как widget-пользователь → Settings → Account → API Keys → Create"
echo "   Скопировать ключ (sk-...)"
echo ""
echo "3) Nginx API key:"
echo "   cp nginx/widget-api-key.conf.example /etc/nginx/conf.d/aiserver-widget-api-key.conf"
echo "   nano /etc/nginx/conf.d/aiserver-widget-api-key.conf   # вставить sk-..."
echo ""
echo "4) Обновить zz-agent-webui.conf из репозитория (embed locations + CSP):"
echo "   sed \"s/90.156.171.36/YOUR_IP/g\" nginx/hestia-zz-agent-webui.conf.example \\"
echo "     > /etc/nginx/conf.d/zz-agent-webui.conf"
echo "   nginx -t && systemctl reload nginx"
echo ""
echo "5) Проверки:"
echo "   curl -sI https://agent.remont-gazon.ru/embed/widget.js | head -5"
echo "   curl -sI https://agent.remont-gazon.ru/embed/chat.html | grep -i frame"
echo "   # POST /embed/api/chat/completions — только из chat.html (ключ добавляет nginx)"
echo ""
echo "6) Установка на ons.remont-gazon.ru — вставить перед </body>:"
echo "   см. embed/snippet.html"
echo "   Hestia: /home/rubi/web/ons.remont-gazon.ru/public_html/"
echo ""
echo "Готово. Standalone https://agent.remont-gazon.ru — вход админа без изменений."
