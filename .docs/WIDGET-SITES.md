# Виджет на нескольких сайтах

> **Один агент** — `https://agent.remont-gazon.ru`  
> **Один промпт** — модель `truck-service` (Ollama)  
> **Один код** — вставляется на каждый сайт одинаково

---

## Подключённые сайты

| Сайт | CSP в nginx | Статус snippet |
|------|-------------|----------------|
| [service-ref.ru](https://service-ref.ru) | ✅ | ✅ виджет работает (WordPress) |
| [gortruck.ru](https://gortruck.ru) | ✅ | вставить snippet |
| [refmontaj.ru](https://refmontaj.ru) | ✅ | вставить snippet |
| [ons.remont-gazon.ru](https://ons.remont-gazon.ru) | ✅ | вставить snippet |
| [remont-gazon.ru](https://remont-gazon.ru) | ✅ | по необходимости |

Диалоги со всех сайтов → https://agent.remont-gazon.ru/intake/admin  
(колонка `source_url` — с какого сайта открыли чат).

---

## Код для вставки на **любой** сайт

Перед `</body>` в шаблоне / `index.html` / footer CMS:

```html
<link rel="stylesheet" href="https://agent.remont-gazon.ru/embed/widget.css?v=2">
<script
  src="https://agent.remont-gazon.ru/embed/widget.js?v=2"
  defer
  data-chat-url="https://agent.remont-gazon.ru/embed/chat.html"
></script>
```

Готовый файл: [embed/snippet.html](../embed/snippet.html)

После обновления стилей виджета (Phase 3) увеличьте версию в URL: `?v=3`.

### Опционально — заголовок кнопки

Перед `widget.js`:

```html
<script>
  window.AIServerWidget = {
    title: 'Чат с администратором автосервиса',
  };
</script>
```

---

## DOM-ID виджета (изоляция от CSS темы)

WordPress и другие темы часто ломают классы `.aiserver-*`. Стили привязаны к ID:

| ID | Элемент |
|----|---------|
| `#aiserver-widget-root` | корневой контейнер |
| `#aiserver-widget-launcher` | круглая кнопка |
| `#aiserver-widget-panel-wrap` | обёртка панели чата |
| `#aiserver-widget-iframe` | iframe → `chat.html` |
| `#aiserver-widget-backdrop` | затемнение фона |

---

## VPS: nginx CSP (разрешить iframe с сайта)

Домены уже в шаблоне `nginx/hestia-zz-agent-webui.conf.example` и `nginx/frame-ancestors.snippet`.

Применить на сервере:

```bash
cd ~/AIServer
cp nginx/hestia-zz-agent-webui.conf.example /etc/nginx/conf.d/zz-agent-webui.conf
# или точечно sed, если правили вручную — см. историю в PROJECT.md
nginx -t && systemctl reload nginx
```

Проверка CSP для чата:

```bash
curl -sI https://agent.remont-gazon.ru/embed/chat.html | grep -i content-security
```

В ответе должны быть `service-ref.ru`, `gortruck.ru`, `refmontaj.ru` и др.

---

## VPS: публикация embed-статики

Файлы отдаются из `/var/www/aiserver/embed/` (не из `/root/AIServer`).

```bash
# из каталога с актуальными файлами
cp -f embed/widget.css embed/widget.js embed/chat.* /var/www/aiserver/embed/

# проверка новой версии CSS (ожидается число > 0):
grep -c aiserver-widget-launcher /var/www/aiserver/embed/widget.css
```

Если `curl .../main/embed/widget.css` с GitHub отдаёт старый файл, используйте URL с SHA коммита:

```bash
SHA=fdff713   # или актуальный: git rev-parse --short HEAD
curl -fsSL -o /var/www/aiserver/embed/widget.css \
  "https://raw.githubusercontent.com/rubigruz-creator/AIServer/${SHA}/embed/widget.css"
```

Полный деплой: `./scripts/widget-deploy.sh`

---

## Проверка после вставки кода

1. Сайт в **инкогнито** (Ctrl+F5) — кнопка справа внизу, круглая, зелёная.
2. Открыть чат → тестовое сообщение → ответ модели.
3. Intake admin — новая сессия с вашим `source_url`.

### Типичные проблемы

| Симптом | Решение |
|---------|---------|
| Пустой iframe, CSP в консоли без вашего домена | Обновить `zz-agent-webui.conf`, `nginx -t && reload` |
| Кнопка «расплющена» / не круглая | Старый `widget.css` — деплой с `#aiserver-widget-launcher`, `?v=2` |
| Старый CSP в браузере, curl на сервере OK | Инкогнито, Clear cache, Network → Disable cache |
| `Framing https://agent.remont-gazon.ru/` | Неверный snippet — нужен `data-chat-url=.../embed/chat.html` |

---

## Добавить ещё один сайт

1. Добавить `https://новый-сайт.ru` и `https://www.новый-сайт.ru` в оба `add_header Content-Security-Policy` в `nginx/hestia-zz-agent-webui.conf.example`.
2. Обновить `nginx/frame-ancestors.snippet` и таблицу выше.
3. `nginx -t && systemctl reload nginx` на VPS.
4. Вставить snippet на сайт.

---

## См. также

- [WIDGET-INTEGRATION.md](./WIDGET-INTEGRATION.md) — архитектура, скорость ответа
- [INTAKE-STORAGE.md](./INTAKE-STORAGE.md) — заявки, webhook
- [AGENT-PROMPT-WIDGET-UI.md](./AGENT-PROMPT-WIDGET-UI.md) — промпт для Phase 3 (анимация, UI)
