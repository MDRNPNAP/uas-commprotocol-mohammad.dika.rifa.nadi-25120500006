#!/usr/bin/env bash
set -euo pipefail

docker rm -f n8n >/dev/null 2>&1 || true
echo "n8n container stopped. Persistent data remains in Docker volume: n8n_data"
