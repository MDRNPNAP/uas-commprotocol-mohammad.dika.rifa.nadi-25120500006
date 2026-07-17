# Communication Protocols Demo App

Satu aplikasi lokal untuk mendemokan materi Communication Protocols sesuai RPS yang dikirim.

Tujuan app ini bukan mengganti semua tool lab seperti Wireshark, Postman, MQTTX, atau grpcurl. Tujuannya adalah memberi dosen satu local backend dan UI browser yang stabil untuk demonstrasi kelas.

## Cara Menjalankan

Windows:

```powershell
cd "C:\Users\Yenny-Haikal\OneDrive\Documents\New project\communication-protocols-demo-app"
py -m pip install -r requirements.txt
py server.py
```

macOS/Linux:

```bash
cd communication-protocols-demo-app
python3 -m pip install -r requirements.txt
python3 server.py
```

Buka:

```text
http://localhost:8088
```

Server yang aktif dari satu script:

```text
HTTP teaching UI/API : http://127.0.0.1:8088
MQTT broker asli    : 127.0.0.1:1883
gRPC HTTP/2 server  : 127.0.0.1:50051
HTTPS/TLS demo      : https://127.0.0.1:8443
```

## Modul Pertemuan

| Pertemuan | Halaman demo | Endpoint utama |
|---|---|---|
| 2 Recap | HTTP/HTTPS & REST API CRUD prerequisite | `/api/products`, `/api/users`, `/api/profiles`, `/api/orders`, `/api/transactions`, dan masing-masing `/{id}` untuk `GET/PUT/PATCH/DELETE` |
| 3 | WebSocket & Real-Time Communication | `ws://localhost:8088/ws/echo?channel=...`, `/api/websocket/real-status`, `/api/websocket/real-send`, `/api/realtime/events` |
| 4 | MQTT & IoT Telemetry Simulator + Real MQTT Packet Capture | `/api/mqtt/publish`, `/api/mqtt/real-status`, `/api/mqtt/real-publish`, `/api/mqtt/session/start`, `/api/mqtt/session/status`, `/api/mqtt/session/stop`, `/api/mqtt/messages?topic=...`, `/api/mqtt/topics`; real MQTT broker runs inside `server.py` on port `1883` |
| 5 | gRPC/Protobuf Concept + Integrated Real HTTP/2 | `/api/grpc/proto`, `/api/grpc/services`, `/api/grpc/infer`, `/api/grpc/call`, `/api/grpc/http2-status`, `/api/grpc/http2-call`; real gRPC HTTP/2 runs inside `server.py` on port `50051` |
| 6 | JSON/XML/Protobuf/Data Encoding | `/api/exchange/json`, `/api/exchange/xml`, `/api/exchange/protobuf-schema`, `/api/encoding/convert` |
| 7 | TLS/HTTP Troubleshooting & UTS Prep | `/api/tls/status`, `/api/tls/self-test`, `/api/health`, `/api/troubleshooting/status/{code}`, `/api/troubleshooting/slow?ms=1000`, `/api/troubleshooting/test` |
| 8 | UTS Case Evidence | `/api/uts/cases`, `/api/users`, `/api/profiles`, `/api/orders`, `/api/transactions`, `/api/uts/orders`, `/api/webhook/inbox`, `/api/uts/evidence` |
| 9 | API Design & Documentation using Postman/Newman | `/api/openapi`, `/api/postman-run-summary`, `/api/postman/run` |
| 10 | Rate Limiting & Load Balancing | `/api/reliability/rate-limited`, `/api/reliability/load-balanced`, `/api/reliability/simulate-load` |
| 11 | Microservices Communication Patterns | `/api/microservices/order-flow`, `/api/microservices/orders` with `wireCapture: true` |
| 12 | Monitoring, Logging, Telemetry & Observability | `/api/observability/metrics`, `/api/observability/logs`, `/api/observability/trace/{id}`, `/api/observability/custom-log`, `/api/observability/capture-scenario` |
| 13-15 | n8n Automation, Project Phase & Peer Review | `/api/automation/n8n-workflow-spec`, `/api/automation/inbox`, `/api/automation/workflow-run` |
| 16 | UAS Final Project Presentation | `/api/project/events`, `/api/project/summary`, `/api/project/capture-demo` |

## Wireshark Capture Matrix

Endpoint cepat:

```http
GET http://127.0.0.1:8088/api/capture/matrix
```

Filter inti:

| Protocol | Trigger | Wireshark filter |
|---|---|---|
| WebSocket | `POST /api/websocket/real-send` | `tcp.port == 8088`, lalu `websocket` setelah HTTP Upgrade terbaca |
| MQTT | `POST /api/mqtt/session/start` untuk persistent session atau `POST /api/mqtt/real-publish` untuk one-shot | `tcp.port == 1883`, `mqtt` |
| gRPC HTTP/2 | `POST /api/grpc/http2-call` | `tcp.port == 50051`, `http2` |
| TLS | `POST /api/tls/self-test` | `tcp.port == 8443`, `tls`, `tls.handshake` |
| HTTP/JSON/XML/CSV | halaman P6-P16 HTTP endpoints | `tcp.port == 8088`, `http` |

## Postman

Import collection:

```text
postman/Communication_Protocols_Demo_App.postman_collection.json
```

Variable default:

```text
base_url = http://localhost:8088
```

## UTS REST API Case Endpoints

Mahasiswa tidak hanya memakai `products`. Demo app menyediakan beberapa case resource yang bisa diuji dengan Postman menggunakan method `GET`, `POST`, `PUT`, `PATCH`, dan `DELETE`.

| Case | Collection endpoint | Item endpoint | Required fields untuk POST/PUT |
|---|---|---|---|
| Product/inventory | `/api/products` | `/api/products/1` | `name`, `category`, `price`, `stock` |
| User/account | `/api/users` | `/api/users/1` | `username`, `email`, `role` |
| User profile | `/api/profiles` | `/api/profiles/1` | `userId`, `fullName`, `program`, `semester` |
| Order | `/api/orders` | `/api/orders/1` | `customer`, `amount`, `status` |
| Transaction/payment | `/api/transactions` | `/api/transactions/1` | `orderId`, `method`, `amount`, `status` |

Shortcut classroom yang juga disediakan:

```text
/api/user/profile
/api/user/profile/1
/api/order/transaction
/api/order/transaction/1
```

Di web UI, buka `P2 REST Recap` atau `P8 UTS Evidence`, lalu gunakan `Quick UTS Method Matrix`. Tombol `DELETE` di UI membuat temporary record terlebih dahulu lalu menghapus record itu, sehingga demo bisa diulang tanpa error karena data seed sudah terhapus.

## Revisi Lab Pertemuan 3-4

Panduan praktikum interaktif yang sudah mengikuti revisi:

```text
LAB_PERTEMUAN_3_4_REVISI.md
```

## Revisi Advanced P3-P16

Panduan detail untuk demo yang lebih komprehensif, termasuk pilihan `GET`/`POST`, topic/channel/message berbeda, failure scenario, runner simulation, observability, dan n8n workflow:

```text
LAB_ADVANCED_INTERACTIVE_P3_P16.md
```

## Lab Post-UTS dan n8n Automation

Panduan praktikum setelah UTS yang diselaraskan dengan RPS:

```text
LAB_POST_UTS_N8N_AUTOMATION.md
```

## Catatan Teknis

- App utama tetap berjalan dengan Python, tetapi real gRPC HTTP/2 Pertemuan 5 membutuhkan `grpcio` dan `protobuf` dari `requirements.txt`.
- P5 gRPC tidak membutuhkan edit `.proto` untuk demo standar. Gunakan dropdown method di UI atau Postman: `Predict` untuk satu request, `BatchPredict` untuk beberapa request di `items[]`, dan `HealthCheck` untuk cek status service.
- BatchPredict memakai sample `items[]` otomatis dari UI `Quick Invoke`, sehingga output tidak kosong saat demo kelas.
- HealthCheck memakai empty request `{}` dan output normalnya adalah `status: SERVING`.
- WebSocket echo memiliki heartbeat setiap 15 detik dan server ping keepalive. Jika `websocket` belum muncul di Wireshark, gunakan `tcp.port == 8088`, cari request `GET /ws/echo`, lalu **Decode As... HTTP**.
- MQTT page memiliki tiga mode: HTTP simulator untuk topic/filter evidence, one-shot MQTT packet trigger melalui `/api/mqtt/real-publish`, dan persistent MQTT session melalui `/api/mqtt/session/start`. Untuk demo yang tidak disconnect, gunakan **Start Persistent MQTT Session** lalu capture `PINGREQ`/`PINGRESP` pada port `1883`.
- gRPC page memiliki dua mode: concept mock HTTP/1.1 untuk Postman/browser, dan trigger real gRPC HTTP/2 melalui `/api/grpc/http2-call`. Capture Wireshark tetap dilakukan pada `tcp.port == 50051`.
- Di web UI, gunakan `Quick Invoke` untuk menjalankan `Predict`, `BatchPredict`, dan `HealthCheck` secara eksplisit. Jika real HTTP/2 server tidak aktif karena port `50051` bentrok, response akan menampilkan `fallbackConceptResponse` agar demo browser tidak menggantung.
- TLS server memakai self-signed classroom certificate. Browser/curl mungkin memberi warning sertifikat; untuk Wireshark cukup inspeksi TLS handshake di port `8443`.
- REST API CRUD disediakan sebagai halaman recap Pertemuan 2/prerequisite, bukan materi utama Pertemuan 3-16.
- n8n automation membutuhkan instalasi n8n terpisah. Jika n8n berjalan di Docker, gunakan `host.docker.internal:8088` untuk mengakses app ini dari container.
