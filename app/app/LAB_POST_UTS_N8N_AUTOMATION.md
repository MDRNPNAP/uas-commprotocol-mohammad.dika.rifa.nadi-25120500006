# Lab Post-UTS: API Documentation, Reliability, Microservices, Observability, n8n Automation

Dokumen ini menyelaraskan praktikum setelah UTS dengan RPS Communication Protocols.

RPS post-UTS:

| Pertemuan | Topik RPS | Fokus praktikum |
|---|---|---|
| 9 | API Design & Documentation menggunakan Postman | Collection, environment, documentation, test evidence, Newman-style runner |
| 10 | Rate Limiting dan Load Balancing | 429, request limit, backend distribution, reliability evidence |
| 11 | Microservices Communication Patterns | service chain, protocol choice, trace/call flow |
| 12 | Monitoring & Logging Protocol | logs, metrics, traces, observability interpretation |
| 13 | Proyek Protokol Fase 1 | automation/integration evidence, initial architecture |
| 14 | Proyek Protokol Fase 2 | design revision, documentation, testing plan |
| 15 | Presentasi Proyek & Peer Review | demo checkpoint, peer feedback, readiness |
| 16 | UAS Final Project Presentation | final report, demo, repository, evidence |

## Setup

Jalankan demo app:

```powershell
cd "C:\Users\Yenny-Haikal\OneDrive\Documents\New project\communication-protocols-demo-app"
py server.py
```

Buka:

```text
http://localhost:8088
```

Ports untuk Wireshark evidence:

```text
HTTP UI/API    : 8088
MQTT broker    : 1883
gRPC HTTP/2    : 50051
TLS/HTTPS      : 8443
```

Import Postman collection:

```text
postman/Communication_Protocols_Demo_App.postman_collection.json
```

Variable:

```text
base_url = http://localhost:8088
```

## Pertemuan 9 - API Design & Documentation using Postman/Newman

### Tujuan

Mahasiswa mampu membuat API collection yang terdokumentasi, menggunakan environment variable, menambahkan test sederhana, dan menjelaskan bagaimana collection dapat dijalankan berulang.

### Endpoint

```text
GET /api/openapi
GET /api/postman-run-summary
```

### Aktivitas

1. Buka halaman **P9 API Docs/Newman**.
2. Klik **GET OpenAPI-style Spec**.
3. Buka Postman collection folder **P9 API Documentation and Newman**.
4. Jalankan request `GET OpenAPI-style Spec`.
5. Jalankan request `GET Newman Runner Guide`.
6. Tambahkan Postman test minimal:

```javascript
pm.test("Status is 200", function () {
  pm.response.to.have.status(200);
});

pm.test("Response has teachingUse", function () {
  pm.expect(pm.response.json()).to.have.property("teachingUse");
});
```

7. Jalankan Collection Runner.
8. Screenshot test result.

### Newman/Postman CLI

Jika Newman tersedia:

```powershell
newman run postman/Communication_Protocols_Demo_App.postman_collection.json --env-var base_url=http://localhost:8088
```

Fallback jika Newman tidak tersedia:

- Gunakan Postman Collection Runner.
- Screenshot runner result.
- Jelaskan bahwa Newman adalah CLI runner untuk automation/testing pipeline.

### Deliverables

- Screenshot Postman collection.
- Screenshot tests pass.
- Exported collection.
- Ringkasan: endpoint, status code, test logic, runner evidence.
- Wireshark evidence: `tcp.port == 8088` dan `http.request.uri contains "/api/openapi"` atau `/api/postman/run`.

## Pertemuan 10 - Rate Limiting dan Load Balancing

### Tujuan

Mahasiswa memahami API reliability melalui rate limiting dan load balancing secara praktis.

### Endpoint

```text
GET /api/reliability/rate-limited
GET /api/reliability/load-balanced
POST /api/reliability/reset
```

### Aktivitas Rate Limiting

1. Buka halaman **P10 Reliability**.
2. Klik **Hit Rate-Limited API** sebanyak 4-5 kali.
3. Amati saat response berubah menjadi:

```text
429 Too Many Requests
```

4. Catat `limit`, `windowSeconds`, dan `retryAfterSeconds`.
5. Klik **Reset Reliability State** untuk mengulang.

### Aktivitas Load Balancing

1. Klik **Hit Load-Balanced API** beberapa kali.
2. Amati field `backend` berganti:

```text
api-node-a
api-node-b
api-node-c
```

3. Jelaskan bahwa load balancer mendistribusikan request ke beberapa backend.

### Deliverables

- Screenshot 200 dan 429.
- Screenshot backend yang berganti.
- Tabel analisis: reliability benefit, tradeoff, common failure.

## Pertemuan 11 - Microservices Communication Patterns

### Tujuan

Mahasiswa memahami pola komunikasi antar service dan titik observability yang perlu dicatat.

### Endpoint

```text
GET /api/microservices/order-flow
POST /api/microservices/orders
GET /api/cases/protocol-decision
```

### Aktivitas

1. Buka halaman **P11 Microservices**.
2. Klik **Protocol Decision Case**.
3. Klik **GET Order Flow**.
4. Jalankan `POST Simulate Order Flow`.
5. Identifikasi service chain:
   - API Gateway
   - Order Service
   - Inventory Service
   - Payment Service
   - Notification Service
6. Tandai protocol yang muncul: REST, gRPC internal call, WebSocket event.

### Deliverables

- Screenshot order flow.
- Diagram sequence sederhana.
- Analisis failure point: service mana paling kritis dan evidence apa yang dibutuhkan.

## Pertemuan 12 - Monitoring, Logging, Telemetry & Observability

### Tujuan

Mahasiswa membedakan logs, metrics, dan traces serta mengaitkannya dengan troubleshooting protocol.

### Endpoint

```text
GET /api/observability/metrics
GET /api/observability/logs
GET /api/observability/trace/demo-trace-001
```

### Aktivitas

1. Jalankan beberapa request dari halaman lain.
2. Buka **P12 Observability**.
3. Klik **GET Metrics**.
4. Klik **GET Logs**.
5. Klik **GET Trace**.
6. Diskusikan:
   - Metrics menjawab "berapa banyak / seberapa sering".
   - Logs menjawab "apa yang terjadi".
   - Trace menjawab "request ini lewat mana saja".

### Deliverables

- Screenshot metrics.
- Screenshot logs.
- Screenshot trace.
- Analisis: bedakan symptom, evidence, probable cause.
- Wireshark evidence: jalankan `POST /api/observability/capture-scenario`, lalu capture `tcp.port == 8088` dan `tcp.port == 1883` atau `mqtt`.

## Pertemuan 13-15 - n8n Automation, Project Phase & Peer Review

### Tujuan

Mahasiswa memahami automation workflow untuk integrasi protokol dan menyiapkan evidence project.

### Endpoint Demo App

```text
GET /api/automation/n8n-workflow-spec
POST /api/automation/inbox
POST /api/automation/workflow-run
GET /api/automation/inbox
```

### Workflow n8n yang Disarankan

Struktur workflow:

```text
Webhook Trigger
  -> Set / Edit Fields
  -> HTTP Request
  -> Respond to Webhook
```

Node 1: **Webhook Trigger**

- Method: `POST`
- Path: `commproto-demo`
- Test URL contoh:

```text
http://localhost:5678/webhook-test/commproto-demo
```

Node 2: **Set / Edit Fields**

Fields:

```json
{
  "protocol": "MQTT+REST+n8n",
  "event": "telemetry.workflow.completed",
  "deviceId": "sensor-01",
  "evidence": "n8n-workflow-run"
}
```

Node 3: **HTTP Request**

Jika n8n berjalan lokal tanpa Docker:

```text
POST http://localhost:8088/api/automation/inbox
```

Jika n8n berjalan di Docker:

```text
POST http://host.docker.internal:8088/api/automation/inbox
```

Headers:

```text
Content-Type: application/json
```

Body:

```json
{
  "protocol": "{{$json.protocol}}",
  "event": "{{$json.event}}",
  "deviceId": "{{$json.deviceId}}",
  "evidence": "{{$json.evidence}}"
}
```

Node 4: **Respond to Webhook**

Response body:

```json
{
  "status": "accepted",
  "message": "Workflow completed"
}
```

### Fallback Jika n8n Belum Bisa Jalan

Gunakan Postman:

```text
POST {{base_url}}/api/automation/inbox
```

Body:

```json
{
  "protocol": "MQTT+REST+n8n",
  "event": "telemetry.workflow.completed",
  "deviceId": "sensor-01",
  "evidence": "postman-fallback"
}
```

Untuk Wireshark evidence tanpa n8n, gunakan:

```text
POST {{base_url}}/api/automation/workflow-run
```

Body:

```json
{
  "workflow": "telemetry-to-inbox",
  "event": "telemetry.workflow.completed",
  "triggerPayload": {
    "deviceId": "sensor-01",
    "temperature": 31.2,
    "source": "postman-fallback"
  },
  "wireCapture": true
}
```

Filter:

```text
tcp.port == 8088
tcp.port == 1883
mqtt
```

### Deliverables

- Screenshot n8n workflow canvas.
- Screenshot Webhook Trigger execution.
- Screenshot HTTP Request node success.
- Screenshot `GET /api/automation/inbox`.
- Reflection: apa yang otomatis, protocol apa yang terlibat, failure apa yang mungkin terjadi.

## Pertemuan 16 - UAS Final Project

### Minimum Evidence

| Evidence | Wajib |
|---|---|
| GitHub repository | Ya |
| PDF report | Ya |
| PPT final | Ya |
| Postman collection | Ya |
| Automation evidence n8n atau fallback Postman | Ya untuk project automation |
| Screenshot logs/metrics/trace | Ya |
| Protocol rationale | Ya |
| Troubleshooting note | Ya |
| Wireshark capture minimal dua protocol | Ya |

### Recommended Project Pattern

```text
MQTT telemetry simulation
  -> API ingestion / automation trigger
  -> n8n workflow
  -> demo app automation inbox
  -> observability evidence
  -> final report and presentation
```

Recommended final capture:

```text
POST /api/project/capture-demo
```

Expected packet evidence:

- HTTP project endpoint: `tcp.port == 8088`.
- WebSocket upgrade/frame: `http.request.uri contains "/ws/echo"` atau `websocket`.
- MQTT publish: `tcp.port == 1883` atau `mqtt`.
- gRPC HTTP/2: `tcp.port == 50051` atau `http2`.

### Rubrik Ringkas

| Komponen | Bobot |
|---|---:|
| Protocol design and rationale | 20% |
| Implementation/demo | 25% |
| Testing and evidence | 20% |
| n8n automation / integration evidence | 15% |
| Observability and troubleshooting | 10% |
| Documentation and presentation | 10% |
