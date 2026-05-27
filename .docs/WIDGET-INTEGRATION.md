# Website Widget Integration — Technical Spec

> **Status:** NOT IMPLEMENTED (planned Phase 2)  
> **Parent context:** [AGENT-CONTEXT.md](./AGENT-CONTEXT.md) §12  
> **Chat backend:** `https://agent.remont-gazon.ru` (Open WebUI + Ollama `truck-service`)

---

## 1. Objective

Render a **floating chat assistant** on the business website:

- **Collapsed:** circular/rounded button, fixed `bottom-right`
- **Expanded:** chat panel (~380–420px × 560–640px), same corner
- **Behavior:** identical intake flow as production agent (Russian, `ЗАЯВКА СОЗДАНА` line)

**Non-goals for MVP:**

- Custom LLM fine-tuning
- Multi-tenant auth
- Payment integration

---

## 2. Target Sites (confirm with owner)

| Domain | Hestia vhost | Notes |
|--------|--------------|-------|
| `ons.remont-gazon.ru` | exists | likely main site candidate |
| `remont-gazon.ru` | verify DNS | may redirect |
| `gazonbaza.ru` | exists | unrelated brand? confirm |

Agent must confirm which `public_html` receives the embed snippet.

---

## 3. Architecture Options

```text
┌─────────────────────────────────────┐
│  Parent site (remont-gazon.ru)      │
│  ┌──────────────┐                   │
│  │ widget.js    │ launcher UI       │
│  └──────┬───────┘                   │
│         │ iframe src                │
│         ▼                           │
│  https://agent.remont-gazon.ru      │
└─────────────────────────────────────┘
         │
         ▼ (existing stack)
    Open WebUI → Ollama truck-service
```

---

## 4. Recommended Approach: iframe + launcher

### 4.1 Files to add (repository)

```text
embed/
  widget.css
  widget.js
  snippet.html      # install instructions
```

### 4.2 `widget.js` behavior (spec)

```javascript
// Pseudocode contract
const CONFIG = {
  chatUrl: 'https://agent.remont-gazon.ru',  // or public chat path
  position: 'bottom-right',
  zIndex: 2147483000,
};

// States: COLLAPSED | OPEN
// toggle on launcher click
// optional: close on overlay click outside panel
// optional: postMessage height to parent
```

### 4.3 `widget.css` (spec)

```css
.aiserver-launcher {
  position: fixed;
  bottom: 24px;
  right: 24px;
  width: 56px;
  height: 56px;
  border-radius: 50%;
  z-index: 2147483000;
}
.aiserver-panel {
  position: fixed;
  bottom: 96px;
  right: 24px;
  width: min(420px, calc(100vw - 32px));
  height: min(620px, calc(100vh - 120px));
  border: 0;
  border-radius: 12px;
  box-shadow: 0 8px 32px rgba(0,0,0,.2);
  display: none;
}
.aiserver-panel.is-open { display: block; }
```

### 4.4 Install on Hestia site

Insert before `</body>` on target domain:

```html
<link rel="stylesheet" href="https://agent.remont-gazon.ru/embed/widget.css">
<script src="https://agent.remont-gazon.ru/embed/widget.js" defer></script>
```

**Serving static files:** add Nginx location on agent vhost:

```nginx
location /embed/ {
    alias /root/AIServer/embed/;
    add_header Cache-Control "public, max-age=3600";
    add_header Access-Control-Allow-Origin "*";
}
```

Reload: `nginx -t && systemctl reload nginx`.

---

## 5. Security Headers

### 5.1 Allow framing from parent domains

On `agent.remont-gazon.ru` server block:

```nginx
add_header Content-Security-Policy "frame-ancestors 'self' https://ons.remont-gazon.ru https://remont-gazon.ru https://www.remont-gazon.ru" always;
```

Remove or override `X-Frame-Options: DENY` if present.

### 5.2 Do NOT expose in client

- `WEBUI_ADMIN_PASSWORD`
- `WEBUI_SECRET_KEY`
- `N8N_*` credentials

---

## 6. Authentication Gap (blocker)

Current prod: `WEBUI_ENABLE_SIGNUP=false`, admin login required.

**iframe to `/` will show login form** unless agent configures one of:

| Approach | Effort |
|----------|--------|
| Open WebUI public/shared chat URL | Low — if supported in v0.9.5 |
| API key in widget (server-side proxy) | Medium |
| Dedicated guest user + auto-login token | Medium — security review |
| `ENABLE_SIGNUP=true` + rate limit | High risk — spam |

**Required research:** Open WebUI env vars:

- `ENABLE_PUBLIC_CHAT` / similar  
- Shared conversation links  
- `WEBUI_AUTH=false` (dev only — **never prod without reverse proxy auth**)

---

## 7. Testing Checklist

```bash
# Headers
curl -sI https://agent.remont-gazon.ru | grep -iE 'frame|content-security'

# Embed page loads
curl -sI https://agent.remont-gazon.ru/embed/widget.js

# Manual
# - Desktop Chrome/Firefox: open parent site, launcher visible
# - Expand chat, send Russian message, complete intake
# - Verify ЗАЯВКА СОЗДАНА line
# - Mobile Safari viewport
```

---

## 8. Alternative: same-origin proxy (advanced)

```nginx
# On ons.remont-gazon.ru vhost only
location /assistant/ {
    proxy_pass http://127.0.0.1:3000/;
    # same proxy headers as zz-agent-webui.conf
}
```

Widget iframe: `src="/assistant/"` → same origin, simpler cookies.

**Risk:** Hestia template conflicts — test on staging first.

---

## 9. Deliverables for PR

- [ ] `embed/widget.js`, `embed/widget.css`
- [ ] Nginx: `/embed/` static + CSP `frame-ancestors`
- [ ] Open WebUI config for anonymous/public chat (document env vars set)
- [ ] `.docs/WIDGET-INTEGRATION.md` updated with final URLs
- [ ] Screenshot / short screen recording in PR description
- [ ] No secrets in committed files

---

*Blocked on: public/guest chat policy in Open WebUI — resolve before iframe MVP.*
