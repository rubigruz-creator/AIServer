# Website Widget Integration — Technical Spec

> **Status:** IMPLEMENTED (Phase 2a–2b)  
> **Parent context:** [AGENT-CONTEXT.md](./AGENT-CONTEXT.md) §12  
> **Chat backend:** `https://agent.remont-gazon.ru` (Open WebUI + Ollama `truck-service`)  
> **Target site:** `ons.remont-gazon.ru`

---

## 1. Objective

Render a **floating chat assistant** on the business website:

- **Collapsed:** circular button, fixed `bottom-right`
- **Expanded:** chat panel (~380–420px × 560–640px), same corner
- **Behavior:** identical intake flow as production agent (Russian, `ЗАЯВКА СОЗДАНА` line)

---

## 2. Phase 2a — Discovery (результаты)

| Вариант | Вердикт |
|---------|---------|
| iframe на `/` Open WebUI | ❌ Требует логин (`WEBUI_ENABLE_SIGNUP=false`) |
| Shared link `/s/{id}` | ❌ Read-only снимок, не новый диалог |
| `WEBUI_AUTH=false` | ❌ Только пустая БД; ломает prod-админа |
| **API key + nginx proxy + свой chat UI** | ✅ Выбран для MVP |

**Вывод:** публичный чат реализован через `embed/chat.html`, который вызывает `/embed/api/chat/completions`. Nginx добавляет `Authorization: Bearer <API key>` — ключ **не попадает в браузер**.

**Проверка заголовков (на сервере):**

```bash
curl -sI https://agent.remont-gazon.ru/embed/chat.html | grep -iE 'frame|content-security'
curl -sI https://agent.remont-gazon.ru/embed/widget.js | head -5
```

---

## 3. Архитектура (реализовано)

```text
ons.remont-gazon.ru
  widget.js / widget.css  ← загрузка с agent.remont-gazon.ru/embed/
  iframe → agent.remont-gazon.ru/embed/chat.html
                │
                POST /embed/api/chat/completions
                │
                ▼
         nginx (+ Bearer API key)
                │
                ▼
         Open WebUI :3000 → Ollama truck-service
```

---

## 4. Файлы в репозитории

```text
embed/
  widget.js       # launcher + iframe panel
  widget.css
  chat.html       # публичный чат (RU)
  chat.js         # streaming UI → /embed/api/
  chat.css
  snippet.html    # copy-paste для public_html

nginx/
  hestia-zz-agent-webui.conf.example  # + /embed/ + CSP
  widget-api-key.conf.example         # map $widget_api_key (на сервере)

scripts/widget-setup.sh               # пошаговая настройка на VPS
```

---

## 5. Развёртывание на VPS

### 5.1 Open WebUI — сервисный пользователь

1. Admin Panel → Users → **Add User**  
   - Email: `widget@remont-gazon.ru` (или из `.env` `WIDGET_SERVICE_EMAIL`)  
   - Role: `user`  
   - Permissions: workspace off; **Temporary Chat** on (Enforced — опционально)

2. Войти как widget-user → Settings → Account → **API Keys** → Create → скопировать `sk-...`

3. Перезапуск не обязателен; модель по умолчанию `truck-service` доступна через API.

### 5.2 Nginx

```bash
cd /root/AIServer

# Ключ API (не коммитить!)
cp nginx/widget-api-key.conf.example /etc/nginx/conf.d/aiserver-widget-api-key.conf
nano /etc/nginx/conf.d/aiserver-widget-api-key.conf   # sk-...

# Основной vhost (embed + CSP + API proxy)
cp nginx/hestia-zz-agent-webui.conf.example /etc/nginx/conf.d/zz-agent-webui.conf
# при смене IP/домена — sed как в PROJECT.md

nginx -t && systemctl reload nginx
```

### 5.3 Проверка

```bash
./scripts/widget-setup.sh          # напоминание шагов
curl -sI https://agent.remont-gazon.ru/embed/widget.js
# Открыть https://agent.remont-gazon.ru/embed/chat.html — диалог без логина
```

---

## 6. Установка на ons.remont-gazon.ru

Вставить **перед `</body>`** в `public_html` (Hestia: `/home/rubi/web/ons.remont-gazon.ru/public_html/`):

```html
<link rel="stylesheet" href="https://agent.remont-gazon.ru/embed/widget.css">
<script
  src="https://agent.remont-gazon.ru/embed/widget.js"
  defer
  data-chat-url="https://agent.remont-gazon.ru/embed/chat.html"
></script>
```

Полный пример: [embed/snippet.html](../embed/snippet.html)

---

## 7. Security

| Правило | Статус |
|---------|--------|
| API key только в nginx | ✅ |
| `WEBUI_ADMIN_PASSWORD` не в клиенте | ✅ |
| CSP `frame-ancestors` для ons.remont-gazon.ru | ✅ в nginx |
| Standalone admin login без изменений | ✅ `/` не затронут |

---

## 8. Acceptance criteria

- [x] Launcher bottom-right (widget.js/css)
- [x] Click expands chat without navigation
- [x] Chat uses `truck-service` via API
- [x] Mobile viewport (CSS `@media`)
- [x] CSP/frame-ancestors для ons.remont-gazon.ru
- [x] Nginx `/embed/` static + `/embed/api/` proxy
- [ ] **На prod:** создать widget-user + API key + reload nginx
- [ ] **На prod:** вставить snippet на ons.remont-gazon.ru
- [ ] E2E: полный диалог → строка `ЗАЯВКА СОЗДАНА: ...`

---

## 9. Phase 2c+ (backlog)

- Rate limiting на `/embed/api/`
- postMessage resize между iframe и родителем
- n8n hook на `ЗАЯВКА СОЗДАНА`
- Same-origin proxy `/assistant/` на ons (альтернатива iframe cookies)

---

*Обновлено: Phase 2a–2b реализованы в репозитории; деплой на VPS и snippet на сайт — ручные шаги §5–6.*
