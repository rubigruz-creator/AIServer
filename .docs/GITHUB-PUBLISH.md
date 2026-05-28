# Публикация AIServer на GitHub

## Текущее состояние

| Параметр | Значение |
|----------|----------|
| Локальный репозиторий | готов, ветка `main` |
| Remote | `https://github.com/ts-rubiroid/AIServer.git` |
| Репозиторий на GitHub | **пустой** (первый push загрузит весь проект) |
| Секреты | `.env` в `.gitignore` — **не коммитится** |

Последний коммит с виджетом: `embed/`, nginx, `WIDGET-INTEGRATION.md`.

---

## Ошибка 403 при push

```
Permission to ts-rubiroid/AIServer.git denied to rubigruz-creator
```

Git на этом ПК авторизован как **rubigruz-creator**, а репозиторий принадлежит **ts-rubiroid**.

### Вариант A — войти как ts-rubiroid (рекомендуется)

1. GitHub → **Settings** → **Developer settings** → **Personal access tokens** → **Tokens (classic)** → **Generate new token**
   - Scope: `repo`
2. Windows: **Панель управления** → **Диспетчер учётных данных** → **Учётные данные Windows** → найдите `git:https://github.com` → **Удалить**
3. В PowerShell:

```powershell
cd C:\Users\USER\AIServer
git push -u origin main
```

При запросе логина: **Username** = `ts-rubiroid`, **Password** = токен (не пароль от аккаунта).

### Вариант B — SSH

```powershell
# Сгенерировать ключ (если нет)
ssh-keygen -t ed25519 -C "vm-tmpl@yandex.ru"

# Добавить публичный ключ в GitHub: ts-rubiroid → Settings → SSH keys
Get-Content $env:USERPROFILE\.ssh\id_ed25519.pub

cd C:\Users\USER\AIServer
git remote set-url origin git@github.com:ts-rubiroid/AIServer.git
git push -u origin main
```

### Вариант C — дать доступ rubigruz-creator

На GitHub: `ts-rubiroid/AIServer` → **Settings** → **Collaborators** → Add `rubigruz-creator` с правом **Write**.

---

## После успешного push

Проверьте: https://github.com/ts-rubiroid/AIServer

На VPS (для будущего деплоя виджета):

```bash
cd /root/AIServer
git clone https://github.com/ts-rubiroid/AIServer.git .   # если каталог пустой
# или
git pull origin main
```

---

## Перед публикацией (чеклист безопасности)

- [ ] Файл `.env` **не** в git: `git ls-files .env` — пустой вывод
- [ ] В коммитах нет реальных паролей и `sk-...` ключей
- [ ] Репозиторий **Private**, если не хотите открытый код (Settings → Danger zone → Change visibility)

---

## Следующий шаг — виджет на prod

После push пришлите агенту:

1. SSH на `root@90.156.171.36`
2. API key виджета (`sk-...`) или доступ админа Open WebUI
3. Домен сайта для snippet (`remont-gazon.ru` / `ons` / `www`)

См. [.docs/WIDGET-INTEGRATION.md](./WIDGET-INTEGRATION.md)
