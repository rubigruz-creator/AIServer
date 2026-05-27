#!/usr/bin/env bash
# Общие функции для скриптов AIServer

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

cd_project() {
  cd "$ROOT_DIR"
}

require_compose() {
  if [[ ! -f "$ROOT_DIR/docker-compose.yml" ]]; then
    echo "Ошибка: не найден docker-compose.yml в $ROOT_DIR" >&2
    exit 1
  fi
}

require_ollama() {
  if ! docker exec ollama ollama list >/dev/null 2>&1; then
    echo "Ошибка: контейнер ollama не запущен." >&2
    echo "  cd $ROOT_DIR && docker compose up -d ollama" >&2
    exit 1
  fi
}

default_base_model() {
  echo "qwen2.5:1.5b"
}
