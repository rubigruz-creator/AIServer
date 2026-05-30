# AIServer — Technical Context for AI Agents

> **Audience:** autonomous coding agents continuing this repository.  
> **Human-oriented history:** see [PROJECT.md](./PROJECT.md).  
> **Production URL:** `https://agent.remont-gazon.ru`

---

## 0. Agent Instructions (read first)

1. **Do not break production invariants** listed in §8.
2. **Single source of truth for LLM behavior:** `prompts/truck-service-system.txt` → rebuild via `scripts/model-create.sh`.
3. **HestiaCP is present** on the VPS; Nginx for this domain is **not** managed only by repo files — live config is `/etc/nginx/conf.d/zz-agent-webui.conf`.
4. **Website widget:** implemented in `embed/`; multisite via CSP — see [WIDGET-SITES.md](./WIDGET-SITES.md), [WIDGET-INTEGRATION.md](./WIDGET-INTEGRATION.md). Intake: [INTAKE-STORAGE.md](./INTAKE-STORAGE.md).
5. Secrets live in `.env` (gitignored); never commit credentials.

---

## 1. System Purpose

| Property | Value |
|----------|-------|
| Domain | Truck service (heavy vehicles) appointment intake |
| Language | Russian only (`ru-RU`) |
| Billing | No cloud LLM APIs; local inference via Ollama |
| UI | Open WebUI (`ghcr.io/open-webui/open-webui:main`) |
| Custom model name | `truck-service` (Ollama) |
| Base weights (prod) | `qwen2.5:1.5b` (RAM-constrained VPS ~2GB) |

### Output Contract (machine-parseable)

When all 6 slots are collected and confirmed, the model MUST emit **exactly one line**, no markdown, no extra text:

```text
ЗАЯВКА СОЗДАНА: Имя: {name}, Телефон: {phone}, Авто: {vehicle_make_model_and_plate}, Услуга: {service_type}, Время: {preferred_time}
```

**Slots (strict order in dialog):**

1. Vehicle make/model  
2. Service type (repair, maintenance, diagnostics, etc.)  
3. Preferred visit time  
4. Customer name  
5. Phone  
6. License plate (RU: госномер)

Downstream automation (n8n, not implemented) should regex-parse this line.

---

## 2. Runtime Topology

```text
Internet
  │
  ▼
DNS A: agent.remont-gazon.ru → 90.156.171.36
  │
  ▼
nginx (host, /etc/nginx/conf.d/zz-agent-webui.conf)
  listen VPS_IP:443 ssl
  /              → 127.0.0.1:3000 (Open WebUI admin)
  /embed/        → static /var/www/aiserver/embed + /embed/ollama/chat → Ollama
  /intake/       → 127.0.0.1:3101 (intake-api)
  │
  ├─► open-webui (127.0.0.1:3000→8080)
  ├─► ollama (127.0.0.1:11434) — truck-service:latest
  └─► intake-api (127.0.0.1:3101) — SQLite dialogs

Parent sites (iframe): gortruck.ru, service-ref.ru, refmontaj.ru,
  ons.remont-gazon.ru, remont-gazon.ru — see nginx/frame-ancestors.snippet
```

| Endpoint | Bind | Exposure |
|----------|------|----------|
| Nginx :443/:80 | `90.156.171.36` | Public |
| Open WebUI | `127.0.0.1:3000` | Localhost only |
| Ollama API | `127.0.0.1:11434` | Localhost only |
| n8n (optional) | `127.0.0.1:5678` | Localhost only; profile `automation` |

**Compose project name on server:** typically `aiserver` → volumes `aiserver_ollama_data`, `aiserver_open_webui_data`.

---

## 3. Repository Map

| Path | Responsibility |
|------|----------------|
| `docker-compose.yml` | Service definitions, env injection, volume names |
| `.env` / `.env.example` | Secrets and tunables (DOMAIN, admin, signup flags) |
| `prompts/truck-service-system.txt` | SYSTEM prompt text for Ollama model build |
| `ollama/Modelfile.params` | `PARAMETER_*`, `TEMPLATE` for Qwen chat format |
| `scripts/common.sh` | `require_ollama`, `default_base_model` → `qwen2.5:1.5b` |
| `scripts/model-create.sh` | Assembles Modelfile, `docker cp`, `ollama create truck-service` |
| `scripts/model-pull.sh` | `docker exec ollama ollama pull` |
| `scripts/stack.sh` | `start\|stop\|status` for compose |
| `scripts/reset-webui.sh` | Drops `*open_webui_data` volume, recreates stack |
| `scripts/fix-line-endings.sh` | `dos2unix` after Windows deploy |
| `nginx/hestia-zz-agent-webui.conf.example` | Reference for production Nginx (must use VPS IP in `listen`) |
| `nginx/n8n.conf` | Optional; only if n8n subdomain enabled |
| `.docs/PROJECT.md` | Human runbook + incident log |
| `.docs/AGENT-CONTEXT.md` | This file |

**Removed (do not reintroduce without reason):**

- `ollama/Modelfile.truck-service` — duplicate of prompt; use `model-create.sh` pipeline  
- `nginx/open-webui.conf` — incompatible with Hestia default vhost selection  
- `scripts/stack-start.sh`, `stack-stop.sh` — merged into `stack.sh`

---

## 4. Docker Compose Contract

### Services

| Service | Image | Profile | Host port |
|---------|-------|---------|-----------|
| `ollama` | `ollama/ollama:latest` | default | `127.0.0.1:11434` |
| `open-webui` | `ghcr.io/open-webui/open-webui:main` | default | `127.0.0.1:3000→8080` |
| `intake-api` | build `./services/intake-api` | default | `127.0.0.1:3101→3100` |
| `n8n` | `n8nio/n8n:latest` | `automation` | `127.0.0.1:5678` |

### Critical `open-webui` environment variables

| Variable | Source | Effect |
|----------|--------|--------|
| `OLLAMA_BASE_URL` | hardcoded `http://ollama:11434` | Backend LLM |
| `WEBUI_SECRET_KEY` | `.env` | Session crypto |
| `WEBUI_URL` | `https://${DOMAIN}` | Public URL; prevents http redirects behind TLS proxy |
| `ENABLE_SIGNUP` | `WEBUI_ENABLE_SIGNUP` | Must be `false` in prod |
| `ENABLE_PERSISTENT_CONFIG` | `.env` | `false` = env overrides DB on start |
| `DEFAULT_MODELS` | `OLLAMA_DEFAULT_MODEL` | Default: `truck-service` |
| `WEBUI_ADMIN_EMAIL/PASSWORD` | `.env` | Bootstrap admin if DB empty |

### Volumes (persistent)

```text
ollama_data      → /root/.ollama inside ollama container
open_webui_data  → /app/backend/data (SQLite, users, chats, PersistentConfig)
n8n_data         → /home/node/.n8n
```

---

## 5. Model Build Pipeline

```bash
# Preconditions: container `ollama` running
./scripts/model-pull.sh [base_model]      # default: qwen2.5:1.5b
./scripts/model-create.sh [base_model]    # creates truck-service
```

**Build algorithm (`model-create.sh`):**

1. `FROM {base_model}`  
2. `SYSTEM """` + contents of `prompts/truck-service-system.txt` + `"""`  
3. Append `ollama/Modelfile.params`  
4. Write `/tmp/Modelfile.truck-service.build` on host → `docker cp` → `ollama create truck-service -f ...`

**After prompt edits:** always rerun `model-create.sh`; Open WebUI may also allow UI-level system prompt override (redundant).

---

## 6. Authentication & Access Model

| Surface | Auth |
|---------|------|
| `https://agent.remont-gazon.ru` | Open WebUI login; signup disabled |
| Ollama API | No auth on localhost |
| Admin bootstrap | `WEBUI_ADMIN_*` when DB empty |

**User-facing rule:** use **Sign in**, not Sign up (`WEBUI_ENABLE_SIGNUP=false`).

**Recovery:** `./scripts/reset-webui.sh` wipes WebUI DB; admin recreated from env on next start if DB empty.

---

## 7. Production Host Facts (immutable unless migrated)

| Key | Value |
|-----|-------|
| OS | Ubuntu 24.04 |
| VPS IP | `90.156.171.36` |
| FQDN | `agent.remont-gazon.ru` |
| Control panel | HestiaCP, system user `rubi` |
| App deploy path | `/root/AIServer` |
| Active Nginx site config | `/etc/nginx/conf.d/zz-agent-webui.conf` |
| TLS cert (LE) | `/etc/letsencrypt/live/agent.remont-gazon.ru/` |
| TLS cert (Hestia copy) | `/home/rubi/conf/web/agent.remont-gazon.ru/ssl/*.pem` |
| Main website (separate) | `ons.remont-gazon.ru`, `gazonbaza.ru` on same host |

---

## 8. Invariants (DO NOT violate)

1. **Bind Ollama/WebUI to 127.0.0.1 only** in `docker-compose.yml` unless adding new security layer.
2. **Nginx must `listen <VPS_IP>:443`** on Hestia — generic `listen 443` was overridden by panel vhosts → static "Coming Soon" page.
3. **Do not enable Hestia "Rebuild"** for `agent.remont-gazon.ru` without re-applying `zz-agent-webui.conf` and disabling conflicting `domains/agent.*.conf` symlinks.
4. **Do not add `nginx.ssl.conf_custom` with bare `proxy_pass`** — Hestia includes custom at `server` level → `proxy_pass directive is not allowed here`.
5. **Do not add duplicate `location /`** in Hestia custom snippets.
6. **Keep `WEBUI_URL=https://${DOMAIN}`** when TLS terminates at Nginx.
7. **Prompt changes** require `model-create.sh` rerun (not hot-reload).
8. **Disk budget:** ~6GB Docker images + ~1GB/model; VPS disk 29GB — prune regularly.

---

## 9. Failure Mode Matrix

| Symptom | Root cause | Fix |
|---------|------------|-----|
| `bash\r: No such file` | CRLF scripts | `fix-line-endings.sh` |
| `no space left on device` | Disk full / failed layer extract | `docker system prune -af`, pull images sequentially |
| Exit 137 / WebUI restart | OOM | swap, `qwen2.5:1.5b`, `model-stop.sh` |
| `no configuration file` in compose dir | Wrong cwd | `cd ~/AIServer` |
| `No such container: ollama` | Stack down | `stack.sh start` |
| Permission denied on signup | `ENABLE_SIGNUP=false` | Sign in as admin |
| 500 on signup | Corrupt WebUI DB | `reset-webui.sh` |
| `ERR_CONNECTION_REFUSED` localhost:3000 | No SSH tunnel (pre-HTTPS) | Use public HTTPS URL |
| HTML "Coming Soon" on HTTPS | Wrong nginx vhost | `zz-agent-webui.conf` + IP listen |
| LE 404 on `/.well-known/` | Proxy swallowed ACME | certbot webroot to `public_html` |
| `duplicate location /` | Hestia + custom both define `/` | Use standalone zz-agent conf |
| `nginx.ssl.conf_letsencrypt` missing | File deleted | `touch nginx.conf_letsencrypt` |
| `conflicting server name` | Duplicate conf.d files | Remove `agent-remont-gazon.conf` |

---

## 10. Operational Commands

```bash
cd /root/AIServer

# Lifecycle
./scripts/stack.sh {start|stop|status}
docker compose logs -f open-webui

# Model
./scripts/model-pull.sh qwen2.5:1.5b
./scripts/model-create.sh qwen2.5:1.5b
docker exec ollama ollama list

# Health
curl -s -o /dev/null -w "%{http_code}\n" http://127.0.0.1:3000
curl -sI https://agent.remont-gazon.ru

# Nginx
nginx -t && systemctl reload nginx

# Disk
df -h && docker system df
```

---

## 11. Optional Subsystems (not deployed)

### n8n (`docker compose --profile automation up -d`)

- Parse assistant message for substring `ЗАЯВКА СОЗДАНА:`  
- Trigger: Telegram / email  
- Config stub: `nginx/n8n.conf`, `.env` `N8N_*`

### GPU

Uncomment `deploy.resources.reservations` in `ollama` service if NVIDIA available.

---

## 12. Website Floating Chat Widget (IMPLEMENTED)

**Status:** Production. Static assets in `embed/`; chat via `/embed/ollama/chat`; logs in `intake-api`.

**Multisite:** same snippet on all parent domains; nginx `frame-ancestors` whitelist — [WIDGET-SITES.md](./WIDGET-SITES.md).

**Backend:** `https://agent.remont-gazon.ru` → Ollama `truck-service` + intake SQLite.

### 12.1 Constraints

| Constraint | Implication |
|------------|-------------|
| WebUI auth enabled | Anonymous iframe may show login wall |
| `X-Frame-Options` / CSP | Parent site must be allowed to frame agent subdomain |
| Cross-origin | `agent.remont-gazon.ru` ≠ `www.remont-gazon.ru` → third-party cookies/session issues |
| Signup disabled | Need guest/public chat strategy |
| RAM | No second model instance; reuse same Ollama |

### 12.2 Implementation Options (ranked)

#### Option A — iframe embed (fastest MVP)

```html
<!-- On parent site before </body> -->
<div id="aiserver-widget">
  <button id="aiserver-launcher" aria-label="Открыть чат">💬</button>
  <iframe id="aiserver-frame" src="https://agent.remont-gazon.ru" hidden></iframe>
</div>
```

CSS: fixed `bottom:24px; right:24px`; iframe `width:400px; height:600px; border:0; border-radius:12px; box-shadow:...`.

**Agent tasks:**

1. Verify Open WebUI allows embedding: Admin → Settings → check iframe/CORS; set `WEBUI_URL` correctly.  
2. Nginx on agent subdomain: ensure no `X-Frame-Options DENY` (or set `Content-Security-Policy frame-ancestors https://remont-gazon.ru https://*.remont-gazon.ru`).  
3. Add `frame-ancestors` in `zz-agent-webui.conf` `location /` if needed:

```nginx
add_header Content-Security-Policy "frame-ancestors 'self' https://remont-gazon.ru https://www.remont-gazon.ru https://ons.remont-gazon.ru" always;
```

4. **Auth blocker:** enable Open WebUI **public/shared chat** or dedicated guest workspace if available in v0.9.x; else iframe shows login.

**Research required:** Open WebUI docs for `ENABLE_PUBLIC_*`, shared chat links, API keys for embedded anonymous use.

#### Option B — Open WebUI shared link / embed URL

Some versions expose `/c/{id}` public chat URLs. Agent should:

- Create a read-only or public chat template bound to `truck-service`.  
- iframe `src` = public URL instead of root.

#### Option C — Thin custom widget → Ollama API (not recommended)

Would require exposing API publicly or building BFF on same domain — breaks current security model.

#### Option D — Reverse proxy path on main site

`https://remont-gazon.ru/assistant/` → proxy to `127.0.0.1:3000` on VPS.

**Pros:** same-origin cookies. **Cons:** Hestia vhost complexity; same IP listen issues.

### 12.3 Recommended delivery plan for next agent

```text
Phase 2a — Discovery (1 session)
  - Read Open WebUI v0.9.5 env docs: public chat, API keys, iframe policy
  - curl -I https://agent.remont-gazon.ru | grep -i frame
  - Confirm target parent domain(s)

Phase 2b — MVP iframe widget (repo: /widget or /embed)
  - Add static assets: widget.js, widget.css (launcher + panel)
  - Document install snippet for site `public_html`
  - Nginx CSP frame-ancestors patch on agent vhost

Phase 2c — Authless guest flow
  - Configure WebUI for anonymous session OR service account token in widget
  - Never expose WEBUI_ADMIN credentials client-side

Phase 2d — Polish
  - Mobile responsive, z-index, locale ru-RU
  - Optional: postMessage resize between iframe and parent
  - Optional: n8n hook on ЗАЯВКА СОЗДАНА
```

### 12.4 Suggested repo layout (to create)

```text
AIServer/
  embed/
    widget.js          # launcher UI, toggle iframe
    widget.css
    chat.html, chat.js, chat.css   # public chat UI (API via nginx)
    snippet.html       # copy-paste snippet for Hestia public_html
  nginx/
    widget-api-key.conf.example
  .docs/
    WIDGET-INTEGRATION.md   # step-by-step for site owner
```

**Status:** created in Phase 2b.

### 12.5 Parent site install snippet (target)

```html
<link rel="stylesheet" href="https://agent.remont-gazon.ru/static/widget.css">
<script src="https://agent.remont-gazon.ru/static/widget.js" defer></script>
```

**Note:** requires serving static files from agent subdomain (Nginx `location /static/widget/` alias or Open WebUI static mount). Alternative: host widget assets on main CDN/domain.

### 12.6 Acceptance criteria

- [x] Launcher + iframe chat (`embed/`)
- [x] `truck-service` + intake storage
- [x] CSP for gortruck.ru, service-ref.ru, refmontaj.ru, remont-gazon.ru, ons
- [ ] Snippet on each target site (owner paste)
- [ ] VPS nginx reloaded after CSP update

---

## 13. Environment Schema (`.env`)

| Key | Type | Required | Default in example |
|-----|------|----------|-------------------|
| `DOMAIN` | string FQDN | yes | `agent.remont-gazon.ru` |
| `LETSENCRYPT_EMAIL` | email | yes | — |
| `WEBUI_SECRET_KEY` | hex 64 | yes | placeholder |
| `OLLAMA_DEFAULT_MODEL` | string | yes | `truck-service` |
| `WEBUI_ENABLE_SIGNUP` | bool string | yes | `false` |
| `WEBUI_DEFAULT_LOCALE` | string | no | `ru-RU` |
| `WEBUI_ADMIN_EMAIL` | string | bootstrap | — |
| `WEBUI_ADMIN_PASSWORD` | string | bootstrap | — |
| `WEBUI_ADMIN_NAME` | string | no | `Администратор` |
| `ENABLE_PERSISTENT_CONFIG` | bool string | no | `false` |
| `N8N_*` | various | if profile automation | — |
| `OLLAMA_KEEP_ALIVE` | duration | no | `30m` |
| `INTAKE_ADMIN_*` | string | intake admin | — |
| `INTAKE_WEBHOOK_URL` | URL | optional n8n/MAX | — |
| `TZ` | timezone | no | `Europe/Moscow` |

---

## 14. Extension Hooks

| Hook | Location | Use |
|------|----------|-----|
| System prompt | `prompts/truck-service-system.txt` | Dialog policy |
| Model params | `ollama/Modelfile.params` | temperature, context window |
| Default model | `.env` `OLLAMA_DEFAULT_MODEL` | WebUI default selection |
| Public URL | `WEBUI_URL`, `DOMAIN` | Links, redirects, embed |
| Edge proxy | `/etc/nginx/conf.d/zz-agent-webui.conf` | TLS, CSP, timeouts |
| Automation | n8n profile | Post-process `ЗАЯВКА СОЗДАНА` |

---

## 15. Version Pins (as deployed)

| Component | Pin |
|-----------|-----|
| Open WebUI | `main` tag (reported v0.9.5 in logs) |
| Ollama | `latest` |
| Base model | `qwen2.5:1.5b` |
| Compose format | v3 (implicit) |

**Risk:** `main`/`latest` float — consider pinning digests for reproducibility in future PR.

---

## 16. Related Documents

| Document | Use case |
|----------|----------|
| [PROJECT.md](./PROJECT.md) | Human operator, incident history, Russian explanations |
| [../README.md](../README.md) | Quick start |
| `nginx/hestia-zz-agent-webui.conf.example` | Production proxy template |

---

*Last updated: multisite widget (gortruck, service-ref, refmontaj), intake-api, Ollama keep_alive.*
