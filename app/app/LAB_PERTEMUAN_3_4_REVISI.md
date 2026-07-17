# Revisi Lab Praktikum Interaktif

Fokus revisi:

- Pertemuan 3: WebSocket dan Real-Time Communication.
- Pertemuan 4: MQTT dan IoT Telemetry.

App lokal:

```text
http://localhost:8088
```

Catatan revisi advanced: untuk runbook lengkap P3-P16 dengan variasi `GET`/`POST`, topic, channel, payload, failure scenario, observability, dan n8n, gunakan:

```text
LAB_ADVANCED_INTERACTIVE_P3_P16.md
```

Jalankan server:

```powershell
cd "C:\Users\Yenny-Haikal\OneDrive\Documents\New project\communication-protocols-demo-app"
py server.py
```

## Pertemuan 3 - WebSocket dan Real-Time Communication

### Tujuan Lab

Mahasiswa mampu menjelaskan dan mendemokan perbedaan komunikasi HTTP request-response dengan WebSocket persistent connection.

### Scenario Dunia Kerja

Sebuah real-time dashboard perlu menerima event seperti order baru, alert telemetry, atau update status tanpa refresh halaman berulang.

### Mapping RPS

| Elemen | Mapping |
|---|---|
| CPMK | CPMK-1, CPMK-3 |
| Sub-CPMK | Sub-CPMK2, Sub-CPMK5 |
| Fokus | WebSocket, real-time communication, persistent connection, message event |

### Tools

| Tool | Fungsi |
|---|---|
| Demo App browser UI | Demo connect/send/receive WebSocket |
| Postman WebSocket request | Alternatif client WebSocket |
| Wireshark | Capture HTTP Upgrade handshake dan WebSocket text frame |

### Endpoint

```text
ws://localhost:8088/ws/echo
GET http://localhost:8088/api/websocket/real-status
POST http://localhost:8088/api/websocket/real-send
```

### Alur Demo Dosen

1. Buka `http://localhost:8088`.
2. Pilih menu **P3 WebSocket**.
3. Klik **Connect**.
4. Kirim message:

```json
{
  "event": "dashboard_refresh",
  "value": 1
}
```

5. Tunjukkan log `SEND` dan `RECV`.
6. Jelaskan bahwa koneksi tetap terbuka setelah message pertama.
7. Kirim message kedua:

```json
{
  "event": "new_order",
  "orderId": "ORD-2026-001"
}
```

8. Untuk Wireshark evidence yang paling stabil, start capture di `Npcap Loopback Adapter`, lalu klik **Send Real WebSocket Capture**.
9. Filter `tcp.port == 8088`, cari `GET /ws/echo?channel=dashboard`, lalu pastikan ada `101 Switching Protocols`.
10. Setelah handshake terlihat, gunakan display filter `websocket` untuk melihat text frame.
11. Biarkan koneksi idle selama minimal 30 detik. UI akan mengirim heartbeat setiap 15 detik dan server juga mengirim WebSocket ping keepalive.
12. Tutup koneksi dengan tombol **Close**.

Wireshark filter:

```text
tcp.port == 8088
http.request.uri contains "/ws/echo"
http.header contains "Upgrade"
websocket
```

Jika `websocket` belum muncul, gunakan `tcp.port == 8088`, klik kanan paket port 8088, pilih **Decode As...**, lalu set sebagai `HTTP`. WebSocket baru terlihat setelah handshake `101 Switching Protocols` ikut tertangkap.

Catatan: koneksi tidak lagi diputus otomatis saat idle. Jika tertutup, cek apakah browser tab ditutup, tombol **Close** ditekan, atau server dihentikan.

### Alternatif Menggunakan Postman

1. Buka Postman.
2. Klik **New**.
3. Pilih **WebSocket**.
4. Masukkan URL:

```text
ws://localhost:8088/ws/echo
```

5. Klik **Connect**.
6. Kirim payload:

```json
{
  "event": "sensor_alert",
  "deviceId": "sensor-01",
  "temperature": 38.5
}
```

7. Amati echo response.

### Aktivitas Mahasiswa

| Tahap | Aktivitas |
|---|---|
| Guided | Connect ke WebSocket endpoint dari browser UI. |
| Guided | Kirim 2 message JSON berbeda. |
| Independent | Ubah event menjadi `chat.message`, `dashboard.refresh`, atau `order.created`. |
| Evidence | Screenshot connected state, sent message, received message. |
| Reflection | Jelaskan kapan WebSocket lebih tepat daripada REST polling. |

### Expected Output

Contoh response:

```json
{
  "type": "echo",
  "receivedAt": "2026-05-26T...",
  "message": "{\"event\":\"dashboard_refresh\",\"value\":1}"
}
```

### Common Mistakes

| Masalah | Penyebab | Solusi |
|---|---|---|
| Tidak bisa connect | Server belum jalan | Jalankan `py server.py` |
| URL salah | Pakai `http://` bukan `ws://` | Gunakan `ws://localhost:8088/ws/echo` |
| Tidak ada response | Belum klik Connect | Connect dulu, baru Send |
| Mengira WebSocket sama dengan REST | Mental model masih request-response | Tekankan persistent connection dan event stream |

### Pertanyaan Pemantik

1. Mengapa WebSocket cocok untuk notification dan dashboard?
2. Apa risiko persistent connection jika jumlah user sangat banyak?
3. Kapan REST polling masih lebih sederhana dibanding WebSocket?

### Deliverables

1. Screenshot WebSocket connected.
2. Screenshot minimal 2 message sent/received.
3. Tabel perbandingan REST polling vs WebSocket.
4. Screenshot Wireshark `101 Switching Protocols`.
5. Screenshot Wireshark `WebSocket Text`.
6. Refleksi 1 paragraf.

### Rubrik Singkat

| Komponen | Bobot |
|---|---:|
| Koneksi dan message WebSocket berhasil | 35% |
| Evidence lengkap | 25% |
| Penjelasan persistent connection | 25% |
| Reflection/troubleshooting | 15% |

## Pertemuan 4 - MQTT dan IoT Telemetry

### Tujuan Lab

Mahasiswa mampu menjelaskan konsep publish/subscribe, topic, broker, telemetry payload, dan penggunaan MQTT dalam IoT data pipeline.

### Scenario Dunia Kerja

Sensor ruangan mengirim temperature dan humidity secara berkala. Data tersebut masuk ke broker lalu dibaca oleh subscriber untuk dashboard atau data science pipeline.

### Mapping RPS

| Elemen | Mapping |
|---|---|
| CPMK | CPMK-1, CPMK-3 |
| Sub-CPMK | Sub-CPMK2, Sub-CPMK5 |
| Fokus | MQTT, IoT telemetry, topic, broker, publisher, subscriber, QoS basic |

### Tools

| Tool | Fungsi |
|---|---|
| Demo App MQTT simulator | Memahami topic dan publish/subscribe tanpa setup broker |
| Postman | Publish telemetry dan read message list |
| MQTTX/HiveMQ optional | Untuk demo MQTT asli |

### Endpoint Simulator

Publish:

```text
POST http://localhost:8088/api/mqtt/publish
GET http://localhost:8088/api/mqtt/real-status
POST http://localhost:8088/api/mqtt/real-publish
GET http://localhost:8088/api/mqtt/session/status
POST http://localhost:8088/api/mqtt/session/start
POST http://localhost:8088/api/mqtt/session/stop
```

Read messages:

```text
GET http://localhost:8088/api/mqtt/messages?topic=class/commproto/sensor-01/temperature
```

Clear:

```text
POST http://localhost:8088/api/mqtt/clear
```

Catatan: `POST /api/mqtt/publish` adalah simulator MQTT-style berbasis HTTP untuk konsep topic/filter. Untuk packet capture MQTT asli singkat, gunakan `POST /api/mqtt/real-publish`. Untuk session yang tidak disconnect saat demo, gunakan **Start Persistent MQTT Session** atau `POST /api/mqtt/session/start`; `server.py` menjalankan embedded MQTT broker pada `127.0.0.1:1883`.

Wireshark persistent session:

```text
tcp.port == 1883
mqtt
```

Packet yang harus terlihat: `CONNECT`, `CONNACK`, `SUBSCRIBE`, `SUBACK`, `PUBLISH`, lalu `PINGREQ` dan `PINGRESP` berulang selama session aktif. Klik **Stop MQTT Session** untuk menutup session secara eksplisit.

### Alur Demo Dosen di Browser UI

1. Buka `http://localhost:8088`.
2. Pilih menu **P4 MQTT IoT**.
3. Isi topic:

```text
class/commproto/sensor-01/temperature
```

4. Isi payload:

```json
{
  "deviceId": "sensor-01",
  "temperature": 27.5,
  "humidity": 61
}
```

5. Klik **Publish**.
6. Klik **Load Messages**.
7. Tunjukkan message masuk ke topic yang sama.
8. Ubah topic menjadi:

```text
class/commproto/sensor-02/temperature
```

9. Publish payload baru.
10. Jelaskan bahwa subscriber hanya menerima message pada topic yang diikuti.

### Alur Menggunakan Postman

Request:

```text
POST {{base_url}}/api/mqtt/publish
```

Body:

```json
{
  "topic": "class/commproto/sensor-01/temperature",
  "payload": {
    "deviceId": "sensor-01",
    "temperature": 27.5,
    "humidity": 61
  }
}
```

Expected:

```text
201 Created
```

Verification:

```text
GET {{base_url}}/api/mqtt/messages?topic=class/commproto/sensor-01/temperature
```

Expected:

```json
{
  "count": 1,
  "topic": "class/commproto/sensor-01/temperature",
  "messages": [...]
}
```

### Aktivitas Mahasiswa

| Tahap | Aktivitas |
|---|---|
| Guided | Publish telemetry ke topic sensor-01. |
| Guided | Load messages untuk topic yang sama. |
| Independent | Buat topic sensor-02 dan publish payload berbeda. |
| Independent | Bandingkan hasil read topic sensor-01 dan sensor-02. |
| Evidence | Screenshot POST publish, GET messages, dan topic difference. |
| Reflection | Jelaskan mengapa topic naming penting untuk IoT telemetry. |

### Expected Output

Contoh publish response:

```json
{
  "id": 1779460782885,
  "topic": "class/commproto/sensor-01/temperature",
  "payload": {
    "deviceId": "sensor-01",
    "temperature": 27.5,
    "humidity": 61
  },
  "publishedAt": "2026-05-26T..."
}
```

### Common Mistakes

| Masalah | Penyebab | Solusi |
|---|---|---|
| `400 topic and payload are required` | Body tidak punya `topic` atau `payload` | Perbaiki JSON body |
| Message tidak muncul | Topic GET berbeda dengan topic publish | Copy-paste topic secara persis |
| JSON invalid | Koma/tanda kutip salah | Gunakan Body -> raw -> JSON di Postman |
| Menganggap simulator HTTP sebagai MQTT asli | Endpoint `/api/mqtt/publish` berjalan di HTTP | Gunakan `/api/mqtt/real-publish` dan capture port `1883` |
| Filter `mqtt` kosong | Capture tidak di port broker atau belum decode | Gunakan `tcp.port == 1883`, lalu **Decode As... MQTT** jika perlu |
| Session MQTT putus setelah idle | Menggunakan versi lama atau client tidak mengirim keepalive | Gunakan `Start Persistent MQTT Session`; broker internal sekarang idle timeout 5 menit dan session mengirim `PINGREQ` tiap 15 detik |

### Pertanyaan Pemantik

1. Mengapa MQTT memakai broker?
2. Apa fungsi topic hierarchy dalam IoT telemetry?
3. Apa bedanya publisher dan subscriber?
4. Dalam konteks data science, telemetry ini bisa dipakai untuk analisis apa?

### Deliverables

1. Screenshot publish telemetry.
2. Screenshot read messages by topic.
3. Dua topic berbeda dan dua payload berbeda.
4. Penjelasan topic naming.
5. Screenshot Wireshark `mqtt` atau `tcp.port == 1883`.
6. Screenshot `PINGREQ`/`PINGRESP` dari persistent session.
7. Refleksi perbedaan REST request-response dan MQTT pub/sub.

### Rubrik Singkat

| Komponen | Bobot |
|---|---:|
| Publish/subscribe simulator berhasil | 35% |
| Topic naming dan payload benar | 25% |
| Evidence lengkap | 20% |
| Analisis REST vs MQTT | 15% |
| Troubleshooting note | 5% |

## Catatan Delivery untuk Dosen

Urutan kelas yang disarankan:

1. Pertemuan 3: mulai dari masalah dashboard yang butuh update real-time, lalu demo WebSocket.
2. Pertemuan 4: mulai dari masalah sensor telemetry, lalu demo MQTT topic publish/subscribe.
3. Jangan masuk terlalu dalam ke scaling dan broker internals. Fokus pada mental model.
4. Tekankan evidence: WebSocket harus punya `101 Switching Protocols`; MQTT harus punya packet di port `1883`, bukan hanya response HTTP simulator.
