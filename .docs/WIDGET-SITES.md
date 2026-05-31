# Виджет на нескольких сайтах

> **Один агент** — `https://agent.remont-gazon.ru`  
> **Один промпт** — модель `truck-service` (Ollama)  
> **Один код** — вставляется на каждый сайт одинаково

---

## Подключённые сайты

| Сайт | Домен в nginx CSP |
|------|-------------------|
| [ons.remont-gazon.ru](https://ons.remont-gazon.ru) | `ons.remont-gazon.ru` |
| [remont-gazon.ru](https://remont-gazon.ru) | `remont-gazon.ru`, `www.remont-gazon.ru` |
| [gortruck.ru](https://gortruck.ru) | `gortruck.ru`, `www.gortruck.ru` |
| [service-ref.ru](https://service-ref.ru) | `service-ref.ru`, `www.service-ref.ru` |
| [refmontaj.ru](https://refmontaj.ru) | `refmontaj.ru`, `www.refmontaj.ru` |

Диалоги со всех сайтов попадают в одну админку:  
https://agent.remont-gazon.ru/intake/admin  
(в таблице видно `source_url` — с какого сайта открыли чат).

---

## Код для вставки на **любой** из сайтов

Вставьте **перед `</body>`** в шаблоне / `index.html` / footer CMS:

```html
<link rel="stylesheet" href="https://agent.remont-gazon.ru/embed/widget.css?v=2">
<script
  src="https://agent.remont-gazon.ru/embed/widget.js?v=2"
  defer
  data-chat-url="https://agent.remont-gazon.ru/embed/chat.html"
></script>
```

Готовый файл: [embed/snippet.html](../embed/snippet.html)

### Опционально — свой заголовок кнопки

Перед `widget.js`:

```html
<script>
  window.AIServerWidget = {
    title: 'Чат с администратором',
  };
</script>
```

---

## Что сделать на VPS (один раз после добавления доменов)

На сервере `agent.remont-gazon.ru`:

```bash
cd ~/AIServer
# обновить конфиг (git pull или scp)
cp nginx/hestia-zz-agent-webui.conf.example /etc/nginx/conf.d/zz-agent-webui.conf
nginx -t && systemctl reload nginx
```

Список доменов в CSP: `nginx/frame-ancestors.snippet`.

Полный деплой виджета + intake: `./scripts/widget-deploy.sh`

---

## Проверка после вставки кода

1. Откройте сайт в **инкогнито** — внизу справа кнопка чата.
2. Отправьте тестовое сообщение.
3. В админке intake появится новая сессия с `source_url` вашего домена.

Если iframe пустой — откройте DevTools → Console: часто это **CSP frame-ancestors** (домен не добавлен в nginx) или блокировщик скриптов.

**Стили WordPress перебивают виджет:** обновите `widget.css` / `widget.js` на сервере (см. §6). Виджет изолирован под `#aiserver-widget-root` и ID `#aiserver-widget-launcher` и др. В snippet используйте `?v=2` для сброса кэша CSS.

```bash
# на сервере: заголовок embed-страницы
curl -sI https://agent.remont-gazon.ru/embed/chat.html | grep -i content-security
```

---

## Добавить ещё один сайт

1. Дописать `https://новый-сайт.ru` и `https://www.новый-сайт.ru` в `nginx/hestia-zz-agent-webui.conf.example` (оба `add_header Content-Security-Policy` в `location /embed/` и `location /`).
2. Обновить `nginx/frame-ancestors.snippet` и эту таблицу.
3. `nginx -t && systemctl reload nginx` на VPS.
4. Вставить тот же snippet на новый сайт.

---

## См. также

- [WIDGET-INTEGRATION.md](./WIDGET-INTEGRATION.md) — архитектура, деплой, скорость ответа
- [INTAKE-STORAGE.md](./INTAKE-STORAGE.md) — заявки и webhook
