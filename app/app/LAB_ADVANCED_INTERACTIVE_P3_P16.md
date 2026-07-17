# Advanced Interactive Lab P3-P16

Dokumen ini adalah revisi detail agar praktikum P3 ke atas tidak berhenti di `GET` sederhana. Setiap pertemuan punya kombinasi `GET` untuk membaca state dan `POST` untuk membuat event, payload, workflow, failure scenario, atau evidence baru.

App lokal:

```text
http://localhost:8088
```

Ports untuk Wireshark:

```text
HTTP/WebSocket: 8088
MQTT: 1883
gRPC HTTP/2: 50051
TLS/HTTPS: 8443
```

Postman collection:

```text
postman/Communication_Protocols_Demo_App.postman_collection.json
```

Variable Postman:

```text
base_url = http://localhost:8088
```

## Prinsip Demo Dosen

1. Dosen mulai dari halaman app sesuai pertemuan.
2. Dosen ubah input seperti `channel`, `topic`, `payload`, `RPC method`, `status code`, atau `failure point`.
3. Dosen jalankan `POST` untuk membuat state baru.
4. Dosen jalankan `GET` untuk membuktikan state berubah.
5. Mahasiswa screenshot request, response, dan interpretasi protocol.
6. Jika perlu evidence formal, ulangi request yang sama dari Postman collection.

## P3 - WebSocket and Real-Time Communication

Mapping RPS: WebSocket & Real-Time Communication.

Fokus konsep:

- Persistent connection.
- Event-driven message.
- Channel-based realtime update.
- Perbandingan WebSocket vs HTTP polling.

UI demo:

- Page: `P3 WebSocket`.
- Input yang bisa diubah mahasiswa:
  - `Channel`: `dashboard`, `orders`, `telemetry`, `alerts`.
  - `Event Template`: `dashboard_refresh`, `order_created`, `sensor_alert`, `chat_message`.
  - `Message JSON`: bebas selama valid JSON.

Demo 1: WebSocket asli dari browser.

1. Pilih `channel = dashboard`.
2. Pilih template `dashboard_refresh`.
3. Klik `Connect`.
4. Klik `Send Message`.
5. Ubah payload:

```json
{
  "event": "order_created",
  "orderId": "ORD-2026-009",
  "amount": 900000
}
```

6. Klik `Send Message` lagi.
7. Bahas perbedaan `SEND` dan `RECV`.

Demo 1B: WebSocket packet capture terkontrol.

1. Start Wireshark pada Npcap Loopback Adapter.
2. Klik `Send Real WebSocket Capture`.
3. Gunakan filter awal:

```text
tcp.port == 8088
```

4. Cari `GET /ws/echo?channel=dashboard` dengan status `101 Switching Protocols`.
5. Jika belum muncul sebagai WebSocket, gunakan **Decode As...** lalu set TCP port `8088` sebagai `HTTP`.
6. Gunakan filter:

```text
websocket
http.request.uri contains "/ws/echo"
http.header contains "Upgrade"
```

Demo 1C: WebSocket session retention.

1. Klik `Connect`.
2. Jangan klik `Close`.
3. Biarkan session idle minimal 30 detik.
4. UI mengirim `client_keepalive` tiap 15 detik dan server mengirim WebSocket ping keepalive.
5. Di Wireshark, cari `WebSocket Text`, `Ping`, dan `Pong`.

Catatan: session tidak diputus otomatis saat idle. Koneksi tertutup hanya jika tombol `Close` ditekan, tab browser ditutup, jaringan putus, atau server dihentikan.

Demo 2: HTTP event API untuk evidence Postman.

```http
POST /api/realtime/events
GET /api/realtime/events?channel=dashboard
```

Sample body:

```json
{
  "channel": "alerts",
  "event": "sensor_alert",
  "transport": "http-post-event",
  "payload": {
    "deviceId": "sensor-02",
    "temperature": 39.4,
    "severity": "warning"
  }
}
```

Expected output:

- `POST` return `201`.
- `GET` return list event sesuai channel.

Evidence mahasiswa:

- Screenshot WebSocket connected state.
- Screenshot `SEND` dan `RECV`.
- Screenshot Wireshark `101 Switching Protocols`.
- Screenshot Wireshark frame `WebSocket Text`.
- Screenshot WebSocket heartbeat atau Ping/Pong setelah 30 detik idle.
- Screenshot Postman `POST /api/realtime/events`.
- Screenshot Postman `GET /api/realtime/events?channel=...`.
- Reflection: kapan WebSocket lebih cocok daripada REST polling.

Fallback:

- Jika WebSocket client Postman bermasalah, pakai browser UI.
- Jika WebSocket blocked jaringan kantor, pakai HTTP event API sebagai simulasi event.

## P4 - MQTT and IoT Telemetry

Mapping RPS: MQTT dan Protokol IoT untuk telemetry.

Fokus konsep:

- Publisher, subscriber, broker concept.
- Topic hierarchy.
- Topic filter `+`.
- QoS concept.
- Retained message concept.
- Telemetry payload untuk data science.

UI demo:

- Page: `P4 MQTT IoT`.
- Input yang bisa diubah mahasiswa:
  - `Client ID`.
  - `Topic`.
  - `QoS`.
  - `Retained message`.
  - `Payload JSON`.
  - `Subscribe Filter`.

Demo utama:

1. Isi `Client ID`: `student-client-01`.
2. Isi topic:

```text
class/commproto/sensor-01/temperature
```

3. Isi payload:

```json
{
  "deviceId": "sensor-01",
  "temperature": 27.5,
  "humidity": 61
}
```

4. Pilih `QoS 1`.
5. Centang `Retained message`.
6. Klik `Publish`.
7. Untuk evidence Wireshark MQTT asli singkat, start capture lalu klik `Publish Real MQTT Packet`.
8. Untuk session yang tidak disconnect, klik `Start Persistent MQTT Session`.
9. Biarkan session berjalan minimal 30 detik agar Wireshark menangkap `PINGREQ` dan `PINGRESP`.
10. Klik `Stop MQTT Session` hanya saat demo selesai.
11. Klik `Load Messages`.
12. Ubah topic menjadi:

```text
class/commproto/sensor-02/humidity
```

13. Ubah payload:

```json
{
  "deviceId": "sensor-02",
  "humidity": 72,
  "battery": 88
}
```

14. Klik `Publish Real MQTT Packet`.
15. Ubah filter:

```text
class/commproto/+/temperature
```

16. Klik `Load by Filter`.
17. Klik `Load Topics`.

Postman endpoints:

```http
POST /api/mqtt/publish
GET /api/mqtt/real-status
POST /api/mqtt/real-publish
GET /api/mqtt/session/status
POST /api/mqtt/session/start
POST /api/mqtt/session/stop
GET /api/mqtt/messages?topic=class/commproto/sensor-01/temperature
GET /api/mqtt/messages?filter=class/commproto/+/temperature
GET /api/mqtt/topics
POST /api/mqtt/clear
```

Wireshark MQTT asli:

```text
tcp.port == 1883
mqtt
```

Jika Wireshark belum otomatis mengenali protocol, gunakan **Decode As...** lalu set TCP port `1883` sebagai `MQTT`.

Expected output:

- `POST` return `201` dengan `clientId`, `topic`, `qos`, `retained`, `payload`.
- `POST /api/mqtt/real-publish` return `ok: true`, `realMqtt: true`, dan daftar packet seperti `CONNECT`, `CONNACK`, `SUBSCRIBE`, `SUBACK`, `PUBLISH`, `DISCONNECT`.
- `POST /api/mqtt/session/start` return session active/starting dan koneksi tetap hidup dengan `PINGREQ`/`PINGRESP`.
- `GET topic` return message exact topic.
- `GET filter` return message yang match wildcard.
- `GET topics` return topic unik dan retained messages.

Evidence mahasiswa:

- Screenshot publish telemetry.
- Screenshot terminal `Real MQTT broker running at 127.0.0.1:1883`.
- Screenshot Wireshark filter `mqtt` atau `tcp.port == 1883`.
- Screenshot `PINGREQ`/`PINGRESP` untuk membuktikan session tetap hidup.
- Screenshot subscribe by exact topic.
- Screenshot subscribe by filter.
- Interpretasi topic hierarchy dan QoS.

Fallback:

- Jika port `1883` sudah dipakai broker lain, stop broker tersebut atau gunakan MQTTX/HiveMQ/Mosquitto sebagai alternatif.
- Jika Wireshark tidak menangkap loopback, gunakan adapter Npcap loopback atau demo antar dua laptop/VM.
- Jika real MQTT bermasalah, tetap pakai simulator lokal untuk topic/filter concept, tetapi jangan klaim itu MQTT packet capture.

## P5 - gRPC and Protocol Buffers

Mapping RPS: gRPC dan Protocol Buffers.

Fokus konsep:

- Service contract.
- `.proto` schema.
- RPC method.
- Request message vs response message.
- Perbandingan gRPC dengan REST.

Mode A - UI concept demo:

- Page: `P5 gRPC Protobuf`.
- Input:
  - `RPC Method`: `Predict`, `BatchPredict`, `HealthCheck`.
  - `Message JSON`: payload request.

Catatan penting:

- Endpoint `/api/grpc/*` berjalan di demo app HTTP biasa pada port `8088`.
- Jika di-capture dengan Wireshark, traffic ini akan terlihat sebagai HTTP/1.x. Itu normal karena halaman ini adalah **concept mock** agar mudah dilihat di browser/Postman.
- Untuk praktikum Wireshark yang harus menunjukkan HTTP/2, gunakan tombol/endpoint **POST Real gRPC HTTP/2 Call**. Satu script `server.py` menjalankan HTTP UI di port `8088` dan real gRPC HTTP/2 di port `50051`.
- Untuk demo standar, mahasiswa **tidak perlu edit `.proto`**. `.proto` adalah service contract yang dibaca lewat `GET /api/grpc/proto`. Edit `.proto` hanya diperlukan jika ingin menambah field atau method baru.
- Saat dropdown `RPC Method` diganti, textarea otomatis berubah:
  - `Predict`: satu `customerId` dan satu object `features`.
  - `BatchPredict`: object `items[]` berisi beberapa prediction request.
  - `HealthCheck`: body kosong `{}` untuk cek readiness service.

Endpoints:

```http
GET /api/grpc/proto
GET /api/grpc/services
GET /api/grpc/http2-status
POST /api/grpc/infer
POST /api/grpc/call
POST /api/grpc/http2-call
```

Sample `Predict`:

```json
{
  "method": "Predict",
  "payload": {
    "customerId": "C-1024",
    "features": {
      "avgOrderValue": 250000,
      "monthlyOrders": 7
    }
  }
}
```

Sample `BatchPredict`:

```json
{
  "method": "BatchPredict",
  "payload": {
    "items": [
      {"customerId": "C-1001", "features": {"avgOrderValue": 150000, "monthlyOrders": 3}},
      {"customerId": "C-1002", "features": {"avgOrderValue": 420000, "monthlyOrders": 9}}
    ]
  }
}
```

Sample `HealthCheck`:

```json
{
  "method": "HealthCheck",
  "payload": {}
}
```

Expected output:

- `GET /api/grpc/proto` menampilkan schema.
- `GET /api/grpc/services` menampilkan service dan method.
- `POST /api/grpc/call` return response berbeda berdasarkan method.
- `Predict` menghasilkan satu `PredictionReply`.
- `BatchPredict` menghasilkan `count` dan array `predictions`, bukan response kosong.
- `HealthCheck` menghasilkan status `SERVING`.
- `POST /api/grpc/http2-call` memicu real gRPC call ke `127.0.0.1:50051` untuk `Predict`, `BatchPredict`, atau `HealthCheck`.

Evidence:

- Screenshot `.proto`.
- Screenshot `Predict`, `BatchPredict`, dan/atau `HealthCheck`.
- Analisis: field apa yang menjadi contract.

Mode B - Integrated Real Python gRPC HTTP/2:

Satu command untuk menjalankan app dan gRPC server:

```powershell
cd "C:\Users\Yenny-Haikal\OneDrive\Documents\New project\communication-protocols-demo-app"
py -m pip install -r requirements.txt
py server.py
```

Wireshark:

```text
tcp.port == 50051
```

Jika belum terbaca sebagai HTTP/2, gunakan **Decode As...** lalu set TCP port `50051` sebagai `HTTP2`, kemudian filter:

```text
http2
```

Evidence tambahan:

- Screenshot terminal menunjukkan `Real gRPC HTTP/2 server running at 127.0.0.1:50051`.
- Screenshot response dari tombol **POST Real gRPC HTTP/2 Call** atau Postman `POST /api/grpc/http2-call`.
- Screenshot Wireshark `tcp.port == 50051`.
- Screenshot HTTP/2 `HEADERS`/`DATA` frames atau path `/demo.inference.InferenceService/Predict`.
- Reflection: mengapa trigger HTTP di port `8088` terlihat HTTP/1.x, sedangkan internal gRPC call di port `50051` terlihat HTTP/2.

Fallback:

- Jika dependency `grpcio` belum terinstall, jalankan `python -m pip install -r requirements.txt`.
- Jika dependency `grpcio` belum bisa diinstall saat kelas, dosen dapat menjalankan server dari laptop dosen dan mahasiswa melakukan capture/analisis.
- Jika Wireshark tidak bisa capture loopback, gunakan demo antar dua laptop/VM atau screenshot capture dosen.

## P6 - Data Encoding JSON, XML, CSV, Protobuf

Mapping RPS: Data Encoding.

Fokus konsep:

- Serialization format.
- Human-readable vs schema-based format.
- Payload size.
- Format pilihan untuk data pipeline.

Endpoints:

```http
GET /api/exchange/json
GET /api/exchange/xml
GET /api/exchange/csv
GET /api/exchange/protobuf-schema
POST /api/encoding/convert
```

Sample body:

```json
{
  "to": "protobuf",
  "records": [
    {"id": 1, "sensor": "temperature", "value": 27.5, "unit": "celsius"}
  ]
}
```

Variasi tugas mahasiswa:

- Convert ke `json`.
- Convert ke `xml`.
- Convert ke `csv`.
- Convert ke `protobuf`.
- Bandingkan `byteLength`.

Evidence:

- Screenshot empat format.
- Catatan format paling mudah dibaca dan paling cocok untuk service-to-service.
- Wireshark capture HTTP endpoint converter:

```text
tcp.port == 8088
http.request.uri contains "/api/encoding"
```

Catatan dosen: P6 adalah data serialization lab. JSON/XML/CSV/Protobuf demo dikirim melalui HTTP API agar mudah dibaca di Postman dan Wireshark. Untuk binary Protobuf yang lebih nyata, hubungkan dengan P5 gRPC HTTP/2 pada port `50051`.

## P7 - TLS/HTTP Troubleshooting and UTS Prep

Mapping RPS: TLS/SSL, HTTP/TLS fundamentals, troubleshooting.

Fokus konsep:

- Status code.
- Latency/delay.
- Error scenario.
- Header dan response body.
- Wireshark/curl evidence.

Endpoints:

```http
GET /api/tls/status
POST /api/tls/self-test
GET /api/health
GET /api/troubleshooting/status/400
GET /api/troubleshooting/status/404
GET /api/troubleshooting/slow?ms=1200
POST /api/troubleshooting/test
```

Sample `POST`:

```json
{
  "status": 429,
  "delayMs": 300,
  "scenario": "Client receives rate limit while testing API integration"
}
```

Expected output:

- Status sesuai input.
- Response menjelaskan scenario.
- Mahasiswa harus menghubungkan symptom, probable cause, dan next action.

Wireshark:

```text
tcp.port == 8443
tls
tls.handshake
tcp.port == 8088
http
```

Langkah demo:

1. Start capture pada `Npcap Loopback Adapter`.
2. Klik `POST TLS Self-Test` dari UI atau Postman.
3. Filter `tcp.port == 8443`.
4. Tunjukkan `Client Hello`, `Server Hello`, `Certificate`, dan `Application Data`.
5. Jalankan `GET /api/troubleshooting/status/404` lalu filter `tcp.port == 8088` untuk membandingkan HTTP plaintext dengan HTTPS encrypted payload.

Evidence:

- Screenshot Postman status code.
- Screenshot curl command.
- Screenshot Wireshark TLS handshake `tcp.port == 8443`.
- Screenshot HTTP troubleshooting `tcp.port == 8088`.

Fallback:

- Jika TLS tidak muncul, pastikan server menampilkan `TLS/HTTPS demo server running at https://127.0.0.1:8443`.
- Jika browser menolak self-signed certificate, gunakan tombol `POST TLS Self-Test`; tombol ini membuat TLS client internal dari `server.py`.
- Jika Wireshark tidak decode `tls`, gunakan display filter `tcp.port == 8443` dan cari paket handshake di kolom Info.

## P8 - UTS Evidence

Mapping RPS: UTS.

Fokus:

- Individual evidence.
- API testing.
- Packet capture evidence.
- Basic troubleshooting.

Endpoints:

```http
GET /api/uts/orders
POST /api/webhook/inbox
POST /api/uts/evidence
GET /api/webhook/inbox
```

Sample evidence body:

```json
{
  "studentId": "NIM-DEMO",
  "case": "UTS API + packet capture evidence",
  "methods": ["GET", "POST"],
  "evidence": ["postman-screenshot", "curl-command", "pcapng-optional"]
}
```

Minimum evidence:

- Postman collection screenshot.
- Response body screenshot.
- CLI/curl command.
- Short explanation of request and response.
- Wireshark screenshot dengan filter `tcp.port == 8088`.
- Optional `.pcapng` berisi request UTS.

Wireshark:

```text
tcp.port == 8088
http.request.uri contains "/api/uts"
http.request.uri contains "/api/webhook"
```

Guidance presentasi mahasiswa:

1. Mahasiswa jalankan capture sebelum request.
2. Mahasiswa kirim `GET /api/uts/orders`.
3. Mahasiswa kirim `POST /api/webhook/inbox`.
4. Mahasiswa kirim `POST /api/uts/evidence`.
5. Mahasiswa tunjukkan request method, URI, status code, dan response body.

Fallback:

- Jika Wireshark loopback gagal, evidence minimal tetap Postman + curl. Dosen dapat menampilkan sample capture dari laptop dosen.

## P9 - API Documentation and Newman/Postman Runner

Mapping RPS: API Design & Documentation using Postman.

Endpoints:

```http
GET /api/openapi
GET /api/postman-run-summary
POST /api/postman/run
```

Sample body:

```json
{
  "folder": "P9 API Documentation and Newman",
  "iterations": 2
}
```

Aktivitas:

1. Import collection.
2. Cek variable `base_url`.
3. Jalankan folder P9.
4. Tambahkan test minimal: status code expected.
5. Export screenshot runner.

Wireshark:

```text
tcp.port == 8088
http.request.uri contains "/api/openapi"
http.request.uri contains "/api/postman"
```

Evidence:

- Screenshot OpenAPI-style response.
- Screenshot Postman Runner/Newman-style simulator.
- Screenshot Wireshark yang menunjukkan request ke `/api/openapi` atau `/api/postman/run`.

Fallback:

- Jika Newman belum tersedia, gunakan Postman Collection Runner.
- Jika mahasiswa belum install Postman, gunakan UI browser dan `curl`.

## P10 - Rate Limiting and Load Balancing

Mapping RPS: Rate Limiting dan Load Balancing.

Endpoints:

```http
GET /api/reliability/rate-limited
GET /api/reliability/load-balanced
POST /api/reliability/simulate-load
POST /api/reliability/reset
```

Sample `POST`:

```json
{
  "requests": 9
}
```

Aktivitas:

- Klik rate-limited API empat kali untuk memicu `429`.
- Jalankan simulate load untuk melihat backend `api-node-a/b/c`.
- Jelaskan mengapa client perlu retry/backoff.

Evidence:

- Screenshot response `429`.
- Screenshot load-balanced backend distribution.
- Screenshot Wireshark HTTP request berulang.

Wireshark:

```text
tcp.port == 8088
http.response.code == 429
http.request.uri contains "/api/reliability"
```

Guidance:

- Untuk memunculkan `429`, hit `GET /api/reliability/rate-limited` minimal empat kali dari client yang sama.
- Untuk load balancing, jalankan `POST /api/reliability/simulate-load` dan cocokkan response `api-node-a/b/c` dengan packet request di Wireshark.

Fallback:

- Jika `http.response.code == 429` tidak muncul, gunakan `tcp.port == 8088`, lalu cari response text `Too Many Requests` di packet details.

## P11 - Microservices Communication Patterns

Mapping RPS: Microservices Communication Patterns.

Endpoints:

```http
GET /api/cases/protocol-decision
GET /api/microservices/order-flow
POST /api/microservices/orders
```

Sample success:

```json
{
  "orderId": "ORD-DEMO-001",
  "amount": 450000,
  "wireCapture": true
}
```

Sample failure:

```json
{
  "orderId": "ORD-DEMO-002",
  "amount": 750000,
  "failAt": "payment-service",
  "wireCapture": true
}
```

Aktivitas:

- Jalankan flow sukses.
- Jalankan flow gagal pada `inventory-service`, `payment-service`, atau `notification-service`.
- Buat sequence diagram sederhana.
- Jelaskan protocol pada tiap hop.
- Aktifkan `wireCapture: true` untuk memicu gRPC HTTP/2 dan MQTT packet nyata selain HTTP API response.

Evidence:

- Screenshot traceId.
- Screenshot service yang gagal.
- Reflection: di mana perlu timeout, retry, atau compensation.
- Screenshot Wireshark HTTP API di `8088`.
- Screenshot Wireshark MQTT publish di `1883`.
- Screenshot Wireshark gRPC HTTP/2 di `50051`.

Wireshark:

```text
tcp.port == 8088
tcp.port == 1883
mqtt
tcp.port == 50051
http2
```

Guidance:

- Request ke `/api/microservices/orders` tetap HTTP/1.1 di port `8088`.
- Karena `wireCapture: true`, `server.py` juga melakukan real gRPC HTTP/2 call ke port `50051` dan real MQTT publish ke port `1883`.
- Jika `http2` belum terbaca, klik kanan paket port `50051` > `Decode As...` > `HTTP2`.

## P12 - Monitoring, Logging, Telemetry, Observability

Mapping RPS: Monitoring & Logging Protocol.

Endpoints:

```http
GET /api/observability/metrics
GET /api/observability/logs
GET /api/observability/trace/demo-trace-001
POST /api/observability/custom-log
POST /api/observability/capture-scenario
```

Sample log:

```json
{
  "event": "custom.observability.event",
  "severity": "info",
  "service": "demo-postman",
  "message": "Mahasiswa membuat custom log dari Postman",
  "traceId": "demo-trace-001"
}
```

Aktivitas:

- Jalankan beberapa endpoint P9-P11.
- Buka metrics.
- Buka logs.
- Buka trace.
- Buat custom log.
- Klik `POST Capture Scenario` untuk memicu HTTP request plus MQTT telemetry packet.
- Bandingkan fungsi logs, metrics, dan traces.

Evidence:

- Screenshot metrics dengan request count.
- Screenshot logs.
- Screenshot trace.
- Screenshot MQTT telemetry evidence dari capture scenario.

Wireshark:

```text
tcp.port == 8088
http.request.uri contains "/api/observability"
tcp.port == 1883
mqtt
```

Fallback:

- Jika MQTT capture tidak muncul, jalankan dulu P4 `Publish Real MQTT Packet` untuk memastikan broker aktif.
- Jika hanya HTTP yang muncul, gunakan response field `mqttEvidence` untuk melihat error teknisnya.

## P13-P15 - n8n Automation and Project Phase

Mapping RPS: Proyek Protokol Fase 1, Fase 2, Project Presentation & Peer Review.

Endpoints:

```http
GET /api/automation/n8n-workflow-spec
POST /api/automation/inbox
POST /api/automation/workflow-run
GET /api/automation/inbox
```

Sample automation body:

```json
{
  "protocol": "MQTT+REST+n8n",
  "event": "telemetry.workflow.completed",
  "deviceId": "sensor-01",
  "evidence": "n8n-workflow-run"
}
```

Sample workflow simulation:

```json
{
  "workflow": "telemetry-to-inbox",
  "event": "telemetry.workflow.completed",
  "triggerPayload": {
    "deviceId": "sensor-01",
    "temperature": 31.2,
    "source": "mqtt-simulator"
  },
  "wireCapture": true
}
```

Aktivitas n8n:

1. Buat `Webhook Trigger`.
2. Tambah `Set/Edit Fields`.
3. Tambah `HTTP Request`.
4. POST ke:

```text
http://localhost:8088/api/automation/inbox
```

5. Jika n8n berjalan di Docker, gunakan:

```text
http://host.docker.internal:8088/api/automation/inbox
```

6. Tambah `Respond to Webhook`.
7. Screenshot workflow dan execution result.
8. Dari UI/Postman, jalankan `POST /api/automation/workflow-run` dengan `wireCapture: true` untuk memicu MQTT packet nyata.

Wireshark:

```text
tcp.port == 8088
http.request.uri contains "/api/automation"
tcp.port == 1883
mqtt
```

Evidence:

- Screenshot n8n workflow.
- Screenshot execution result.
- Screenshot HTTP request ke `/api/automation/inbox` atau `/api/automation/workflow-run`.
- Screenshot MQTT packet dari automation simulator jika `wireCapture: true`.

Fallback:

- Jika n8n belum siap, gunakan `POST /api/automation/workflow-run` dari UI/Postman untuk simulasi workflow.
- Jika n8n berjalan di Docker dan tidak bisa mengakses host, gunakan `host.docker.internal` atau jalankan Postman simulator saja.

## P16 - UAS Final Project

Mapping RPS: UAS Final Project Presentation.

Endpoints:

```http
GET /api/project/summary
POST /api/project/events
GET /api/project/events
POST /api/project/capture-demo
```

Sample body:

```json
{
  "protocol": "MQTT+WebSocket+n8n",
  "event": "uas.demo.executed",
  "evidence": "screenshot+postman+automation-log",
  "wireCapture": true
}
```

Minimum UAS evidence:

- GitHub repository.
- Source code or workflow export.
- Postman collection evidence.
- Screenshot protocol flow.
- Screenshot observability or automation evidence.
- Reflection: protocol used, reason, failure encountered, troubleshooting action.
- Wireshark screenshot untuk minimal dua protocol berbeda.

Recommended final capture:

1. Start Wireshark pada `Npcap Loopback Adapter`.
2. Klik `POST Multi-Protocol Capture` di halaman P16 atau jalankan `POST /api/project/capture-demo`.
3. Ambil evidence HTTP endpoint pada `8088`.
4. Ambil evidence WebSocket upgrade/frame pada `8088`.
5. Ambil evidence MQTT packet pada `1883`.
6. Ambil evidence gRPC HTTP/2 pada `50051`.

Wireshark:

```text
tcp.port == 8088
http.request.uri contains "/api/project"
http.request.uri contains "/ws/echo"
websocket
tcp.port == 1883
mqtt
tcp.port == 50051
http2
```

Fallback:

- Jika waktu demo terbatas, wajib tampilkan HTTP + satu protocol event-driven: MQTT atau WebSocket.
- Jika Wireshark tidak decode protocol otomatis, gunakan filter `tcp.port == ...` dulu, lalu `Decode As...` sesuai port.

## Rubrik Ringkas untuk P3-P16

| Komponen | Bobot | Indikator |
|---|---:|---|
| Protocol understanding | 25% | Bisa menjelaskan request/response, event, topic, method, schema, atau trace sesuai pertemuan. |
| Lab execution | 25% | Berhasil menjalankan `GET` dan `POST` dengan input yang dimodifikasi sendiri. |
| Evidence quality | 20% | Screenshot/log/response jelas dan bisa diverifikasi. |
| Troubleshooting analysis | 15% | Bisa menghubungkan status code, delay, failure point, atau missing payload dengan penyebab teknis. |
| Documentation | 10% | Catatan ringkas, rapi, dan menyebut endpoint serta payload. |
| Professionalism | 5% | Repo/filename/presentasi rapi, tidak hardcode bukti palsu. |
