# Публикация AIServer на GitHub

## Репозиторий

| Параметр | Значение |
|----------|----------|
| Аккаунт | **rubigruz-creator** |
| URL | https://github.com/rubigruz-creator/AIServer |
| Remote | `https://github.com/rubigruz-creator/AIServer.git` |
| Ветка | `main` |
| Секреты | `.env` в `.gitignore` — **не коммитится** |

---

## Первый push (если репозиторий ещё не создан)

1. Войдите на GitHub как **rubigruz-creator**.
2. **New repository** → Name: `AIServer` → **без** README/license (код уже локально).
3. Visibility: **Private** (рекомендуется).
4. В PowerShell:

```powershell
cd C:\Users\USER\AIServer
git remote -v
# должно быть: origin  https://github.com/rubigruz-creator/AIServer.git

git push -u origin main
```

Если спросит логин: `rubigruz-creator` + Personal Access Token (scope `repo`).

---

## Смена remote (если был ts-rubiroid)

```powershell
cd C:\Users\USER\AIServer
git remote set-url origin https://github.com/rubigruz-creator/AIServer.git
git push -u origin main
```

Старый репозиторий `ts-rubiroid/AIServer` можно удалить или оставить пустым — проект живёт в **rubigruz-creator**.

---

## После push

Проверка: https://github.com/rubigruz-creator/AIServer

На VPS:

```bash
cd /root/AIServer
git remote set-url origin https://github.com/rubigruz-creator/AIServer.git
git pull origin main
```

---

## Безопасность перед публикацией

- [ ] `git ls-files .env` — пустой вывод
- [ ] Нет реальных `sk-...`, паролей в коммитах
- [ ] Репозиторий **Private**, если код не для публики

---

## Дальше — виджет на prod

См. [.docs/WIDGET-INTEGRATION.md](./WIDGET-INTEGRATION.md). Для агента: SSH VPS + API key виджета.
