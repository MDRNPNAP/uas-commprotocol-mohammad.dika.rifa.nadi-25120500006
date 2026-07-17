# Communication Protocols P10-P16 n8n/UAS Lab Package

This package contains:

- app/server.py: consolidated Communication Protocols demo app.
- app/requirements.txt: Python dependencies.
- n8n/P10_API_Reliability_Workflow_n8n_template.json: starter n8n workflow template.
- postman/P10_P16_n8n_UAS_Communication_Protocols.postman_collection.json: Postman collection with test scripts.
- scripts/: starter commands for Windows and Debian-family Linux.
- docs/: PDF and DOCX lab manual.

Quick start:

1. Run the demo app from `app/`:
   - Windows: `py -m pip install -r requirements.txt` then `py server.py`
   - Linux: `python3 -m pip install -r requirements.txt` then `python3 server.py`
2. Open `http://localhost:8088/api/health`.
3. Run n8n with the script in `scripts/`.
4. In n8n HTTP Request nodes, use `http://host.docker.internal:8088` when n8n runs in Docker.
5. Import the Postman collection and n8n workflow template.

Notes:

- The demo app is designed to run without internet after dependencies are installed.
- The local MQTT broker is embedded in `server.py` on port 1883.
- Protobuf conversion uses the Python protobuf library and returns binary bytes as base64 for Postman/browser readability.

---

## Tambahan: MacBook Apple Silicon M4 Pro

Untuk MacBook Apple Silicon M1/M2/M3/M4, gunakan file berikut:

```text
README_MACBOOK_APPLE_SILICON_M4_PRO.md
scripts/start_app_macos_apple_silicon.sh
scripts/run_n8n_macos_apple_silicon.sh
scripts/run_n8n_macos_compose.sh
scripts/smoke_test_macos_apple_silicon.sh
postman/CommProto_Local_Mac_Apple_Silicon.postman_environment.json
docker/docker-compose.n8n.macos-apple-silicon.yml
```

Ringkasan URL:

```text
Postman/browser Mac -> Demo App:
http://localhost:8088

Postman/browser Mac -> n8n:
http://localhost:5678

Postman -> n8n Webhook test:
http://localhost:5678/webhook-test/commproto-p10

n8n Docker -> Demo App di Mac host:
http://host.docker.internal:8088
```
