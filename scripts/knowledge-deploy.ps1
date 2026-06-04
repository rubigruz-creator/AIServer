# Деплой файлов знаний с ПК на VPS + применение на сервере.
# Запуск из корня репозитория:
#   cd C:\Users\USER\AIServer
#   .\scripts\knowledge-deploy.ps1

$ErrorActionPreference = "Stop"
$Vps = "root@90.156.171.36"
$Remote = "/root/AIServer"
$Root = Split-Path $PSScriptRoot -Parent

Set-Location $Root

Write-Host "==> SCP (из $Root)..."
scp prompts/truck-service-system.txt "${Vps}:${Remote}/prompts/"
scp prompts/knowledge/faq.md "${Vps}:${Remote}/prompts/knowledge/"
scp prompts/knowledge/services.md "${Vps}:${Remote}/prompts/knowledge/"

Write-Host "==> VPS: rebuild intake-api + knowledge-apply..."
ssh $Vps "cd $Remote && sed -i 's/\r$//' prompts/truck-service-system.txt prompts/knowledge/*.md scripts/*.sh 2>/dev/null; chmod +x scripts/*.sh; docker compose build intake-api; docker compose up -d intake-api; ./scripts/knowledge-apply.sh"

Write-Host "==> Готово. Тест: https://agent.remont-gazon.ru/embed/chat.html"
