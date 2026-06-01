# Цикл улучшения знаний из диалогов intake

## Регламент (рекомендуется раз в месяц)

1. Откройте [https://agent.remont-gazon.ru/intake/admin](https://agent.remont-gazon.ru/intake/admin) — диалоги **без заявки** с длинной перепиской.
2. Экспорт черновика:
   ```bash
   ./scripts/knowledge-feedback-export.sh
   ```
   Файл: `prompts/knowledge/feedback-export.json` (не коммитить PII в публичный git).
3. Выделите **повторяющиеся вопросы**, на которые бот ответил слабо или выдумал.
4. Добавьте пары вопрос–ответ в [`prompts/knowledge/faq.md`](../prompts/knowledge/faq.md).
5. Примените изменения:
   ```bash
   ./scripts/knowledge-index.sh
   ./scripts/model-create.sh
   ./scripts/widget-deploy.sh   # на VPS — обновить embed/chat.js
   ```

## API

`GET /intake/api/admin/feedback-report` (Basic auth) — JSON со списком диалогов без `ЗАЯВКА СОЗДАНА` и с ≥2 сообщениями пользователя.

## Правила безопасности

- Не копируйте в FAQ телефоны и ФИО из экспорта.
- Не дописывайте промпт автоматически ответами модели без ревью человека.
- Удаляйте `feedback-export.json` после обработки или держите в `.gitignore`.

## Связанные документы

- [KNOWLEDGE-PIPELINE.md](./KNOWLEDGE-PIPELINE.md) — скрейп, RAG, индексация
- [INTAKE-STORAGE.md](./INTAKE-STORAGE.md) — хранение диалогов
