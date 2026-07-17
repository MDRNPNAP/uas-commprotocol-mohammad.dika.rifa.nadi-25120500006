#!/usr/bin/env bash
set -euo pipefail

echo "DANGER: This deletes all local n8n workflows/credentials stored in volume n8n_data."
read -r -p "Type DELETE_N8N_DATA to continue: " confirm
if [[ "$confirm" != "DELETE_N8N_DATA" ]]; then
  echo "Cancelled."
  exit 0
fi

docker rm -f n8n >/dev/null 2>&1 || true
docker volume rm n8n_data
echo "Deleted Docker volume n8n_data."
