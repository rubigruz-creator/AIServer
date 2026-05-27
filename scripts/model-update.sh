#!/usr/bin/env bash
# Обновление базовой модели и пересборка truck-service.

set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=common.sh
source "$SCRIPT_DIR/common.sh"

BASE_MODEL="${1:-$(default_base_model)}"

require_ollama

echo "==> Обновляем ${BASE_MODEL}..."
docker exec ollama ollama pull "${BASE_MODEL}"

"$SCRIPT_DIR/model-create.sh" "${BASE_MODEL}"
