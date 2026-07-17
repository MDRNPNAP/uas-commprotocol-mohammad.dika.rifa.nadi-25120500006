# Lab P5 - Integrated gRPC HTTP/2

Folder ini sudah deprecated untuk eksekusi `server.py` dan `client.py` terpisah.

Jalur resmi praktikum sekarang:

```powershell
cd "C:\Users\Yenny-Haikal\OneDrive\Documents\New project\communication-protocols-demo-app"
py -m pip install -r requirements.txt
py server.py
```

Satu script root `server.py` akan menjalankan:

- HTTP teaching UI/API: `http://127.0.0.1:8088`
- Real gRPC HTTP/2 server: `127.0.0.1:50051`

Untuk generate traffic gRPC HTTP/2, gunakan UI P5 atau Postman:

```http
POST http://127.0.0.1:8088/api/grpc/http2-call
```

Payload contoh:

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

Wireshark:

```text
tcp.port == 50051
```

Jika belum terbaca sebagai HTTP/2, gunakan **Decode As...** lalu set TCP port `50051` sebagai `HTTP2`, kemudian filter:

```text
http2
```

Catatan penting: request ke `8088` tetap HTTP/1.1 karena itu trigger dari browser/Postman. Traffic real gRPC HTTP/2 muncul pada port `50051`.
