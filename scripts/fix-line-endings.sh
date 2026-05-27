#!/usr/bin/env bash
# Конвертация CRLF → LF (файлы, скопированные с Windows).

set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=common.sh
source "$SCRIPT_DIR/common.sh"

if ! command -v dos2unix >/dev/null 2>&1; then
  echo "Установите dos2unix: apt install -y dos2unix"
  exit 1
fi

dos2unix "$ROOT_DIR"/scripts/*.sh
dos2unix "$ROOT_DIR"/prompts/*.txt 2>/dev/null || true
dos2unix "$ROOT_DIR"/ollama/* 2>/dev/null || true
chmod +x "$ROOT_DIR"/scripts/*.sh

echo "==> Готово: переносы строк исправлены, скрипты исполняемые."
