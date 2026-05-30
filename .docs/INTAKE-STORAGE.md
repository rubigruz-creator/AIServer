# Хранение диалогов и заявок (Intake API)

> **Сервис:** `intake-api` (Docker, порт `127.0.0.1:3101` → контейнер `3100`)  
> **Админ-страница:** https://agent.remont-gazon.ru/intake/admin  
> **БД:** SQLite в volume `intake_data` → `/data/intake.db`

---

## Что сохраняется

| Данные | Описание |
|--------|----------|
| `conversations` | Сессия чата (ID, время создания/обновления, источник, user-agent) |
| `messages` | Каждое сообщение: `user`, `assistant`, `system` + время |
| Поля заявки | При строке `ЗАЯВКА СОЗДАНА:` — телефон, авто, услуга, время и т.д. |

Виджет (`embed/chat.js`) при каждом сообщении вызывает API — история не теряется при закрытии вкладки.

**Несколько сайтов:** один intake на все домены; в `conversations.source_url` сохраняется сайт-источник (referrer). Список сайтов с виджетом: [WIDGET-SITES.md](./WIDGET-SITES.md).

---

## Настройка (.env)

```env
INTAKE_ADMIN_USER=admin
INTAKE_ADMIN_PASSWORD=сильный_пароль
# Опционально — webhook при новой заявке (n8n, MAX, любой HTTP POST):
INTAKE_WEBHOOK_URL=https://your-n8n.example/webhook/aiserver-applications
```

---

## Запуск на VPS

```bash
cd /root/AIServer
cp .env.example .env   # если ещё не настроен
nano .env              # INTAKE_ADMIN_PASSWORD=...

docker compose build intake-api
docker compose up -d intake-api ollama open-webui

# nginx (если обновился шаблон)
cp nginx/hestia-zz-agent-webui.conf.example /etc/nginx/conf.d/zz-agent-webui.conf
nginx -t && systemctl reload nginx

# embed на сайт
cp -f embed/* /var/www/aiserver/embed/
```

Проверка:

```bash
curl -s http://127.0.0.1:3101/health
# {"status":"ok"}
```

Откройте: https://agent.remont-gazon.ru/intake/admin (логин/пароль из `.env`).

---

## Подключение оповещений (n8n / MAX)

При появлении строки `ЗАЯВКА СОЗДАНА` сервис отправляет **POST** на `INTAKE_WEBHOOK_URL`:

```json
{
  "event": "application_created",
  "conversation_id": "sess_...",
  "created_at": "2026-05-28T08:00:00+00:00",
  "application_line": "ЗАЯВКА СОЗДАНА: ...",
  "client_name": "-",
  "client_phone": "+79001234567",
  "vehicle": "Газон Некст -",
  "service_type": "ТО",
  "visit_time": "сегодня"
}
```

### n8n

1. `docker compose --profile automation up -d`
2. Workflow: **Webhook** → парсинг JSON → Telegram / Email / Google Sheets.
3. В `.env`: `INTAKE_WEBHOOK_URL=https://n8n.example/webhook/...`

### MAX / другие мессенджеры

Добавьте узел в n8n с HTTP-запросом в API MAX или расширьте `app/notifications/` в репозитории (см. `dispatcher.py`).

---

## API (для разработки)

| Метод | Путь | Auth |
|-------|------|------|
| POST | `/intake/api/session` | нет |
| POST | `/intake/api/messages` | нет |
| GET | `/intake/admin` | Basic |
| GET | `/intake/api/admin/conversations` | Basic |
| GET | `/intake/api/admin/conversations/{id}` | Basic |

---

## Резервное копирование

```bash
docker run --rm -v aiserver_intake_data:/data -v $(pwd):/backup alpine \
  cp /data/intake.db /backup/intake-$(date +%F).db
```
