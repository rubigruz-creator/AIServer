# Website Widget Integration — Technical Spec

> **Status:** PRODUCTION (Phase 2 + Phase 3 UI + intake + multisite + CSS isolation)  
> **Parent context:** [AGENT-CONTEXT.md](./AGENT-CONTEXT.md) §12  
> **Sites:** [WIDGET-SITES.md](./WIDGET-SITES.md)

---

## 1. Objective

Floating chat assistant on truck-service websites:

- **Launcher:** `#aiserver-widget-launcher` (fixed bottom-right)
- **Panel:** iframe → `embed/chat.html`
- **Behavior:** Russian intake, line `ЗАЯВКА СОЗДАНА: ...`
- **Storage:** `intake-api` → `/intake/admin`

---

## 2. Architecture

```text
service-ref.ru | gortruck.ru | refmontaj.ru | ons.remont-gazon.ru | …
  │
  ├─ widget.css?v=3, widget.js?v=3  ← agent.remont-gazon.ru/embed/
  └─ iframe #aiserver-widget-iframe → /embed/chat.html
                    │
                    ├─ POST /intake/api/chat → intake-api (RAG) → Ollama :11434
                    ├─ POST /intake/api/*      → intake-api :3101
                    └─ CSP frame-ancestors   → whitelist only

agent.remont-gazon.ru/
  ├─ /              → Open WebUI :3000
  ├─ /embed/        → /var/www/aiserver/embed/ + ollama proxy
  └─ /intake/       → intake-api
```

**Chat:** `/intake/api/chat` (RAG + прокси Ollama). Резерв: `/embed/ollama/chat` (прямой Ollama без RAG).

**Static:** nginx `alias /var/www/aiserver/embed/`; `Access-Control-Allow-Origin: *` для CSS/JS.

---

## 3. Repository files

```text
embed/
  widget.js, widget.css   # launcher — ID-scoped CSS, WordPress-safe
  chat.html, chat.js, chat.css
  snippet.html            # ?v=3 cache buster

services/intake-api/

nginx/
  hestia-zz-agent-webui.conf.example
  frame-ancestors.snippet

scripts/
  widget-deploy.sh, model-warmup.sh, widget-setup.sh
```

---

## 4. CSS isolation (WordPress)

Темы переопределяют `button`, `div`. Решение:

- Корень: `#aiserver-widget-root`
- `all: unset` на launcher/panel/backdrop, затем явные стили
- Селекторы только по `#aiserver-widget-*`, не голые `.aiserver-launcher`

Коммит: `fix(embed): isolate widget CSS with unique IDs for WordPress`.

---

## 5. Install on websites

Один snippet — [embed/snippet.html](../embed/snippet.html).  
CSP на VPS должен включать домен сайта — см. [WIDGET-SITES.md](./WIDGET-SITES.md).

**Проверено в prod:** https://service-ref.ru/

---

## 6. Response speed

| Mechanism | Where |
|-----------|--------|
| `OLLAMA_KEEP_ALIVE=30m` | `docker-compose.yml` → service `ollama` |
| `./scripts/model-warmup.sh` | после start / deploy |
| Browser warmup | `embed/chat.js` (`keep_alive`, `num_predict: 1`) |
| Parallel intake | `logMessage` без await перед Ollama |

---

## 7. VPS deploy

```bash
cd ~/AIServer
./scripts/widget-deploy.sh
# или вручную:
cp -f embed/* /var/www/aiserver/embed/
cp nginx/hestia-zz-agent-webui.conf.example /etc/nginx/conf.d/zz-agent-webui.conf
nginx -t && systemctl reload nginx
```

Проверки:

```bash
curl -s http://127.0.0.1:3101/health
curl -fsSL https://agent.remont-gazon.ru/embed/widget.css | grep -c aiserver-widget-launcher
curl -sI https://agent.remont-gazon.ru/embed/chat.html | grep -i content-security
```

---

## 8. Security

| Rule | Status |
|------|--------|
| Ollama / WebUI / intake только localhost | ✅ |
| CSP `frame-ancestors` whitelist | ✅ |
| Intake admin HTTP Basic | ✅ |
| API key в nginx (для `/embed/api/`, опционально) | ✅ |

---

## 9. Acceptance criteria

- [x] Launcher + iframe chat
- [x] `/embed/ollama/chat` + intake
- [x] Multisite CSP (5 доменных групп)
- [x] `keep_alive` + warmup
- [x] CSS isolation (`#aiserver-widget-*`)
- [x] service-ref.ru — E2E виджет
- [ ] snippet на gortruck.ru, refmontaj.ru, ons (владелец)
- [x] Phase 3 UI (анимация, badge, hint, плавная панель)
- [ ] E2E заявка на каждом сайте в intake admin

---

## 10. Phase 3 — UI & animation (done)

Реализовано в `embed/widget.css`, `embed/widget.js` (`?v=3`).

| Функция | Реализация |
|---------|------------|
| Заметность launcher | Градиент 60×60px, пульсирующее кольцо (`::before`), лёгкое покачивание |
| Появление | Класс `is-revealed` после скролла >80px или через 1.2 с |
| Badge «1» | `#aiserver-widget-launcher-badge`, скрывается после первого открытия (`localStorage`) |
| Подсказка | `#aiserver-widget-hint` — «Нужна помощь?…», первый визит, закрытие × |
| Панель / backdrop | `opacity` + `transform`, без `display:none` — плавное открытие |
| Иконка | Чат ↔ крестик при открытии (`is-active`) |
| Доступность | `prefers-reduced-motion: reduce` — без анимаций, кнопка сразу видна |
| iframe UI | `chat.css` — градиент шапки в цвет бренда |

**Деплой:** `cp embed/widget.css embed/widget.js /var/www/aiserver/embed/`  
**Сайты:** обновить snippet на `?v=3` (см. [WIDGET-SITES.md](./WIDGET-SITES.md)).

Другой backlog: rate limit, n8n/MAX webhook, per-site `AIServerWidget.title`.

---

*Updated: May 2026 — multisite prod, intake, Ollama direct chat, WordPress CSS IDs.*
