# Website Widget Integration — Technical Spec

> **Status:** PRODUCTION (Phase 2 + intake + multisite)  
> **Parent context:** [AGENT-CONTEXT.md](./AGENT-CONTEXT.md) §12  
> **Backend:** `https://agent.remont-gazon.ru`  
> **Parent sites:** см. [WIDGET-SITES.md](./WIDGET-SITES.md)

---

## 1. Objective

Floating chat assistant on business websites:

- **Collapsed:** button bottom-right (`embed/widget.js`)
- **Expanded:** iframe → `embed/chat.html`
- **Behavior:** Russian intake dialog, line `ЗАЯВКА СОЗДАНА: ...`
- **Storage:** all messages → `intake-api` → `/intake/admin`

---

## 2. Architecture (current)

```text
gortruck.ru | service-ref.ru | refmontaj.ru | ons.remont-gazon.ru | …
  │
  ├─ widget.css, widget.js  (from agent.remont-gazon.ru/embed/)
  └─ iframe → agent.remont-gazon.ru/embed/chat.html
                    │
                    ├─ POST /embed/ollama/chat → Ollama :11434 (truck-service)
                    ├─ POST /intake/api/*      → intake-api :3101 (SQLite)
                    └─ CSP frame-ancestors     → only listed parent domains

agent.remont-gazon.ru/
  ├─ /              → Open WebUI :3000 (admin)
  ├─ /embed/        → static + ollama chat proxy
  └─ /intake/       → intake-api (admin UI + API)
```

**Chat path:** виджет использует **`/embed/ollama/chat`** (прямой прокси в Ollama), не Open WebUI API — обход бага WebUI v0.9.5 без `chat_id`.

---

## 3. Repository files

```text
embed/
  widget.js, widget.css     # launcher + panel
  chat.html, chat.js, chat.css
  snippet.html              # copy-paste для любого сайта

services/intake-api/        # диалоги, заявки, webhook

nginx/
  hestia-zz-agent-webui.conf.example
  frame-ancestors.snippet   # список доменов CSP
  widget-api-key.conf.example

scripts/
  widget-deploy.sh
  model-warmup.sh
```

---

## 4. Install on a website (owner)

**Один snippet для всех сайтов** — [embed/snippet.html](../embed/snippet.html) или [WIDGET-SITES.md](./WIDGET-SITES.md).

На VPS домен сайта должен быть в `frame-ancestors` (уже добавлены: gortruck.ru, service-ref.ru, refmontaj.ru, remont-gazon.ru, ons).

---

## 5. Response speed

| Mechanism | Where |
|-----------|--------|
| `OLLAMA_KEEP_ALIVE=30m` | `.env` + `docker-compose.yml` (service `ollama`) |
| `./scripts/model-warmup.sh` | after stack start / deploy |
| Browser warmup | `embed/chat.js` on chat open |
| Parallel intake | `logMessage` does not block Ollama |

---

## 6. VPS deploy

```bash
cd ~/AIServer
export WIDGET_API_KEY='sk-...'   # если ещё не в nginx
./scripts/fix-line-endings.sh
chmod +x scripts/*.sh
./scripts/widget-deploy.sh
```

После добавления доменов в nginx template:

```bash
cp nginx/hestia-zz-agent-webui.conf.example /etc/nginx/conf.d/zz-agent-webui.conf
nginx -t && systemctl reload nginx
cp -f embed/* /var/www/aiserver/embed/
```

Проверки:

```bash
curl -s http://127.0.0.1:3101/health
curl -fsSL https://agent.remont-gazon.ru/embed/chat.js | grep -c keep_alive   # ожидается 2
```

---

## 7. Security

| Rule | Status |
|------|--------|
| Ollama only on 127.0.0.1 | ✅ |
| API key for `/embed/api/` only on server (optional path) | ✅ |
| CSP `frame-ancestors` whitelist | ✅ see `frame-ancestors.snippet` |
| Intake admin — HTTP Basic | ✅ `/intake/admin` |

---

## 8. Acceptance criteria

- [x] Launcher + iframe chat
- [x] `truck-service` via `/embed/ollama/chat`
- [x] Intake storage + admin UI
- [x] Multisite CSP (gortruck, service-ref, refmontaj, remont-gazon, ons)
- [x] `keep_alive` + warmup
- [ ] Snippet pasted on all target sites (owner)
- [ ] nginx CSP deployed on VPS after domain list change
- [ ] E2E on each site: dialog → `ЗАЯВКА СОЗДАНА` in intake admin

---

## 9. Backlog (next)

- Widget UI: animation, visibility (Phase 3)
- Rate limit on public endpoints
- n8n / MAX via `INTAKE_WEBHOOK_URL`
- Optional per-site title via `AIServerWidget`

---

*Updated: multisite widget, intake-api, Ollama direct chat, keep_alive.*
