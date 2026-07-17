# Panduan MacBook Apple Silicon M4 Pro
## Communication Protocols Demo App + n8n Self-Hosted Community Free

Dokumen ini adalah quick-start khusus macOS Apple Silicon (M1/M2/M3/M4), termasuk MacBook Pro M4 Pro.

---

## 1. Prasyarat

Install komponen berikut:

1. Docker Desktop for Mac - pilih versi Apple Silicon.
2. Python 3 latest stable untuk macOS arm64.
3. Postman Desktop.
4. Terminal bawaan macOS.

Validasi cepat:

```bash
python3 --version
docker --version
docker compose version
uname -m
```

Expected:

```text
uname -m -> arm64
```

---

## 2. Jalankan Demo App

Dari folder package:

```bash
chmod +x scripts/start_app_macos_apple_silicon.sh
./scripts/start_app_macos_apple_silicon.sh
```

Aplikasi akan berjalan di:

```text
http://localhost:8088
```

Smoke test dari Terminal baru:

```bash
chmod +x scripts/smoke_test_macos_apple_silicon.sh
./scripts/smoke_test_macos_apple_silicon.sh
```

---

## 3. Jalankan n8n Self-Hosted Community Free

Buka Docker Desktop dulu sampai status engine running.

Dari folder package:

```bash
chmod +x scripts/run_n8n_macos_apple_silicon.sh
./scripts/run_n8n_macos_apple_silicon.sh
```

Buka:

```text
http://localhost:5678
```

Alternatif Docker Compose:

```bash
chmod +x scripts/run_n8n_macos_compose.sh
./scripts/run_n8n_macos_compose.sh
```

---

## 4. URL yang sering tertukar

### Postman ke n8n Webhook

Karena Postman berjalan di host MacBook, gunakan:

```text
http://localhost:5678/webhook-test/commproto-p10
```

### n8n Docker container ke Demo App di MacBook

Karena n8n berjalan di container, gunakan di node HTTP Request:

```text
http://host.docker.internal:8088/api/reliability/rate-limited
```

Jangan pakai `localhost:8088` dari dalam HTTP Request node n8n, karena `localhost` di sana berarti container n8n, bukan MacBook host.

---

## 5. Import Postman Environment untuk Mac

Import file:

```text
postman/CommProto_Local_Mac_Apple_Silicon.postman_environment.json
```

Pilih environment:

```text
CommProto Local - Mac Apple Silicon
```

Variable penting:

```text
base_url = http://localhost:8088
n8n_webhook_url = http://localhost:5678/webhook-test/commproto-p10
n8n_to_host_base_url = http://host.docker.internal:8088
```

Jika muncul error `getaddrinfo ENOTFOUND {{n8n_webhook_url}}`, artinya environment belum dipilih atau variable belum dibuat.

---

## 6. Import Workflow n8n

Di n8n:

```text
Workflows -> Import from File
```

Pilih:

```text
n8n/P10_API_Reliability_Workflow_n8n_template.json
```

Buka node HTTP Request, pastikan URL target:

```text
http://host.docker.internal:8088/api/reliability/rate-limited
```

Untuk testing:

1. Buka Webhook node.
2. Klik `Listen for test event`.
3. Copy Test URL.
4. Kirim request dari Postman.

---

## 7. Test payload Postman ke n8n

Method:

```text
POST
```

URL:

```text
{{n8n_webhook_url}}
```

Header:

```text
Content-Type: application/json
```

Body:

```json
{
  "clientId": "kelompok-01",
  "scenario": "rate-limit",
  "timestamp": "2026-06-18T20:00:00+07:00"
}
```

---

## 8. Evidence yang harus ditunjukkan mahasiswa

1. Demo App aktif di `http://localhost:8088/api/health`.
2. n8n aktif di `http://localhost:5678`.
3. Webhook node menerima input dari Postman.
4. HTTP Request node memanggil Demo App via `host.docker.internal`.
5. IF node memisahkan success dan error branch.
6. Postman menampilkan response akhir dari n8n.
7. Execution log n8n dapat dibaca sebagai evidence observability.

---

## 9. Troubleshooting cepat

### Docker image lambat saat pertama kali jalan

Normal. Docker harus pull image n8n pertama kali.

### n8n tidak bisa buka localhost:5678

Cek:

```bash
docker ps
```

Pastikan container `n8n` running dan port `5678->5678` terlihat.

### HTTP Request node gagal connect ke Demo App

Cek Demo App:

```bash
curl http://localhost:8088/api/health
```

Di HTTP Request node n8n, gunakan:

```text
http://host.docker.internal:8088/api/health
```

### Webhook tidak menerima request

Pastikan:

1. Klik `Listen for test event`.
2. Postman pakai method POST.
3. URL Postman pakai Test URL `/webhook-test/commproto-p10`.
4. Body raw JSON.
5. Header `Content-Type: application/json`.

---

## 10. Command stop

Stop n8n:

```bash
./scripts/stop_n8n_macos.sh
```

Data workflow tetap tersimpan di Docker volume:

```text
n8n_data
```

Hapus data n8n hanya jika benar-benar perlu:

```bash
./scripts/reset_n8n_volume_macos_DANGER.sh
```
