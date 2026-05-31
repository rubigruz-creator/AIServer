# Промпт для агента: UI и анимация embed-виджета (Phase 3)

Скопируйте блок ниже в **новый чат Cursor (Agent mode)** как первое сообщение.

---

## Текст промпта

```
Ты работаешь в репозитории AIServer (GitHub: rubigruz-creator/AIServer).

## Контекст проекта

- Продакшен: https://agent.remont-gazon.ru
- На сайтах грузовых автосервисов встроен плавающий чат (launcher + iframe).
- Один snippet на все сайты; бэкенд общий: Ollama `truck-service`, intake-api для диалогов.
- Документация (прочитай перед правками):
  - .docs/AGENT-CONTEXT.md — архитектура, инварианты
  - .docs/WIDGET-INTEGRATION.md — embed, nginx, деплой
  - .docs/WIDGET-SITES.md — список сайтов, snippet, CSP

## Твоя задача (Phase 3)

Улучшить **внешний вид и заметность** виджета на родительских сайтах (WordPress и др.):
- анимация launcher (пульс, лёгкое покачивание, появление при скролле — на твоё усмотрение, без раздражения);
- визуальная привлекательность: современный вид, узнаваемость «чат с администратором»;
- мобильная вёрстка (уже есть @media — не сломать);
- опционально: badge «1», подсказка-тултип при первом визите, плавное открытие панели.

**Не менять** (если не согласовано явно):
- логику сбора заявки в `embed/chat.js` и промпт модели;
- URL API (`/embed/ollama/chat`, `/intake/api`);
- nginx CSP и список frame-ancestors;
- авторизацию intake admin.

## Файлы для правок

| Файл | Назначение |
|------|------------|
| `embed/widget.css` | Стили launcher, панели, backdrop — **основной фокус** |
| `embed/widget.js` | DOM, открытие/закрытие, опционально классы для анимации |
| `embed/chat.css` | UI внутри iframe (шапка чата, пузыри) — по желанию, согласованно по цветам |
| `embed/snippet.html` | После деплоя увеличить `?v=` (например `v=3`) для сброса кэша |

## Обязательная изоляция от CSS темы WordPress

Виджет уже использует ID (не переписывай на голые классы):
- `#aiserver-widget-root`
- `#aiserver-widget-launcher`
- `#aiserver-widget-panel-wrap`
- `#aiserver-widget-iframe`
- `#aiserver-widget-backdrop`

Все новые стили — только с этими ID. Для кнопки сохраняй `all: unset` + явные размеры, иначе тема снова сломает вид.

## Бренд (ориентир)

- Основной цвет: `#1a6b4a` (уже в CSS как `--aiserver-primary`)
- Аудитория: владельцы грузовиков, B2B-сервис, без «игрушечного» UI
- Язык интерфейса виджета: русский

## Деплой на VPS (после merge)

```bash
cp -f embed/widget.css embed/widget.js /var/www/aiserver/embed/
# проверка:
grep -c aiserver-widget-launcher /var/www/aiserver/embed/widget.css
```

Если `curl` с `raw.githubusercontent.com/.../main/` отдаёт старый файл — используй URL с коммитом:
`https://raw.githubusercontent.com/rubigruz-creator/AIServer/<SHA>/embed/widget.css`

Сайты для ручной проверки: https://service-ref.ru/ (уже с виджетом), gortruck.ru, refmontaj.ru.

## Критерии готовности

- [ ] Launcher заметен, анимация не мешает чтению страницы (prefers-reduced-motion учесть)
- [ ] На service-ref.ru (WordPress) стили темы не ломают кнопку и панель
- [ ] Панель плавно открывается/закрывается
- [ ] Мобильный вид без обрезания
- [ ] `snippet.html` и `.docs/WIDGET-SITES.md` обновлены (`?v=`)
- [ ] Кратко описано в `.docs/WIDGET-INTEGRATION.md` § Phase 3

## Стиль работы

- Минимальный diff, без лишних зависимостей (только CSS/JS, без React).
- Не коммить `.env` и секреты.
- Ответы пользователю на русском.
```

---

## После завершения работы агента

1. Владелец обновляет snippet на сайтах (`?v=3` или актуальная версия).
2. `cp embed/* /var/www/aiserver/embed/` на VPS.
3. Проверка в инкогнито на каждом сайте из [WIDGET-SITES.md](./WIDGET-SITES.md).
