#!/usr/bin/env bash
set -euo pipefail

# n8n self-hosted Community Edition - macOS Apple Silicon (M1/M2/M3/M4)
# Prerequisite: Docker Desktop for Mac Apple Silicon is installed and running.

if ! command -v docker >/dev/null 2>&1; then
  echo "ERROR: docker command not found. Install Docker Desktop for Mac Apple Silicon first."
  exit 1
fi

if ! docker info >/dev/null 2>&1; then
  echo "ERROR: Docker Desktop is not running. Open Docker Desktop, wait until the engine is running, then retry."
  exit 1
fi

ARCH="$(uname -m)"
if [[ "$ARCH" != "arm64" ]]; then
  echo "WARNING: This script is optimized for Apple Silicon arm64. Current arch: $ARCH"
fi

echo "Creating Docker volume n8n_data if it does not exist..."
docker volume create n8n_data >/dev/null

if docker ps -a --format '{{.Names}}' | grep -q '^n8n$'; then
  echo "Existing n8n container found. Removing it first..."
  docker rm -f n8n >/dev/null 2>&1 || true
fi

echo "Starting n8n on http://localhost:5678"
echo "Apple Silicon note: Docker will use arm64 image automatically. --platform linux/arm64 is specified to avoid x86 emulation."

docker run -it --rm \
  --name n8n \
  --platform linux/arm64 \
  -p 5678:5678 \
  -e GENERIC_TIMEZONE="Asia/Jakarta" \
  -e TZ="Asia/Jakarta" \
  -e N8N_ENFORCE_SETTINGS_FILE_PERMISSIONS=true \
  -e N8N_RUNNERS_ENABLED=true \
  -e N8N_HOST="localhost" \
  -e N8N_PORT="5678" \
  -e N8N_PROTOCOL="http" \
  -e WEBHOOK_URL="http://localhost:5678/" \
  -v n8n_data:/home/node/.n8n \
  docker.n8n.io/n8nio/n8n
