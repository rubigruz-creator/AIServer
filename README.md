# AIServer — ИИ-агент грузового автосервиса

Бесплатный стек на VPS: **Ollama** + **Open WebUI** + системный промпт «администратор автосервиса».

**Продакшен:** https://agent.remont-gazon.ru

---

## Быстрый старт

```bash
# 1. Секреты
cp .env.example .env && nano .env

# 2. Запуск (на сервере, из каталога AIServer)
chmod +x scripts/*.sh
./scripts/fix-line-endings.sh   # если копировали с Windows
./scripts/stack.sh start

# 3. Модель
./scripts/model-pull.sh qwen2.5:1.5b
./scripts/model-create.sh qwen2.5:1.5b
```

---

## Структура

```
AIServer/
├── .docs/
│   ├── PROJECT.md              ← для людей (история, ошибки)
│   ├── AGENT-CONTEXT.md        ← для ИИ-агентов (техспека)
│   ├── WIDGET-INTEGRATION.md   ← виджет: архитектура, деплой
│   ├── WIDGET-SITES.md         ← код для сайтов (multisite)
│   └── INTAKE-STORAGE.md       ← диалоги, заявки, админ, webhook
├── services/intake-api/        ← SQLite + API + /intake/admin
├── embed/                      ← widget + public chat UI
│   ├── widget.js, widget.css
│   ├── chat.html, chat.js, chat.css
│   └── snippet.html
├── docker-compose.yml
├── .env.example
├── prompts/truck-service-system.txt
├── ollama/Modelfile.params
├── nginx/hestia-zz-agent-webui.conf.example
└── scripts/
```

---

## Скрипты

| Команда | Действие |
|---------|----------|
| `./scripts/stack.sh start\|stop\|status` | Docker-стек |
| `./scripts/model-pull.sh` | Скачать модель |
| `./scripts/model-create.sh` | Собрать `truck-service` |
| `./scripts/model-warmup.sh` | Прогрев модели в RAM (быстрее первый ответ) |
| `./scripts/reset-webui.sh` | Сброс Open WebUI |
| `./scripts/widget-setup.sh` | Справка по настройке виджета |
| `./scripts/widget-deploy.sh` | Деплой виджета + intake-api на VPS |

---

## Требования

| RAM | Модель |
|-----|--------|
| ~2 GB | `qwen2.5:1.5b` |
| 6–8 GB | `qwen2.5:3b` |

Диск: от 15 GB свободного (образы Docker ~6 GB + модель ~1 GB).

---

## Документация

| Документ | Аудитория |
|----------|-----------|
| [.docs/PROJECT.md](.docs/PROJECT.md) | Люди: история, ошибки, Hestia, runbook |
| [.docs/AGENT-CONTEXT.md](.docs/AGENT-CONTEXT.md) | **ИИ-агенты:** архитектура, инварианты, API |
| [.docs/WIDGET-SITES.md](.docs/WIDGET-SITES.md) | **Вставка виджета** на gortruck.ru, service-ref.ru, refmontaj.ru и др. |
| [.docs/WIDGET-INTEGRATION.md](.docs/WIDGET-INTEGRATION.md) | Архитектура виджета, nginx, деплой |
| [.docs/INTAKE-STORAGE.md](.docs/INTAKE-STORAGE.md) | Хранение диалогов, админ, webhook для n8n/MAX |
| [.docs/GITHUB-PUBLISH.md](.docs/GITHUB-PUBLISH.md) | Публикация на GitHub (push, 403, безопасность) |

**GitHub:** https://github.com/rubigruz-creator/AIServer

---

## Nginx (HestiaCP)

На сервере с Hestia используйте шаблон:

`nginx/hestia-zz-agent-webui.conf.example` → `/etc/nginx/conf.d/zz-agent-webui.conf`

**Не делайте Rebuild** домена в Hestia — см. `.docs/PROJECT.md`.
