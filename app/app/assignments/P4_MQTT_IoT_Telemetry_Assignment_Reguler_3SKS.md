# Tugas Praktikum Pertemuan 4

## MQTT dan IoT Telemetry untuk Data Science

Mata kuliah: Communication Protocols  
Program studi: Sains Data  
Kelas: Reguler  
Bobot: 3 SKS  
Pertemuan: P4  
Sifat tugas: Individu  
Estimasi pengerjaan: 90 sampai 120 menit  

## 1. Tujuan Pembelajaran

Setelah menyelesaikan tugas ini, mahasiswa mampu:

1. Menjelaskan konsep MQTT sebagai publish/subscribe protocol.
2. Membedakan publisher, subscriber, broker, topic, topic filter, QoS, dan retained message.
3. Mengirim telemetry payload dengan topic berbeda.
4. Membaca packet MQTT menggunakan Wireshark.
5. Menjelaskan hubungan MQTT telemetry dengan data science pipeline.

## 2. Skenario Dunia Kerja

Anda adalah junior data engineer pada tim Smart Campus Monitoring. Tim Anda mengumpulkan data sensor dari beberapa ruangan kampus, seperti temperature, humidity, battery level, dan device status.

Data sensor dikirim menggunakan MQTT karena perangkat IoT perlu protokol yang ringan, event-driven, dan cocok untuk komunikasi telemetry. Tugas Anda adalah membuat simulasi telemetry, menguji topic dan payload, lalu membuktikan bahwa packet MQTT benar-benar muncul di Wireshark.

## 3. Tools yang Digunakan

1. Communication Protocols Demo App lokal.
2. Browser.
3. Postman optional.
4. Wireshark.
5. Npcap Loopback Adapter untuk Windows.

## 4. Setup Awal

Jalankan server:

```powershell
cd "C:\Users\Yenny-Haikal\OneDrive\Documents\New project\communication-protocols-demo-app"
py -m pip install -r requirements.txt
py server.py
```

Buka browser:

```text
http://localhost:8088
```

Pilih menu:

```text
P4 MQTT IoT
```

## 5. Endpoint Penting

HTTP simulator untuk konsep publish/read:

```http
POST /api/mqtt/publish
GET /api/mqtt/messages?topic=class/commproto/sensor-01/temperature
GET /api/mqtt/messages?filter=class/commproto/+/temperature
GET /api/mqtt/topics
```

Real MQTT packet capture:

```http
GET /api/mqtt/real-status
POST /api/mqtt/real-publish
POST /api/mqtt/session/start
GET /api/mqtt/session/status
POST /api/mqtt/session/stop
```

## 6. Instruksi Praktikum

### Bagian A - Publish Telemetry dengan HTTP Simulator

1. Buka halaman P4 MQTT IoT.
2. Isi Client ID:

```text
student-client-NIM
```

3. Isi topic pertama:

```text
class/commproto/sensor-01/temperature
```

4. Isi payload JSON:

```json
{
  "deviceId": "sensor-01",
  "room": "lab-data-01",
  "temperature": 27.5,
  "humidity": 61,
  "battery": 92
}
```

5. Pilih QoS 1.
6. Centang retained message.
7. Klik Publish.
8. Klik Load Messages.
9. Screenshot hasil publish dan hasil Load Messages.

### Bagian B - Publish Telemetry Kedua dengan Topic Berbeda

1. Ubah topic:

```text
class/commproto/sensor-02/humidity
```

2. Ubah payload:

```json
{
  "deviceId": "sensor-02",
  "room": "lab-data-02",
  "temperature": 26.9,
  "humidity": 72,
  "battery": 88
}
```

3. Klik Publish.
4. Klik Load Topics.
5. Screenshot topic list.

### Bagian C - Topic Filter

1. Isi Subscribe Filter:

```text
class/commproto/+/temperature
```

2. Klik Load by Filter.
3. Amati message mana yang muncul.
4. Jelaskan mengapa topic `sensor-01/temperature` match, tetapi `sensor-02/humidity` tidak match.

### Bagian D - Real MQTT Packet Capture

1. Buka Wireshark.
2. Pilih Npcap Loopback Adapter.
3. Start capture.
4. Pada demo app, klik Start Persistent MQTT Session.
5. Tunggu minimal 30 detik.
6. Gunakan display filter:

```text
mqtt
```

Jika filter `mqtt` belum muncul, gunakan:

```text
tcp.port == 1883
```

Jika masih belum decode, gunakan Decode As, lalu pilih MQTT untuk TCP port 1883.

7. Cari packet berikut:

```text
CONNECT
CONNACK
SUBSCRIBE
SUBACK
PUBLISH
PINGREQ
PINGRESP
```

8. Screenshot packet `PUBLISH`.
9. Screenshot packet `PINGREQ` dan `PINGRESP`.
10. Klik Stop MQTT Session setelah selesai.

## 7. Pertanyaan Analisis

Jawab singkat dalam laporan:

1. Apa perbedaan MQTT dengan REST API dari sisi communication pattern?
2. Apa fungsi broker dalam MQTT?
3. Apa fungsi topic hierarchy?
4. Apa arti wildcard `+` pada topic filter?
5. Mengapa MQTT cocok untuk IoT telemetry?
6. Mengapa PINGREQ dan PINGRESP penting pada persistent session?
7. Dalam konteks data science, telemetry ini dapat digunakan untuk analisis apa?

## 8. Deliverables

Upload satu file PDF laporan ke LMS dengan isi:

1. Identitas mahasiswa: nama, NIM, kelas.
2. Screenshot halaman P4 MQTT IoT.
3. Screenshot publish telemetry sensor-01.
4. Screenshot publish telemetry sensor-02.
5. Screenshot Load Messages.
6. Screenshot Load by Filter.
7. Screenshot Load Topics.
8. Screenshot Wireshark filter `mqtt` atau `tcp.port == 1883`.
9. Screenshot packet `PUBLISH`.
10. Screenshot packet `PINGREQ` dan `PINGRESP`.
11. Jawaban pertanyaan analisis.
12. Troubleshooting note jika ada error.

Nama file:

```text
P4_MQTT_NIM_Nama.pdf
```

## 9. Rubrik Penilaian

| Komponen | Bobot | Kriteria |
|---|---:|---|
| Konsep MQTT | 20% | Menjelaskan broker, publisher, subscriber, topic, QoS, retained message dengan benar. |
| Eksekusi lab | 25% | Berhasil publish minimal dua topic dan payload berbeda. |
| Topic filter | 15% | Memahami match topic menggunakan wildcard `+`. |
| Evidence Wireshark | 25% | Menunjukkan packet MQTT nyata, termasuk PUBLISH dan PINGREQ/PINGRESP. |
| Analisis data science | 10% | Menghubungkan telemetry dengan use case data pipeline atau monitoring. |
| Kerapian laporan | 5% | PDF rapi, screenshot terbaca, dan penamaan file sesuai. |

Total: 100%

## 10. Common Mistakes dan Troubleshooting

| Masalah | Penyebab Umum | Solusi |
|---|---|---|
| Filter `mqtt` kosong | Wireshark belum decode MQTT | Gunakan `tcp.port == 1883`, lalu Decode As MQTT. |
| Tidak ada packet MQTT | Capture bukan di loopback adapter | Pilih Npcap Loopback Adapter. |
| Session cepat putus | Tidak memakai persistent session | Klik Start Persistent MQTT Session. |
| Payload error | JSON tidak valid | Cek koma, tanda kutip, dan struktur object. |
| Topic filter tidak match | Topic berbeda struktur | Bandingkan segment topic satu per satu. |

## 11. Catatan Akademik

Tugas ini bersifat individu. Screenshot harus berasal dari perangkat atau sesi praktikum masing-masing mahasiswa. Mahasiswa boleh berdiskusi, tetapi laporan dan evidence harus dibuat sendiri.

## 12. Referensi Singkat

OASIS. (2014). MQTT Version 3.1.1. OASIS Standard. https://docs.oasis-open.org/mqtt/mqtt/v3.1.1/os/mqtt-v3.1.1-os.html

Wireshark Foundation. (n.d.). Wireshark User's Guide. https://www.wireshark.org/docs/wsug_html_chunked/

