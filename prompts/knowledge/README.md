# База знаний для модели truck-service

**Инструкция для администратора:** [.docs/KNOWLEDGE-RUNBOOK.md](../../.docs/KNOWLEDGE-RUNBOOK.md)

Файлы `*.md` в этой папке автоматически подключаются к SYSTEM при `./scripts/model-create.sh`
и индексируются в RAG через `./scripts/knowledge-index.sh`.

## Правила редактирования

1. Только проверенные факты; без устаревших акций и цен без источника.
2. Один файл — одна тема (`services.md`, `faq.md`, `sites-*.md`).
3. После правок на сервере:
   ```bash
   ./scripts/model-create.sh
   ./scripts/knowledge-index.sh
   ```

## Источники с сайтов

Черновики из скрейпера кладите в `sites-*.md`, проверяйте вручную, затем индексируйте.
