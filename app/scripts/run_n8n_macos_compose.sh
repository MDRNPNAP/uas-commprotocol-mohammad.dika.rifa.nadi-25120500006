#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PACKAGE_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
COMPOSE_FILE="$PACKAGE_ROOT/docker/docker-compose.n8n.macos-apple-silicon.yml"

if ! docker info >/dev/null 2>&1; then
  echo "ERROR: Docker Desktop is not running."
  exit 1
fi

docker compose -f "$COMPOSE_FILE" up
