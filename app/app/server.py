from concurrent import futures
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse, parse_qs
import base64
import hashlib
import json
import os
import shutil
import socket
import socketserver
import ssl
import struct
import threading
import time

try:
    import grpc
    from google.protobuf import descriptor_pb2, descriptor_pool, json_format, message_factory
except ImportError:
    grpc = None
    descriptor_pb2 = None
    descriptor_pool = None
    json_format = None
    message_factory = None


ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
STATIC = ROOT / "static"
PRODUCTS = DATA / "products.json"
PRODUCTS_SEED = DATA / "products.seed.json"
USERS = DATA / "users.json"
USERS_SEED = DATA / "users.seed.json"
PROFILES = DATA / "profiles.json"
PROFILES_SEED = DATA / "profiles.seed.json"
ORDERS = DATA / "orders.json"
ORDERS_SEED = DATA / "orders.seed.json"
TRANSACTIONS = DATA / "transactions.json"
TRANSACTIONS_SEED = DATA / "transactions.seed.json"
MESSAGES = DATA / "messages.json"
WEBHOOK_INBOX = DATA / "webhook_inbox.json"
AUTOMATION_INBOX = DATA / "automation_inbox.json"
REALTIME_EVENTS = DATA / "realtime_events.json"
HOST = os.environ.get("COMM_PROTO_HOST", "127.0.0.1")
PORT = 8088
MQTT_PORT = 1883
GRPC_PORT = 50051
TLS_PORT = 8443
GRPC_SERVICE = "demo.inference.InferenceService"
GRPC_MODEL_VERSION = "integrated-http2-v1"
LOCK = threading.Lock()
WS_GUID = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"
REQUEST_LOGS = []
RATE_HITS = {}
BACKENDS = ["api-node-a", "api-node-b", "api-node-c"]
BACKEND_INDEX = 0
GRPC_MESSAGE_CLASSES = None
TELEMETRY_MESSAGE_CLASSES = None
MQTT_SERVER_ACTIVE = False
TLS_SERVER_ACTIVE = False
GRPC_SERVER_ACTIVE = False
MQTT_DEMO_SESSIONS = {}
WEBSOCKET_KEEPALIVE_SECONDS = 15
MQTT_BROKER_IDLE_TIMEOUT_SECONDS = 300

API_RESOURCES = {
    "products": {
        "file": PRODUCTS,
        "seed": PRODUCTS_SEED,
        "label": "Product",
        "required": ("name", "category", "price", "stock"),
        "allowed": ("name", "category", "price", "stock"),
    },
    "users": {
        "file": USERS,
        "seed": USERS_SEED,
        "label": "User",
        "required": ("username", "email", "role"),
        "allowed": ("username", "email", "role", "status", "department"),
    },
    "profiles": {
        "file": PROFILES,
        "seed": PROFILES_SEED,
        "label": "Profile",
        "required": ("userId", "fullName", "program", "semester"),
        "allowed": ("userId", "fullName", "program", "semester", "skills", "city"),
    },
    "orders": {
        "file": ORDERS,
        "seed": ORDERS_SEED,
        "label": "Order",
        "required": ("customer", "amount", "status"),
        "allowed": ("orderId", "customer", "amount", "status", "items", "channel"),
    },
    "transactions": {
        "file": TRANSACTIONS,
        "seed": TRANSACTIONS_SEED,
        "label": "Transaction",
        "required": ("orderId", "method", "amount", "status"),
        "allowed": ("transactionId", "orderId", "method", "amount", "status", "paidAt", "channel"),
    },
}

RESOURCE_PATH_ALIASES = {
    ("api", "user", "profile"): "profiles",
    ("api", "order", "transaction"): "transactions",
}

TLS_CERT_PEM = """-----BEGIN CERTIFICATE-----
MIIC5DCCAcygAwIBAgIJALCyzDfEOUdsMA0GCSqGSIb3DQEBCwUAMBQxEjAQBgNVBAMTCWxvY2Fs
aG9zdDAeFw0yNjA1MzEwOTU0NDRaFw0zMTA2MDEwOTU0NDRaMBQxEjAQBgNVBAMTCWxvY2FsaG9z
dDCCASIwDQYJKoZIhvcNAQEBBQADggEPADCCAQoCggEBAOWAj6UCbCLbmoDEIcVnUl5qt9uDvdWZ
q/MWqPZp5OpbGcobB6aSjBksfmy+LeYcVHnLXr5BC1ejOohLD0xUbQYUHOD+zuaOgn6jcR4m55no
8o+wx+3eyZPHGZOxaUMqwVWNAVBHQmVnPju+oICXr2hF7KeEeuiFwFIoy6PjZkyGOF33bmBQpiU7
r5jmx12vVoObUiiodqd92AVbN1ULZVD+0dpOqzG9jnNaIwqknqsPyc9g91x0ZwLGAiP6/BKc1g7w
1AUReQg1gYs3bavH3+s7w9ebhss6GLAgBju6jqWk5exyVxz3l5hIcpXfbUFwJ64k+5yHC1rMMMFI
masZaiECAwEAAaM5MDcwGgYDVR0RBBMwEYIJbG9jYWxob3N0hwR/AAABMAkGA1UdEwQCMAAwDgYD
VR0PAQH/BAQDAgWgMA0GCSqGSIb3DQEBCwUAA4IBAQDSFFyvG3JciFW3vZJPz5FMVPfv76L3aSry
irrWkVqq0np9q01mteCb6cm7a2vSKCc8B0tWwXXGzO0+Iq0b25yLpAEH6qOJiP8Ivf5SmM6TXF+A
0PVqqXWeDQbGJsOQ1zc4rBRSf/pQ79/FfldzFDNIDE+PUygwMvhsQ6y0H3z//0qSeAASDN/6CwuP
X1MSH75WEuNfSqjqmUMy8xF5zR+TsOjbUI3zMZ+iMaUeKTk/8yjXxHAO8LUAHW1dhrSkBeslKBTx
xaE4F1LoJw36R0UZaCwy+d6Hpxb63510s5ZErRBaLXDzpvYtCiRCJ6T2WC9FvB+rpkG79bWHGf80
xju8
-----END CERTIFICATE-----"""

TLS_KEY_PEM = """-----BEGIN PRIVATE KEY-----
MIIEvgIBADANBgkqhkiG9w0BAQEFAASCBKgwggSkAgEAAoIBAQDlgI+lAmwi25qAxCHFZ1Jearfb
g73VmavzFqj2aeTqWxnKGwemkowZLH5svi3mHFR5y16+QQtXozqISw9MVG0GFBzg/s7mjoJ+o3Ee
JueZ6PKPsMft3smTxxmTsWlDKsFVjQFQR0JlZz47vqCAl69oReynhHrohcBSKMuj42ZMhjhd925g
UKYlO6+Y5sddr1aDm1IoqHanfdgFWzdVC2VQ/tHaTqsxvY5zWiMKpJ6rD8nPYPdcdGcCxgIj+vwS
nNYO8NQFEXkINYGLN22rx9/rO8PXm4bLOhiwIAY7uo6lpOXsclcc95eYSHKV321BcCeuJPuchwta
zDDBSJmrGWohAgMBAAECggEBAMPKJ8GYDXS3cFnF+SGVgbm2xV9qRrtBPGZHwKFnubkNOzUmViKP
ByI6ySgwHqwfIxo8m3knuGttf3PixQxTQidbZT+1YgFjNoSfHtOgURkGmFhpckbGN6XwxysuwSRi
B0na33IDOOuVZoxFllveC/CjJr/Kz6gq4uW0k/Ye+5jvkmWJHsy/vpM1HEYK0OGys+DdDiFN6ajm
nWPh2iONkcLGL+9K4579AN1LsRPPZNThDqs/77W7xREKMrKzAyE2So9bFFz0I/D2eWkb74nszYce
ddQJ9z1Jo/VoZXyXlMUH4oXiHyDOeU7Db77K4P3TSI38uLHSjdZmL7rM1fxcTpkCgYEA/3rZMqb2
y3KBJ5Wdjn210jYsGcBov8/2KBXRtWBrSXGeAVtkJKpHXXNdlJOrNOEpVugMDobZc31kkW/88QL7
hJJxtKnNc5G2jciyH23Q+ZaQw3wxDIxDnIcbc2KB7CUUFRCARSV0FHxxVSUwIQLq3QCYQocQl8hU
cQcyLApJ9dcCgYEA5fgsb2acHMi1UFkKrkzVKcXOdra19imubn5OpITbyrwhg5fEGJyAwDIRGGFO
J4z5sOPNoSHRJrn514B90dM/bMSyUIqsEyOlOqjh7CDg4NYn+HFSYMqTP3DSHtX5fLASeuE3p2oK
SJ0Ylt5aXxiwgSs47+0Sc8mdVL5cklg1MMcCgYBoJ08xBTyMCKx61NYc50ce4hLslLKfsEqsYOjT
xvE2SemeqAGVqQ3bHVNDZUhhEIJn+cYgjf1Mxgwf9sXqA8tCaumMO8WUng0MlIt5oK2XczilWZYt
hWlzAOnCCqDpAtzDEa0Zg4FlcK5LhhOvAZ96ZemtBZ9QIc27HrHnnnI0lQKBgEvXDWhrsX44nrrx
snkK852EE3PJC7czxcfAtdTBz+5LHs5UBaKMMlWv7T1aEbkvX8T7S3whN+WKnZ95S4UgIqGPOLMh
GGBzd/Ehcug5a5AacDIZxS4QgIEChvkOXenF80I89eqrKNsLm+ldSPZloQfoJi3RxC0VR2KEKOlG
V7xPAoGBALoMM6Leoy1C1kUBvH6pbtf0BEGhacMPkAwYZtNK4Rpo2oAXFvIvc/vmkr/6gBhmRUqh
j5NXamL8b9kT/55bknSF62JVwORUDXOVG36fSrPm0rbr5czleIOjeQ45K9CLiivpuhIcYyOy9KUs
Psi5afL2JeK+DoahB0eut1Rxn84l
-----END PRIVATE KEY-----"""


def now_iso():
    return time.strftime("%Y-%m-%dT%H:%M:%S%z")


def read_json(path):
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def write_json(path, payload):
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)
        handle.write("\n")


def next_id(items):
    return max([item.get("id", 0) for item in items], default=0) + 1


def parse_api_resource_path(path):
    parts = path.strip("/").split("/")
    if len(parts) >= 2 and parts[0] == "api" and parts[1] in API_RESOURCES:
        if len(parts) == 2:
            return parts[1], None, None
        if len(parts) == 3:
            try:
                return parts[1], int(parts[2]), None
            except ValueError:
                return parts[1], None, f"Resource id must be an integer: {parts[2]}"
    alias_resource = RESOURCE_PATH_ALIASES.get(tuple(parts[:3]))
    if alias_resource:
        if len(parts) == 3:
            return alias_resource, None, None
        if len(parts) == 4:
            try:
                return alias_resource, int(parts[3]), None
            except ValueError:
                return alias_resource, None, f"Resource id must be an integer: {parts[3]}"
    return None, None, None


def resource_item(resource, item_id):
    config = API_RESOURCES[resource]
    return next((item for item in read_json(config["file"]) if item.get("id") == item_id), None)


def resource_collection_payload(resource):
    config = API_RESOURCES[resource]
    items = read_json(config["file"])
    return {
        "resource": resource,
        "case": config["label"],
        "count": len(items),
        "methods": ["GET", "POST", "PUT", "PATCH", "DELETE"],
        "canonicalPath": f"/api/{resource}",
        "itemPathExample": f"/api/{resource}/1",
        "data": items,
    }


def resource_cases_payload():
    cases = []
    for name, config in API_RESOURCES.items():
        cases.append({
            "resource": name,
            "case": config["label"],
            "canonicalPath": f"/api/{name}",
            "itemPathExample": f"/api/{name}/1",
            "requiredFields": list(config["required"]),
            "allowedFields": list(config["allowed"]),
            "methods": ["GET", "POST", "PUT", "PATCH", "DELETE"],
        })
    return {
        "message": "UTS demo app now supports multiple REST API case resources, not only products.",
        "cases": cases,
        "classroomShortcutPaths": {
            "/api/user/profile": "Alias for /api/profiles",
            "/api/order/transaction": "Alias for /api/transactions",
        },
    }


def validate_resource_body(resource, body, require_full):
    config = API_RESOURCES[resource]
    allowed = set(config["allowed"])
    invalid = [field for field in body if field not in allowed]
    if invalid:
        return {"error": "Invalid fields", "resource": resource, "invalid": invalid, "allowed": sorted(allowed)}
    if require_full:
        missing = [field for field in config["required"] if field not in body]
        if missing:
            return {"error": "Missing required fields", "resource": resource, "missing": missing}
    return None


def apply_resource_defaults(resource, item):
    timestamp = int(time.time() * 1000)
    if resource == "orders" and "orderId" not in item:
        item["orderId"] = f"ORD-{timestamp}"
    if resource == "transactions" and "transactionId" not in item:
        item["transactionId"] = f"TRX-{timestamp}"
    if resource == "transactions" and "paidAt" not in item and item.get("status") in {"paid", "success", "settled"}:
        item["paidAt"] = now_iso()
    return item


def build_resource_item(resource, item_id, body, timestamp_field):
    config = API_RESOURCES[resource]
    item = {"id": item_id}
    for field in config["allowed"]:
        if field in body:
            item[field] = body[field]
    item[timestamp_field] = now_iso()
    return apply_resource_defaults(resource, item)


def create_resource(resource, body):
    error = validate_resource_body(resource, body, require_full=True)
    if error:
        return 400, error, None
    config = API_RESOURCES[resource]
    with LOCK:
        items = read_json(config["file"])
        item = build_resource_item(resource, next_id(items), body, "createdAt")
        items.append(item)
        write_json(config["file"], items)
    return 201, item, {"Location": f"/api/{resource}/{item['id']}"}


def replace_resource(resource, item_id, body):
    error = validate_resource_body(resource, body, require_full=True)
    if error:
        return 400, error
    config = API_RESOURCES[resource]
    with LOCK:
        items = read_json(config["file"])
        for index, item in enumerate(items):
            if item.get("id") == item_id:
                replacement = build_resource_item(resource, item_id, body, "updatedAt")
                items[index] = replacement
                write_json(config["file"], items)
                return 200, replacement
    return 404, {"error": f"{config['label']} not found", "resource": resource, "id": item_id}


def patch_resource(resource, item_id, body):
    error = validate_resource_body(resource, body, require_full=False)
    if error:
        return 400, error
    config = API_RESOURCES[resource]
    with LOCK:
        items = read_json(config["file"])
        for item in items:
            if item.get("id") == item_id:
                item.update(body)
                apply_resource_defaults(resource, item)
                item["updatedAt"] = now_iso()
                write_json(config["file"], items)
                return 200, item
    return 404, {"error": f"{config['label']} not found", "resource": resource, "id": item_id}


def delete_resource(resource, item_id):
    config = API_RESOURCES[resource]
    with LOCK:
        items = read_json(config["file"])
        remaining = [item for item in items if item.get("id") != item_id]
        if len(remaining) == len(items):
            return 404, {"error": f"{config['label']} not found", "resource": resource, "id": item_id}
        write_json(config["file"], remaining)
    return 204, None


def mqtt_topic_match(topic_filter, topic):
    filter_parts = topic_filter.split("/")
    topic_parts = topic.split("/")
    for index, part in enumerate(filter_parts):
        if part == "#":
            return True
        if index >= len(topic_parts):
            return False
        if part != "+" and part != topic_parts[index]:
            return False
    return len(filter_parts) == len(topic_parts)


def mqtt_encode_remaining_length(length):
    encoded = bytearray()
    while True:
        digit = length % 128
        length //= 128
        if length > 0:
            digit |= 0x80
        encoded.append(digit)
        if length == 0:
            return bytes(encoded)


def mqtt_encode_string(value):
    raw = str(value).encode("utf-8")
    return struct.pack("!H", len(raw)) + raw


def mqtt_read_exact(sock, size):
    chunks = bytearray()
    while len(chunks) < size:
        chunk = sock.recv(size - len(chunks))
        if not chunk:
            raise ConnectionError("MQTT connection closed")
        chunks.extend(chunk)
    return bytes(chunks)


def mqtt_read_packet(sock):
    first = sock.recv(1)
    if not first:
        return None
    multiplier = 1
    remaining_length = 0
    while True:
        encoded = mqtt_read_exact(sock, 1)[0]
        remaining_length += (encoded & 0x7F) * multiplier
        if encoded & 0x80 == 0:
            break
        multiplier *= 128
        if multiplier > 128 * 128 * 128:
            raise ValueError("Malformed MQTT remaining length")
    return first[0], mqtt_read_exact(sock, remaining_length)


def mqtt_decode_string(payload, offset):
    if offset + 2 > len(payload):
        raise ValueError("MQTT string length is incomplete")
    size = struct.unpack("!H", payload[offset:offset + 2])[0]
    offset += 2
    if offset + size > len(payload):
        raise ValueError("MQTT string payload is incomplete")
    return payload[offset:offset + size].decode("utf-8", errors="replace"), offset + size


def mqtt_connect_packet(client_id, keep_alive=60):
    body = (
        mqtt_encode_string("MQTT")
        + bytes([4, 0x02])
        + struct.pack("!H", max(1, min(int(keep_alive), 65535)))
        + mqtt_encode_string(client_id)
    )
    return bytes([0x10]) + mqtt_encode_remaining_length(len(body)) + body


def mqtt_subscribe_packet(topic_filter, packet_id=1, qos=0):
    body = struct.pack("!H", packet_id) + mqtt_encode_string(topic_filter) + bytes([qos])
    return bytes([0x82]) + mqtt_encode_remaining_length(len(body)) + body


def mqtt_publish_packet(topic, payload, qos=0, retained=False, packet_id=2):
    qos = max(0, min(int(qos), 2))
    payload_bytes = payload if isinstance(payload, bytes) else str(payload).encode("utf-8")
    body = mqtt_encode_string(topic)
    if qos:
        body += struct.pack("!H", packet_id)
    body += payload_bytes
    flags = (qos << 1) | (0x01 if retained else 0)
    return bytes([0x30 | flags]) + mqtt_encode_remaining_length(len(body)) + body


def mqtt_pingreq_packet():
    return b"\xc0\x00"


def mqtt_disconnect_packet():
    return b"\xe0\x00"


def mqtt_packet_name(packet_type):
    names = {
        1: "CONNECT",
        2: "CONNACK",
        3: "PUBLISH",
        4: "PUBACK",
        5: "PUBREC",
        6: "PUBREL",
        7: "PUBCOMP",
        8: "SUBSCRIBE",
        9: "SUBACK",
        12: "PINGREQ",
        13: "PINGRESP",
        14: "DISCONNECT",
    }
    return names.get(packet_type, f"TYPE_{packet_type}")


def mqtt_payload_to_json(payload_bytes):
    text = payload_bytes.decode("utf-8", errors="replace")
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return {"text": text}


def store_mqtt_message(client_id, topic, qos, retained, payload, transport):
    message = {
        "id": int(time.time() * 1000),
        "clientId": client_id,
        "topic": topic,
        "qos": qos,
        "retained": bool(retained),
        "payload": payload,
        "publishedAt": now_iso(),
        "transport": transport,
    }
    with LOCK:
        messages = read_json(MESSAGES)
        messages.append(message)
        write_json(MESSAGES, messages)
    return message


def content_type(path):
    suffix = path.suffix.lower()
    if suffix == ".css":
        return "text/css; charset=utf-8"
    if suffix == ".js":
        return "application/javascript; charset=utf-8"
    if suffix == ".html":
        return "text/html; charset=utf-8"
    return "application/octet-stream"


def record_request(method, path, status, response_type):
    entry = {
        "time": now_iso(),
        "method": method,
        "path": path,
        "status": status,
        "responseType": response_type,
    }
    with LOCK:
        REQUEST_LOGS.append(entry)
        del REQUEST_LOGS[:-80]


def rate_limited_response(client):
    now = time.time()
    window_seconds = 10
    limit = 3
    with LOCK:
        hits = [ts for ts in RATE_HITS.get(client, []) if now - ts <= window_seconds]
        if len(hits) >= limit:
            RATE_HITS[client] = hits
            return 429, {
                "error": "Too Many Requests",
                "limit": limit,
                "windowSeconds": window_seconds,
                "retryAfterSeconds": max(1, int(window_seconds - (now - hits[0]))),
                "teachingPoint": "Rate limiting protects API reliability by rejecting excessive requests.",
            }
        hits.append(now)
        RATE_HITS[client] = hits
        return 200, {
            "message": "Request accepted",
            "remaining": limit - len(hits),
            "limit": limit,
            "windowSeconds": window_seconds,
        }


def load_balanced_response():
    global BACKEND_INDEX
    with LOCK:
        backend = BACKENDS[BACKEND_INDEX % len(BACKENDS)]
        BACKEND_INDEX += 1
    return {
        "backend": backend,
        "latencyMs": 80 + (BACKENDS.index(backend) * 35),
        "teachingPoint": "Repeated requests are distributed across backend nodes.",
    }


class DemoMqttBroker(socketserver.ThreadingTCPServer):
    allow_reuse_address = True
    daemon_threads = True


class DemoMqttHandler(socketserver.BaseRequestHandler):
    def handle(self):
        self.request.settimeout(MQTT_BROKER_IDLE_TIMEOUT_SECONDS)
        client_id = "unknown-mqtt-client"
        while True:
            try:
                packet = mqtt_read_packet(self.request)
                if packet is None:
                    return
                first_byte, body = packet
                packet_type = first_byte >> 4
                flags = first_byte & 0x0F

                if packet_type == 1:
                    _, offset = mqtt_decode_string(body, 0)
                    if offset + 4 <= len(body):
                        offset += 4
                    if offset < len(body):
                        client_id, _ = mqtt_decode_string(body, offset)
                    self.request.sendall(b"\x20\x02\x00\x00")
                    continue

                if packet_type == 3:
                    qos = (flags & 0x06) >> 1
                    retained = bool(flags & 0x01)
                    topic, offset = mqtt_decode_string(body, 0)
                    packet_id = None
                    if qos:
                        packet_id = body[offset:offset + 2]
                        offset += 2
                    payload = mqtt_payload_to_json(body[offset:])
                    store_mqtt_message(client_id, topic, qos, retained, payload, "mqtt-tcp-real")
                    if qos == 1 and packet_id:
                        self.request.sendall(b"\x40\x02" + packet_id)
                    if qos == 2 and packet_id:
                        self.request.sendall(b"\x50\x02" + packet_id)
                    continue

                if packet_type == 6:
                    packet_id = body[:2]
                    self.request.sendall(b"\x70\x02" + packet_id)
                    continue

                if packet_type == 8:
                    packet_id = body[:2]
                    qos_results = []
                    offset = 2
                    while offset < len(body):
                        _, offset = mqtt_decode_string(body, offset)
                        if offset < len(body):
                            qos_results.append(min(body[offset], 2))
                            offset += 1
                    response_body = packet_id + bytes(qos_results or [0])
                    self.request.sendall(b"\x90" + mqtt_encode_remaining_length(len(response_body)) + response_body)
                    continue

                if packet_type == 12:
                    self.request.sendall(b"\xd0\x00")
                    continue

                if packet_type == 14:
                    return
            except (ConnectionError, OSError, ValueError, TimeoutError):
                return


def start_mqtt_broker():
    global MQTT_SERVER_ACTIVE
    try:
        mqtt_server = DemoMqttBroker((HOST, MQTT_PORT), DemoMqttHandler)
    except OSError as exc:
        print(f"Real MQTT broker disabled on {HOST}:{MQTT_PORT}: {exc}")
        return None
    thread = threading.Thread(target=mqtt_server.serve_forever, name="DemoMqttBroker", daemon=True)
    thread.start()
    MQTT_SERVER_ACTIVE = True
    print(f"Real MQTT broker running at {HOST}:{MQTT_PORT}")
    print(f"Wireshark capture: tcp.port == {MQTT_PORT}; display filter: mqtt")
    return mqtt_server


def mqtt_real_status():
    return {
        "enabled": MQTT_SERVER_ACTIVE,
        "broker": f"{HOST}:{MQTT_PORT}",
        "protocol": "MQTT 3.1.1 over TCP",
        "triggerEndpoint": "POST /api/mqtt/real-publish",
        "persistentSession": {
            "startEndpoint": "POST /api/mqtt/session/start",
            "statusEndpoint": "GET /api/mqtt/session/status",
            "stopEndpoint": "POST /api/mqtt/session/stop",
            "idleTimeoutSeconds": MQTT_BROKER_IDLE_TIMEOUT_SECONDS,
            "defaultKeepaliveIntervalSeconds": 15,
        },
        "wireshark": {
            "captureFilter": f"tcp port {MQTT_PORT}",
            "displayFilter": "mqtt",
            "decodeAs": f"TCP port {MQTT_PORT} -> MQTT if Wireshark does not decode automatically",
            "persistentPackets": ["CONNECT", "CONNACK", "SUBSCRIBE", "SUBACK", "PUBLISH", "PINGREQ", "PINGRESP"],
        },
        "note": "HTTP endpoint 8088 hanya trigger. Packet MQTT asli muncul pada TCP port 1883. Gunakan session/start agar koneksi tetap hidup untuk demo lama.",
    }


def mqtt_real_publish(body):
    client_id = body.get("clientId", "student-client-01")
    topic = body.get("topic", "class/commproto/sensor-01/temperature")
    topic_filter = body.get("filter") or body.get("topicFilter") or topic
    requested_qos = int(body.get("qos", 0))
    qos = max(0, min(requested_qos, 2))
    retained = bool(body.get("retained", False))
    payload = body.get("payload", {})
    payload_bytes = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    packet_id = 7
    packets = []

    try:
        with socket.create_connection((HOST, MQTT_PORT), timeout=5) as sock:
            sock.settimeout(5)

            sock.sendall(mqtt_connect_packet(client_id))
            packets.append("CONNECT")
            response = mqtt_read_packet(sock)
            packets.append(mqtt_packet_name(response[0] >> 4) if response else "NO_CONNACK")

            sock.sendall(mqtt_subscribe_packet(topic_filter, packet_id=1, qos=min(qos, 1)))
            packets.append("SUBSCRIBE")
            response = mqtt_read_packet(sock)
            packets.append(mqtt_packet_name(response[0] >> 4) if response else "NO_SUBACK")

            sock.sendall(mqtt_publish_packet(topic, payload_bytes, qos=qos, retained=retained, packet_id=packet_id))
            packets.append("PUBLISH")
            if qos == 1:
                response = mqtt_read_packet(sock)
                packets.append(mqtt_packet_name(response[0] >> 4) if response else "NO_PUBACK")
            elif qos == 2:
                response = mqtt_read_packet(sock)
                packets.append(mqtt_packet_name(response[0] >> 4) if response else "NO_PUBREC")
                sock.sendall(b"\x62\x02" + struct.pack("!H", packet_id))
                packets.append("PUBREL")
                response = mqtt_read_packet(sock)
                packets.append(mqtt_packet_name(response[0] >> 4) if response else "NO_PUBCOMP")

            sock.sendall(b"\xe0\x00")
            packets.append("DISCONNECT")
    except Exception as exc:
        return {
            "ok": False,
            "realMqtt": True,
            "error": type(exc).__name__,
            "details": str(exc),
            "broker": f"{HOST}:{MQTT_PORT}",
        }

    return {
        "ok": True,
        "realMqtt": True,
        "protocol": "MQTT 3.1.1 over TCP",
        "broker": f"{HOST}:{MQTT_PORT}",
        "clientId": client_id,
        "topic": topic,
        "topicFilter": topic_filter,
        "requestedQos": requested_qos,
        "effectiveQos": qos,
        "retained": retained,
        "packets": packets,
        "payload": payload,
        "wireshark": {
            "captureFilter": f"tcp port {MQTT_PORT}",
            "displayFilter": "mqtt",
            "packetTypesToFind": ["CONNECT", "CONNACK", "SUBSCRIBE", "SUBACK", "PUBLISH", "DISCONNECT"],
        },
        "note": "Request ke 8088 hanya trigger. Untuk bukti protocol MQTT, capture packet pada TCP port 1883.",
    }


def mqtt_session_public(session):
    return {
        key: value
        for key, value in session.items()
        if key not in {"thread", "stopEvent", "socket"}
    }


def mqtt_session_status(client_id=None):
    with LOCK:
        if client_id:
            session = MQTT_DEMO_SESSIONS.get(client_id)
            return {
                "ok": True,
                "clientId": client_id,
                "session": mqtt_session_public(session) if session else None,
                "active": bool(session and session.get("active")),
                "wireshark": {
                    "displayFilter": "mqtt",
                    "captureFilter": f"tcp port {MQTT_PORT}",
                    "keepalivePackets": ["PINGREQ", "PINGRESP"],
                },
            }
        sessions = [mqtt_session_public(session) for session in MQTT_DEMO_SESSIONS.values()]
    return {
        "ok": True,
        "activeCount": sum(1 for session in sessions if session.get("active")),
        "sessions": sessions,
        "wireshark": {
            "displayFilter": "mqtt",
            "captureFilter": f"tcp port {MQTT_PORT}",
            "keepalivePackets": ["PINGREQ", "PINGRESP"],
        },
    }


def mqtt_session_worker(session, body):
    client_id = session["clientId"]
    topic = session["topic"]
    topic_filter = session["topicFilter"]
    qos = session["effectiveQos"]
    retained = session["retained"]
    payload_bytes = json.dumps(session["payload"], separators=(",", ":")).encode("utf-8")
    packet_id = 21
    stop_event = session["stopEvent"]
    interval = session["keepaliveIntervalSeconds"]
    duration = session["durationSeconds"]
    started_monotonic = time.monotonic()

    try:
        with socket.create_connection((HOST, MQTT_PORT), timeout=5) as sock:
            sock.settimeout(max(5, interval + 5))
            session["socket"] = sock

            sock.sendall(mqtt_connect_packet(client_id, keep_alive=max(60, interval * 3)))
            session["packets"].append("CONNECT")
            response = mqtt_read_packet(sock)
            session["packets"].append(mqtt_packet_name(response[0] >> 4) if response else "NO_CONNACK")

            sock.sendall(mqtt_subscribe_packet(topic_filter, packet_id=1, qos=min(qos, 1)))
            session["packets"].append("SUBSCRIBE")
            response = mqtt_read_packet(sock)
            session["packets"].append(mqtt_packet_name(response[0] >> 4) if response else "NO_SUBACK")

            sock.sendall(mqtt_publish_packet(topic, payload_bytes, qos=qos, retained=retained, packet_id=packet_id))
            session["packets"].append("PUBLISH")
            if qos == 1:
                response = mqtt_read_packet(sock)
                session["packets"].append(mqtt_packet_name(response[0] >> 4) if response else "NO_PUBACK")
            elif qos == 2:
                response = mqtt_read_packet(sock)
                session["packets"].append(mqtt_packet_name(response[0] >> 4) if response else "NO_PUBREC")
                sock.sendall(b"\x62\x02" + struct.pack("!H", packet_id))
                session["packets"].append("PUBREL")
                response = mqtt_read_packet(sock)
                session["packets"].append(mqtt_packet_name(response[0] >> 4) if response else "NO_PUBCOMP")

            session["active"] = True
            session["status"] = "connected"
            session["connectedAt"] = now_iso()

            while not stop_event.wait(interval):
                if duration and time.monotonic() - started_monotonic >= duration:
                    session["status"] = "completed_duration"
                    break
                sock.sendall(mqtt_pingreq_packet())
                session["packets"].append("PINGREQ")
                session["lastPingAt"] = now_iso()
                response = mqtt_read_packet(sock)
                session["packets"].append(mqtt_packet_name(response[0] >> 4) if response else "NO_PINGRESP")
                session["lastPongAt"] = now_iso()

            try:
                sock.sendall(mqtt_disconnect_packet())
                session["packets"].append("DISCONNECT")
            except OSError:
                pass
    except Exception as exc:
        session["status"] = "error"
        session["error"] = type(exc).__name__
        session["details"] = str(exc)
    finally:
        session["active"] = False
        session["endedAt"] = now_iso()
        session.pop("socket", None)


def mqtt_session_start(body):
    client_id = body.get("clientId", "student-session-01")
    old_session = None
    with LOCK:
        old_session = MQTT_DEMO_SESSIONS.get(client_id)
    if old_session and old_session.get("active"):
        old_session["stopEvent"].set()

    requested_qos = int(body.get("qos", 1))
    keepalive_interval = max(5, min(int(body.get("keepaliveIntervalSeconds", 15)), 120))
    session = {
        "clientId": client_id,
        "topic": body.get("topic", "class/commproto/sensor-01/temperature"),
        "topicFilter": body.get("filter") or body.get("topicFilter") or body.get("topic", "class/commproto/sensor-01/temperature"),
        "requestedQos": requested_qos,
        "effectiveQos": max(0, min(requested_qos, 2)),
        "retained": bool(body.get("retained", False)),
        "payload": body.get("payload", {}),
        "keepaliveIntervalSeconds": keepalive_interval,
        "durationSeconds": max(0, int(body.get("durationSeconds", 0))),
        "startedAt": now_iso(),
        "connectedAt": None,
        "endedAt": None,
        "lastPingAt": None,
        "lastPongAt": None,
        "active": False,
        "status": "starting",
        "packets": [],
        "stopEvent": threading.Event(),
        "wireshark": {
            "captureFilter": f"tcp port {MQTT_PORT}",
            "displayFilter": "mqtt",
            "sessionPackets": ["CONNECT", "CONNACK", "SUBSCRIBE", "SUBACK", "PUBLISH", "PINGREQ", "PINGRESP"],
        },
    }
    thread = threading.Thread(target=mqtt_session_worker, args=(session, body), name=f"MqttSession-{client_id}", daemon=True)
    session["thread"] = thread
    with LOCK:
        MQTT_DEMO_SESSIONS[client_id] = session
    thread.start()
    return {
        "ok": True,
        "message": "Persistent MQTT session starting. It will stay open until stopped or server exits.",
        "session": mqtt_session_public(session),
    }


def mqtt_session_stop(body):
    client_id = body.get("clientId")
    stopped = []
    with LOCK:
        sessions = [MQTT_DEMO_SESSIONS.get(client_id)] if client_id else list(MQTT_DEMO_SESSIONS.values())
    for session in sessions:
        if not session:
            continue
        session["stopEvent"].set()
        session["status"] = "stopping"
        stopped.append(session["clientId"])
    return {
        "ok": True,
        "stopped": stopped,
        "message": "Stop requested. Wireshark should show MQTT DISCONNECT when the session closes.",
    }


def stop_all_mqtt_sessions():
    with LOCK:
        sessions = list(MQTT_DEMO_SESSIONS.values())
    for session in sessions:
        session["stopEvent"].set()


def websocket_masked_frame(message, opcode=0x1):
    payload = message.encode("utf-8") if isinstance(message, str) else message
    mask_key = os.urandom(4)
    header = bytearray([0x80 | opcode])
    length = len(payload)
    if length < 126:
        header.append(0x80 | length)
    elif length < 65536:
        header.append(0x80 | 126)
        header.extend(struct.pack("!H", length))
    else:
        header.append(0x80 | 127)
        header.extend(struct.pack("!Q", length))
    masked = bytearray(payload)
    for index in range(len(masked)):
        masked[index] ^= mask_key[index % 4]
    return bytes(header) + mask_key + bytes(masked)


def websocket_read_frame(sock):
    header = mqtt_read_exact(sock, 2)
    first, second = header
    opcode = first & 0x0F
    length = second & 0x7F
    if length == 126:
        length = struct.unpack("!H", mqtt_read_exact(sock, 2))[0]
    elif length == 127:
        length = struct.unpack("!Q", mqtt_read_exact(sock, 8))[0]
    masked = second & 0x80
    mask = mqtt_read_exact(sock, 4) if masked else b"\x00\x00\x00\x00"
    payload = bytearray(mqtt_read_exact(sock, length))
    if masked:
        for index in range(length):
            payload[index] ^= mask[index % 4]
    return opcode, bytes(payload)


def websocket_real_status():
    return {
        "enabled": True,
        "endpoint": f"ws://{HOST}:{PORT}/ws/echo?channel=dashboard",
        "triggerEndpoint": "POST /api/websocket/real-send",
        "protocol": "WebSocket over HTTP/1.1 Upgrade",
        "sessionRetention": {
            "serverKeepaliveSeconds": WEBSOCKET_KEEPALIVE_SECONDS,
            "disconnectPolicy": "Koneksi tetap terbuka sampai client menutup tab/tombol Close atau server dihentikan.",
            "wiresharkPackets": ["HTTP 101 Switching Protocols", "WebSocket Text", "WebSocket Ping", "WebSocket Pong"],
        },
        "wireshark": {
            "displayFilters": [
                f"tcp.port == {PORT}",
                "http.request.uri contains \"/ws/echo\"",
                "http.header contains \"Upgrade\"",
                "websocket",
            ],
            "decodeAs": f"TCP port {PORT} -> HTTP, then inspect WebSocket frames after 101 Switching Protocols",
        },
    }


def websocket_real_send(body):
    channel = body.get("channel", "dashboard")
    message = body.get("message") or body.get("payload") or {"event": "dashboard_refresh", "value": 1}
    if not isinstance(message, str):
        message = json.dumps(message, separators=(",", ":"))
    path = f"/ws/echo?channel={channel}"
    key = base64.b64encode(os.urandom(16)).decode("ascii")

    try:
        with socket.create_connection((HOST, PORT), timeout=5) as sock:
            sock.settimeout(5)
            request = (
                f"GET {path} HTTP/1.1\r\n"
                f"Host: {HOST}:{PORT}\r\n"
                "Upgrade: websocket\r\n"
                "Connection: Upgrade\r\n"
                f"Sec-WebSocket-Key: {key}\r\n"
                "Sec-WebSocket-Version: 13\r\n"
                "\r\n"
            ).encode("ascii")
            sock.sendall(request)
            response = bytearray()
            while b"\r\n\r\n" not in response:
                response.extend(sock.recv(4096))
            header_text = response.decode("iso-8859-1", errors="replace")
            if "101" not in header_text.split("\r\n", 1)[0]:
                return {"ok": False, "error": "WebSocket handshake failed", "response": header_text}

            sock.sendall(websocket_masked_frame(message))
            opcode, payload = websocket_read_frame(sock)
            sock.sendall(websocket_masked_frame(b"", opcode=0x8))
    except Exception as exc:
        return {
            "ok": False,
            "realWebSocket": True,
            "error": type(exc).__name__,
            "details": str(exc),
        }

    try:
        echo = json.loads(payload.decode("utf-8", errors="replace"))
    except json.JSONDecodeError:
        echo = payload.decode("utf-8", errors="replace")

    return {
        "ok": True,
        "realWebSocket": True,
        "protocol": "WebSocket over HTTP/1.1 Upgrade",
        "endpoint": f"ws://{HOST}:{PORT}{path}",
        "packets": ["HTTP GET Upgrade", "101 Switching Protocols", "WebSocket Text Frame", "WebSocket Close Frame"],
        "sent": message,
        "receivedOpcode": opcode,
        "received": echo,
        "wireshark": websocket_real_status()["wireshark"],
        "note": "Gunakan filter `tcp.port == 8088` untuk handshake, lalu `websocket` setelah Wireshark decode HTTP Upgrade.",
    }


def ensure_tls_files():
    cert_path = DATA / "tls_demo_cert.pem"
    key_path = DATA / "tls_demo_key.pem"
    cert_path.write_text(TLS_CERT_PEM + "\n", encoding="utf-8")
    key_path.write_text(TLS_KEY_PEM + "\n", encoding="utf-8")
    return cert_path, key_path


def start_tls_server():
    global TLS_SERVER_ACTIVE
    cert_path, key_path = ensure_tls_files()
    try:
        tls_httpd = ThreadingHTTPServer((HOST, TLS_PORT), DemoHandler)
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        context.load_cert_chain(certfile=str(cert_path), keyfile=str(key_path))
        tls_httpd.socket = context.wrap_socket(tls_httpd.socket, server_side=True)
    except OSError as exc:
        print(f"TLS demo server disabled on {HOST}:{TLS_PORT}: {exc}")
        return None
    except ssl.SSLError as exc:
        print(f"TLS demo server disabled: {exc}")
        return None
    thread = threading.Thread(target=tls_httpd.serve_forever, name="DemoTlsServer", daemon=True)
    thread.start()
    TLS_SERVER_ACTIVE = True
    print(f"TLS/HTTPS demo server running at https://{HOST}:{TLS_PORT}")
    print(f"Wireshark capture: tcp.port == {TLS_PORT}; display filter: tls")
    return tls_httpd


def tls_status():
    return {
        "enabled": TLS_SERVER_ACTIVE,
        "httpsUrl": f"https://{HOST}:{TLS_PORT}/api/health",
        "triggerEndpoint": "POST /api/tls/self-test",
        "certificate": "self-signed classroom certificate for localhost",
        "wireshark": {
            "captureFilter": f"tcp port {TLS_PORT}",
            "displayFilters": ["tls", "tls.handshake", f"tcp.port == {TLS_PORT}"],
            "note": "Payload HTTPS terenkripsi. Untuk lab cukup inspeksi Client Hello, Server Hello, Certificate, dan Application Data.",
        },
    }


def tls_self_test():
    if not TLS_SERVER_ACTIVE:
        return {"ok": False, "error": "TLS server is not active", **tls_status()}
    context = ssl.create_default_context()
    context.check_hostname = False
    context.verify_mode = ssl.CERT_NONE
    try:
        with socket.create_connection((HOST, TLS_PORT), timeout=5) as raw:
            with context.wrap_socket(raw, server_hostname="localhost") as sock:
                sock.sendall(
                    (
                        "GET /api/health HTTP/1.1\r\n"
                        f"Host: {HOST}:{TLS_PORT}\r\n"
                        "Connection: close\r\n"
                        "\r\n"
                    ).encode("ascii")
                )
                response = sock.recv(4096).decode("utf-8", errors="replace")
    except Exception as exc:
        return {"ok": False, "error": type(exc).__name__, "details": str(exc), **tls_status()}
    return {
        "ok": True,
        "protocol": "HTTPS over TLS",
        "tlsVersion": "negotiated by Python ssl",
        "responsePreview": response.split("\r\n\r\n", 1)[0],
        **tls_status(),
    }


def grpc_runtime_available():
    return grpc is not None and descriptor_pb2 is not None and descriptor_pool is not None and message_factory is not None


def add_proto_field(message, name, number, field_type, label=None, type_name=None):
    field = message.field.add()
    field.name = name
    field.number = number
    field.label = label or descriptor_pb2.FieldDescriptorProto.LABEL_OPTIONAL
    field.type = field_type
    if type_name:
        field.type_name = type_name
    return field


def message_class(pool, full_name):
    descriptor = pool.FindMessageTypeByName(full_name)
    if hasattr(message_factory, "GetMessageClass"):
        return message_factory.GetMessageClass(descriptor)
    factory = message_factory.MessageFactory(pool)
    return factory.GetPrototype(descriptor)


def grpc_message_classes():
    global GRPC_MESSAGE_CLASSES
    if GRPC_MESSAGE_CLASSES is not None:
        return GRPC_MESSAGE_CLASSES
    if not grpc_runtime_available():
        raise RuntimeError("grpcio/protobuf belum terinstall. Jalankan: python -m pip install -r requirements.txt")

    file_proto = descriptor_pb2.FileDescriptorProto()
    file_proto.name = "inference.proto"
    file_proto.package = "demo.inference"
    file_proto.syntax = "proto3"

    feature_vector = file_proto.message_type.add()
    feature_vector.name = "FeatureVector"
    add_proto_field(feature_vector, "avg_order_value", 1, descriptor_pb2.FieldDescriptorProto.TYPE_DOUBLE)
    add_proto_field(feature_vector, "monthly_orders", 2, descriptor_pb2.FieldDescriptorProto.TYPE_INT32)

    prediction_request = file_proto.message_type.add()
    prediction_request.name = "PredictionRequest"
    add_proto_field(prediction_request, "customer_id", 1, descriptor_pb2.FieldDescriptorProto.TYPE_STRING)
    add_proto_field(
        prediction_request,
        "features",
        2,
        descriptor_pb2.FieldDescriptorProto.TYPE_MESSAGE,
        type_name=".demo.inference.FeatureVector",
    )

    prediction_reply = file_proto.message_type.add()
    prediction_reply.name = "PredictionReply"
    add_proto_field(prediction_reply, "customer_id", 1, descriptor_pb2.FieldDescriptorProto.TYPE_STRING)
    add_proto_field(prediction_reply, "score", 2, descriptor_pb2.FieldDescriptorProto.TYPE_DOUBLE)
    add_proto_field(prediction_reply, "label", 3, descriptor_pb2.FieldDescriptorProto.TYPE_STRING)
    add_proto_field(prediction_reply, "model_version", 4, descriptor_pb2.FieldDescriptorProto.TYPE_STRING)

    batch_request = file_proto.message_type.add()
    batch_request.name = "BatchPredictionRequest"
    add_proto_field(
        batch_request,
        "items",
        1,
        descriptor_pb2.FieldDescriptorProto.TYPE_MESSAGE,
        label=descriptor_pb2.FieldDescriptorProto.LABEL_REPEATED,
        type_name=".demo.inference.PredictionRequest",
    )

    batch_reply = file_proto.message_type.add()
    batch_reply.name = "BatchPredictionReply"
    add_proto_field(
        batch_reply,
        "predictions",
        1,
        descriptor_pb2.FieldDescriptorProto.TYPE_MESSAGE,
        label=descriptor_pb2.FieldDescriptorProto.LABEL_REPEATED,
        type_name=".demo.inference.PredictionReply",
    )

    health_request = file_proto.message_type.add()
    health_request.name = "HealthCheckRequest"

    health_reply = file_proto.message_type.add()
    health_reply.name = "HealthCheckReply"
    add_proto_field(health_reply, "status", 1, descriptor_pb2.FieldDescriptorProto.TYPE_STRING)
    add_proto_field(health_reply, "transport", 2, descriptor_pb2.FieldDescriptorProto.TYPE_STRING)

    service = file_proto.service.add()
    service.name = "InferenceService"
    for name, request, response in [
        ("Predict", ".demo.inference.PredictionRequest", ".demo.inference.PredictionReply"),
        ("BatchPredict", ".demo.inference.BatchPredictionRequest", ".demo.inference.BatchPredictionReply"),
        ("HealthCheck", ".demo.inference.HealthCheckRequest", ".demo.inference.HealthCheckReply"),
    ]:
        method = service.method.add()
        method.name = name
        method.input_type = request
        method.output_type = response

    pool = descriptor_pool.DescriptorPool()
    pool.Add(file_proto)
    GRPC_MESSAGE_CLASSES = {
        name: message_class(pool, f"demo.inference.{name}")
        for name in [
            "FeatureVector",
            "PredictionRequest",
            "PredictionReply",
            "BatchPredictionRequest",
            "BatchPredictionReply",
            "HealthCheckRequest",
            "HealthCheckReply",
        ]
    }
    return GRPC_MESSAGE_CLASSES


def grpc_feature_score(features):
    avg_order_component = min(float(features.avg_order_value) / 500000, 1.0) * 0.55
    monthly_order_component = min(float(features.monthly_orders) / 10, 1.0) * 0.45
    return round(avg_order_component + monthly_order_component, 3)


class IntegratedInferenceService:
    def __init__(self, classes):
        self.classes = classes

    def Predict(self, request, context):
        value = grpc_feature_score(request.features)
        return self.classes["PredictionReply"](
            customer_id=request.customer_id,
            score=value,
            label="high_value" if value >= 0.6 else "standard",
            model_version=GRPC_MODEL_VERSION,
        )

    def BatchPredict(self, request, context):
        response = self.classes["BatchPredictionReply"]()
        for item in request.items:
            value = grpc_feature_score(item.features)
            response.predictions.append(
                self.classes["PredictionReply"](
                    customer_id=item.customer_id,
                    score=value,
                    label="high_value" if value >= 0.6 else "standard",
                    model_version=GRPC_MODEL_VERSION,
                )
            )
        return response

    def HealthCheck(self, request, context):
        return self.classes["HealthCheckReply"](status="SERVING", transport="gRPC over HTTP/2")


def start_grpc_http2_server():
    global GRPC_SERVER_ACTIVE
    if not grpc_runtime_available():
        print("gRPC HTTP/2 server disabled: install dependency with `python -m pip install -r requirements.txt`.")
        return None

    classes = grpc_message_classes()
    service = IntegratedInferenceService(classes)
    grpc_server = grpc.server(futures.ThreadPoolExecutor(max_workers=4))
    grpc_server.add_generic_rpc_handlers((
        grpc.method_handlers_generic_handler(
            GRPC_SERVICE,
            {
                "Predict": grpc.unary_unary_rpc_method_handler(
                    service.Predict,
                    request_deserializer=classes["PredictionRequest"].FromString,
                    response_serializer=classes["PredictionReply"].SerializeToString,
                ),
                "BatchPredict": grpc.unary_unary_rpc_method_handler(
                    service.BatchPredict,
                    request_deserializer=classes["BatchPredictionRequest"].FromString,
                    response_serializer=classes["BatchPredictionReply"].SerializeToString,
                ),
                "HealthCheck": grpc.unary_unary_rpc_method_handler(
                    service.HealthCheck,
                    request_deserializer=classes["HealthCheckRequest"].FromString,
                    response_serializer=classes["HealthCheckReply"].SerializeToString,
                ),
            },
        ),
    ))
    try:
        bound_port = grpc_server.add_insecure_port(f"{HOST}:{GRPC_PORT}")
    except RuntimeError as exc:
        print(f"gRPC HTTP/2 server disabled on {HOST}:{GRPC_PORT}: {exc}")
        return None
    if bound_port == 0:
        print(f"gRPC HTTP/2 server disabled: port {GRPC_PORT} is unavailable.")
        return None
    grpc_server.start()
    GRPC_SERVER_ACTIVE = True
    print(f"Real gRPC HTTP/2 server running at {HOST}:{GRPC_PORT}")
    print(f"Wireshark capture: tcp.port == {GRPC_PORT}; Decode As HTTP2 if needed.")
    return grpc_server


def payload_value(payload, camel_name, snake_name, default=None):
    if camel_name in payload:
        return payload.get(camel_name)
    return payload.get(snake_name, default)


def build_prediction_request(classes, payload):
    features = payload.get("features", payload)
    return classes["PredictionRequest"](
        customer_id=str(payload_value(payload, "customerId", "customer_id", "C-DEMO")),
        features=classes["FeatureVector"](
            avg_order_value=float(payload_value(features, "avgOrderValue", "avg_order_value", 0)),
            monthly_orders=int(payload_value(features, "monthlyOrders", "monthly_orders", 0)),
        ),
    )


def default_batch_prediction_items():
    return [
        {
            "customerId": "C-1001",
            "features": {"avgOrderValue": 150000, "monthlyOrders": 3},
        },
        {
            "customerId": "C-1002",
            "features": {"avgOrderValue": 420000, "monthlyOrders": 9},
        },
    ]


def batch_prediction_items(payload):
    if isinstance(payload, dict):
        items = payload.get("items")
        if items:
            return items
        has_single_prediction_shape = any(
            key in payload
            for key in (
                "customerId",
                "customer_id",
                "features",
                "avgOrderValue",
                "avg_order_value",
                "monthlyOrders",
                "monthly_orders",
            )
        )
        if has_single_prediction_shape:
            return [payload]
    return default_batch_prediction_items()


def score_prediction_payload(item):
    features = item.get("features", item)
    score = 0.0
    score += min(float(features.get("avgOrderValue", features.get("avg_order_value", 0))) / 500000, 1.0) * 0.55
    score += min(float(features.get("monthlyOrders", features.get("monthly_orders", 0))) / 10, 1.0) * 0.45
    return round(score, 3)


def protobuf_to_dict(message):
    if json_format is None:
        return {"text": str(message)}
    return json_format.MessageToDict(message, preserving_proto_field_name=True)


def grpc_http2_status():
    return {
        "enabled": grpc_runtime_available() and GRPC_SERVER_ACTIVE,
        "runtimeAvailable": grpc_runtime_available(),
        "serverActive": GRPC_SERVER_ACTIVE,
        "httpUi": f"http://{HOST}:{PORT}",
        "grpcTarget": f"{HOST}:{GRPC_PORT}",
        "service": GRPC_SERVICE,
        "transport": "gRPC over HTTP/2" if GRPC_SERVER_ACTIVE else "disabled",
        "install": "python -m pip install -r requirements.txt",
        "wireshark": {
            "captureFilter": f"tcp port {GRPC_PORT}",
            "displayFilter": "http2",
            "decodeAs": f"TCP port {GRPC_PORT} -> HTTP2",
        },
    }


def grpc_http2_call(body):
    if not grpc_runtime_available():
        concept = _grpc_call(body)
        return {
            "ok": False,
            "fallbackConceptResponse": concept,
            "error": "grpcio/protobuf belum terinstall",
            "install": "python -m pip install -r requirements.txt",
        }
    if not GRPC_SERVER_ACTIVE:
        concept = _grpc_call(body)
        return {
            "ok": False,
            "realGrpc": True,
            "fallbackConceptResponse": concept,
            "error": "Real gRPC HTTP/2 server is not active",
            "details": f"Port {GRPC_PORT} may be in use or server startup failed. Use POST Dynamic RPC Call as fallback.",
            **grpc_http2_status(),
        }

    classes = grpc_message_classes()
    method = body.get("method", "Predict")
    payload = body.get("payload", body)
    target = body.get("target", f"{HOST}:{GRPC_PORT}")
    timeout = min(float(body.get("timeoutSeconds", 3)), 10)

    try:
        with grpc.insecure_channel(target) as channel:
            if method == "HealthCheck":
                request = classes["HealthCheckRequest"]()
                response_type = classes["HealthCheckReply"]
            elif method == "BatchPredict":
                request = classes["BatchPredictionRequest"]()
                for item in batch_prediction_items(payload):
                    request.items.append(build_prediction_request(classes, item))
                response_type = classes["BatchPredictionReply"]
            elif method == "Predict":
                request = build_prediction_request(classes, payload)
                response_type = classes["PredictionReply"]
            else:
                return {
                    "ok": False,
                    "error": "Unsupported gRPC method",
                    "supportedMethods": ["Predict", "BatchPredict", "HealthCheck"],
                }

            rpc = channel.unary_unary(
                f"/{GRPC_SERVICE}/{method}",
                request_serializer=type(request).SerializeToString,
                response_deserializer=response_type.FromString,
            )
            response = rpc(request, timeout=timeout)
    except grpc.RpcError as exc:
        concept = _grpc_call(body)
        return {
            "ok": False,
            "realGrpc": True,
            "method": method,
            "target": target,
            "fallbackConceptResponse": concept,
            "grpcCode": str(exc.code()),
            "details": exc.details(),
        }
    except Exception as exc:
        concept = _grpc_call(body)
        return {
            "ok": False,
            "realGrpc": True,
            "method": method,
            "target": target,
            "fallbackConceptResponse": concept,
            "error": type(exc).__name__,
            "details": str(exc),
        }

    return {
        "ok": True,
        "realGrpc": True,
        "triggerEndpoint": "POST /api/grpc/http2-call",
        "method": method,
        "target": target,
        "transport": "gRPC over HTTP/2",
        "request": protobuf_to_dict(request),
        "response": protobuf_to_dict(response),
        "wireshark": {
            "captureFilter": f"tcp port {GRPC_PORT}",
            "displayFilter": "http2",
            "decodeAs": f"TCP port {GRPC_PORT} -> HTTP2",
        },
        "note": f"HTTP endpoint ini hanya trigger. Traffic yang perlu di-capture adalah gRPC HTTP/2 pada port {GRPC_PORT}.",
    }


def capture_matrix():
    return {
        "serverPorts": {
            "HTTP_UI_API": PORT,
            "MQTT_TCP": MQTT_PORT,
            "gRPC_HTTP2": GRPC_PORT,
            "HTTPS_TLS": TLS_PORT,
        },
        "meetings": [
            {"meeting": "P3", "topic": "WebSocket", "trigger": "Browser Connect or POST /api/websocket/real-send", "wireshark": ["tcp.port == 8088", "http.request.uri contains \"/ws/echo\"", "websocket"], "expected": "HTTP 101 Switching Protocols, WebSocket text frame, and keepalive Ping/Pong"},
            {"meeting": "P4", "topic": "MQTT", "trigger": "POST /api/mqtt/session/start or /api/mqtt/real-publish", "wireshark": ["tcp.port == 1883", "mqtt"], "expected": "CONNECT, CONNACK, SUBSCRIBE, SUBACK, PUBLISH, and persistent PINGREQ/PINGRESP"},
            {"meeting": "P5", "topic": "gRPC over HTTP/2", "trigger": "POST /api/grpc/http2-call", "wireshark": ["tcp.port == 50051", "http2"], "expected": "HTTP/2 HEADERS and DATA frames"},
            {"meeting": "P6", "topic": "JSON/XML/CSV/Protobuf over HTTP", "trigger": "GET /api/exchange/json, /xml, /csv, /protobuf-schema", "wireshark": ["tcp.port == 8088", "http"], "expected": "HTTP response with Content-Type application/json, application/xml, text/csv, or text/plain"},
            {"meeting": "P7", "topic": "TLS/HTTP troubleshooting", "trigger": "POST /api/tls/self-test and /api/troubleshooting/test", "wireshark": ["tcp.port == 8443", "tls", "tls.handshake", "tcp.port == 8088", "http"], "expected": "TLS handshake on 8443 and HTTP status/error evidence on 8088"},
            {"meeting": "P8", "topic": "UTS evidence", "trigger": "GET /api/uts/orders, POST /api/uts/evidence", "wireshark": ["tcp.port == 8088", "http"], "expected": "HTTP GET/POST with JSON evidence payload"},
            {"meeting": "P9", "topic": "API documentation / Postman runner", "trigger": "GET /api/openapi, POST /api/postman/run", "wireshark": ["tcp.port == 8088", "http"], "expected": "OpenAPI JSON and runner simulation response"},
            {"meeting": "P10", "topic": "Rate limiting / load balancing", "trigger": "GET /api/reliability/rate-limited, POST /api/reliability/simulate-load", "wireshark": ["tcp.port == 8088", "http.response.code == 429", "http"], "expected": "HTTP 200 and 429 responses plus backend distribution"},
            {"meeting": "P11", "topic": "Microservices communication", "trigger": "POST /api/microservices/orders with wireCapture true", "wireshark": ["tcp.port == 8088", "tcp.port == 50051", "http2", "tcp.port == 1883", "mqtt"], "expected": "HTTP order flow plus optional gRPC and MQTT internal evidence"},
            {"meeting": "P12", "topic": "Observability", "trigger": "POST /api/observability/capture-scenario", "wireshark": ["tcp.port == 8088", "http", "tcp.port == 1883", "mqtt"], "expected": "HTTP log/metric/trace calls plus MQTT telemetry evidence"},
            {"meeting": "P13-15", "topic": "n8n automation / project phase", "trigger": "POST /api/automation/workflow-run with wireCapture true", "wireshark": ["tcp.port == 8088", "http", "tcp.port == 1883", "mqtt"], "expected": "Webhook-style HTTP workflow response and MQTT telemetry side effect"},
            {"meeting": "P16", "topic": "UAS final project", "trigger": "POST /api/project/capture-demo", "wireshark": ["tcp.port == 8088", "http", "tcp.port == 1883", "mqtt", "tcp.port == 50051", "http2", "websocket"], "expected": "Integrated multi-protocol evidence"},
        ],
        "loopbackNote": "Di Windows, gunakan Npcap Loopback Adapter/Adapter for loopback traffic capture. Jika protocol tidak otomatis muncul, gunakan Decode As pada port terkait.",
    }


def observability_capture_scenario():
    log_event = {
        "id": int(time.time() * 1000),
        "receivedAt": now_iso(),
        "event": "observability.capture.scenario",
        "severity": "info",
        "service": "demo-observability",
        "message": "Scenario triggers HTTP observability and MQTT telemetry for Wireshark evidence",
        "traceId": "demo-trace-001",
    }
    mqtt_result = mqtt_real_publish({
        "clientId": "observability-agent",
        "topic": "class/commproto/observability/metrics",
        "filter": "class/commproto/+/metrics",
        "qos": 1,
        "payload": {"requestCount": len(REQUEST_LOGS), "timestamp": now_iso()},
    })
    return {
        "ok": True,
        "log": log_event,
        "metrics": _metrics(),
        "trace": _trace("demo-trace-001"),
        "mqttEvidence": mqtt_result,
        "wireshark": {
            "http": f"tcp.port == {PORT}",
            "mqtt": f"tcp.port == {MQTT_PORT} or mqtt",
        },
    }


def project_capture_demo(body=None):
    body = body or {}
    mqtt_result = mqtt_real_publish({
        "clientId": "uas-project-device",
        "topic": "class/commproto/uas/project",
        "filter": "class/commproto/+/project",
        "qos": 1,
        "payload": {"event": body.get("event", "uas.demo.executed"), "source": "project-capture-demo"},
    })
    websocket_result = websocket_real_send({
        "channel": "dashboard",
        "payload": {"event": "uas.dashboard.update", "project": "multi-protocol-pipeline"},
    })
    grpc_result = grpc_http2_call({
        "method": "Predict",
        "payload": {
            "customerId": "UAS-001",
            "features": {"avgOrderValue": 450000, "monthlyOrders": 9},
        },
    })
    return {
        "ok": True,
        "scenario": "UAS integrated multi-protocol capture demo",
        "httpEvidence": {"endpoint": "POST /api/project/capture-demo", "port": PORT},
        "mqttEvidence": mqtt_result,
        "webSocketEvidence": websocket_result,
        "grpcEvidence": grpc_result,
        "wireshark": {
            "http": f"tcp.port == {PORT}",
            "mqtt": f"tcp.port == {MQTT_PORT} or mqtt",
            "websocket": "websocket or http.request.uri contains \"/ws/echo\"",
            "grpc": f"tcp.port == {GRPC_PORT} or http2",
        },
    }


def capture_run(body):
    meeting = str(body.get("meeting", "")).upper()
    if meeting == "P3":
        return websocket_real_send(body)
    if meeting == "P4":
        if body.get("persistentSession"):
            return mqtt_session_start(body)
        return mqtt_real_publish(body)
    if meeting == "P5":
        return grpc_http2_call(body)
    if meeting == "P7":
        return tls_self_test()
    if meeting == "P11":
        payload = {"orderId": "ORD-CAPTURE-001", "amount": 450000, "wireCapture": True}
        payload.update(body)
        return _microservice_order_flow(payload)
    if meeting == "P12":
        return observability_capture_scenario()
    if meeting in {"P13", "P14", "P15", "P13-15"}:
        payload = {"workflow": "telemetry-to-inbox", "event": "telemetry.workflow.completed", "wireCapture": True}
        payload.update(body)
        return _automation_run(payload)
    if meeting == "P16":
        return project_capture_demo(body)
    return {"ok": False, "error": "Unsupported meeting for active capture runner", "supported": ["P3", "P4", "P5", "P7", "P11", "P12", "P13-15", "P16"], "matrix": capture_matrix()}


class DemoHandler(BaseHTTPRequestHandler):
    server_version = "CommProtocolsDemo/1.0"

    def log_message(self, fmt, *args):
        print("%s - %s" % (self.address_string(), fmt % args))

    def _cors(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, PUT, PATCH, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def _json(self, status, payload, headers=None):
        body = json.dumps(payload, indent=2).encode("utf-8")
        record_request(self.command, self.path, status, "json")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self._cors()
        if headers:
            for key, value in headers.items():
                self.send_header(key, value)
        self.end_headers()
        self.wfile.write(body)

    def _text(self, status, payload, mime="text/plain; charset=utf-8"):
        body = payload.encode("utf-8")
        record_request(self.command, self.path, status, mime)
        self.send_response(status)
        self.send_header("Content-Type", mime)
        self.send_header("Content-Length", str(len(body)))
        self._cors()
        self.end_headers()
        self.wfile.write(body)

    def _no_content(self):
        record_request(self.command, self.path, 204, "no-content")
        self.send_response(204)
        self._cors()
        self.end_headers()

    def _body_json(self):
        length = int(self.headers.get("Content-Length", "0"))
        if length == 0:
            return {}
        raw = self.rfile.read(length).decode("utf-8")
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            self._json(400, {"error": "Invalid JSON body", "raw": raw})
            return None

    def _serve_file(self, file_path):
        if not file_path.exists() or not file_path.is_file():
            self._json(404, {"error": "File not found"})
            return
        body = file_path.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", content_type(file_path))
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self.send_response(204)
        self._cors()
        self.end_headers()

    def do_HEAD(self):
        self.send_response(200)
        self._cors()
        self.end_headers()

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path
        query = parse_qs(parsed.query)

        if self.headers.get("Upgrade", "").lower() == "websocket" and path == "/ws/echo":
            self._websocket_echo()
            return

        if path == "/":
            index = ROOT / "index.html"
            if index.exists():
                self._serve_file(index)
            else:
                self._text(200, """<!doctype html><html><head><meta charset='utf-8'><title>Communication Protocols Demo App</title></head><body><h1>Communication Protocols Demo App</h1><p>Server is running. Start with <code>/api/health</code>, <code>/api/openapi</code>, <code>/api/reliability/rate-limited</code>, and <code>/api/project/capture-demo</code>.</p></body></html>""", "text/html; charset=utf-8")
            return

        if path.startswith("/static/"):
            safe = path.replace("/static/", "", 1).replace("\\", "/")
            if ".." in safe:
                self._json(400, {"error": "Invalid static path"})
                return
            self._serve_file(STATIC / safe)
            return

        if path == "/api/health":
            self._json(200, {"status": "ok", "service": "Communication Protocols Demo App", "time": now_iso()})
            return

        if path == "/api/capture/matrix":
            self._json(200, capture_matrix())
            return

        if path == "/api/websocket/real-status":
            self._json(200, websocket_real_status())
            return

        if path == "/api/tls/status":
            self._json(200, tls_status())
            return

        if path == "/api/realtime/events":
            channel = query.get("channel", [None])[0]
            events = read_json(REALTIME_EVENTS)
            if channel:
                events = [event for event in events if event.get("channel") == channel]
            self._json(200, {"count": len(events), "channel": channel, "events": events[-30:]})
            return

        if path == "/api/openapi":
            self._json(200, _openapi_spec())
            return

        if path == "/api/postman-run-summary":
            self._json(200, _postman_run_summary())
            return

        if path == "/api/uts/cases":
            self._json(200, resource_cases_payload())
            return

        resource, item_id, route_error = parse_api_resource_path(path)
        if route_error:
            self._json(400, {"error": route_error, "path": path})
            return
        if resource:
            if item_id is None:
                self._json(200, resource_collection_payload(resource))
                return
            item = resource_item(resource, item_id)
            if not item:
                self._json(404, {"error": f"{API_RESOURCES[resource]['label']} not found", "resource": resource, "id": item_id})
                return
            self._json(200, item)
            return

        if path == "/api/exchange/json":
            self._json(200, {"format": "json", "records": _sample_records()})
            return

        if path == "/api/exchange/xml":
            records = "".join(
                f"<record><id>{r['id']}</id><sensor>{r['sensor']}</sensor><value>{r['value']}</value><unit>{r['unit']}</unit></record>"
                for r in _sample_records()
            )
            self._text(200, f'<?xml version="1.0" encoding="UTF-8"?><telemetry>{records}</telemetry>', "application/xml; charset=utf-8")
            return

        if path == "/api/exchange/csv":
            lines = ["id,sensor,value,unit"]
            lines.extend([f"{r['id']},{r['sensor']},{r['value']},{r['unit']}" for r in _sample_records()])
            self._text(200, "\n".join(lines) + "\n", "text/csv; charset=utf-8")
            return

        if path == "/api/exchange/protobuf-schema":
            self._text(200, _telemetry_proto_schema(), "text/plain; charset=utf-8")
            return

        if path.startswith("/api/troubleshooting/status/"):
            try:
                status = int(path.rsplit("/", 1)[-1])
            except ValueError:
                status = 400
            self._json(status, {"requestedStatus": status, "message": "Intentional troubleshooting response"})
            return

        if path == "/api/troubleshooting/slow":
            ms = min(int(query.get("ms", ["1000"])[0]), 5000)
            time.sleep(ms / 1000)
            self._json(200, {"message": "Slow response completed", "delayMs": ms})
            return

        if path == "/api/uts/orders":
            self._json(200, {"case": "UTS API evidence", "orders": _orders()})
            return

        if path == "/api/webhook/inbox":
            self._json(200, {"count": len(read_json(WEBHOOK_INBOX)), "data": read_json(WEBHOOK_INBOX)})
            return

        if path == "/api/mqtt/messages":
            topic = query.get("topic", [None])[0]
            topic_filter = query.get("filter", [None])[0]
            if topic_filter:
                topic_filter = topic_filter.replace(" ", "+")
            messages = read_json(MESSAGES)
            if topic:
                messages = [msg for msg in messages if msg["topic"] == topic]
            if topic_filter:
                messages = [msg for msg in messages if mqtt_topic_match(topic_filter, msg["topic"])]
            self._json(200, {"count": len(messages), "topic": topic, "filter": topic_filter, "messages": messages[-50:]})
            return

        if path == "/api/mqtt/topics":
            messages = read_json(MESSAGES)
            topics = sorted(set(msg["topic"] for msg in messages))
            retained = [msg for msg in messages if msg.get("retained")]
            self._json(200, {"topics": topics, "retainedMessages": retained[-20:]})
            return

        if path == "/api/mqtt/real-status":
            self._json(200, mqtt_real_status())
            return

        if path == "/api/mqtt/session/status":
            client_id = query.get("clientId", [None])[0]
            self._json(200, mqtt_session_status(client_id))
            return

        if path == "/api/reliability/rate-limited":
            status, payload = rate_limited_response(self.client_address[0])
            self._json(status, payload)
            return

        if path == "/api/reliability/load-balanced":
            self._json(200, load_balanced_response())
            return

        if path == "/api/microservices/order-flow":
            self._json(200, _microservice_order_flow())
            return

        if path == "/api/observability/metrics":
            self._json(200, _metrics())
            return

        if path == "/api/observability/logs":
            self._json(200, {"count": len(REQUEST_LOGS), "logs": REQUEST_LOGS[-30:]})
            return

        if path.startswith("/api/observability/trace/"):
            trace_id = path.rsplit("/", 1)[-1]
            self._json(200, _trace(trace_id))
            return

        if path == "/api/automation/n8n-workflow-spec":
            self._json(200, _n8n_workflow_spec())
            return

        if path == "/api/automation/inbox":
            self._json(200, {"count": len(read_json(AUTOMATION_INBOX)), "data": read_json(AUTOMATION_INBOX)})
            return

        if path == "/api/cases/protocol-decision":
            self._json(200, _protocol_case())
            return

        if path == "/api/grpc/proto":
            self._text(200, _proto_contract(), "text/plain; charset=utf-8")
            return

        if path == "/api/grpc/services":
            self._json(200, _grpc_services())
            return

        if path == "/api/grpc/http2-status":
            self._json(200, grpc_http2_status())
            return

        if path == "/api/project/events":
            self._json(200, {"events": read_json(MESSAGES)[-10:]})
            return

        if path == "/api/project/summary":
            self._json(200, _project_summary())
            return

        self._json(404, {"error": "Route not found", "path": path})

    def do_POST(self):
        path = urlparse(self.path).path

        if path == "/api/reset":
            with LOCK:
                for config in API_RESOURCES.values():
                    shutil.copyfile(config["seed"], config["file"])
                write_json(MESSAGES, [])
                write_json(WEBHOOK_INBOX, [])
                write_json(AUTOMATION_INBOX, [])
                write_json(REALTIME_EVENTS, [])
                REQUEST_LOGS.clear()
                RATE_HITS.clear()
            self._json(200, {"message": "All demo data reset"})
            return

        if path == "/api/capture/run":
            body = self._body_json()
            if body is None:
                return
            result = capture_run(body)
            self._json(200 if result.get("ok") else 400, result)
            return

        if path == "/api/websocket/real-send":
            body = self._body_json()
            if body is None:
                return
            result = websocket_real_send(body)
            self._json(200 if result.get("ok") else 503, result)
            return

        if path == "/api/tls/self-test":
            result = tls_self_test()
            self._json(200 if result.get("ok") else 503, result)
            return

        resource, item_id, route_error = parse_api_resource_path(path)
        if route_error:
            self._json(400, {"error": route_error, "path": path})
            return
        if resource:
            if item_id is not None:
                self._json(400, {"error": f"Use POST /api/{resource} to create a new resource", "resource": resource})
                return
            body = self._body_json()
            if body is None:
                return
            status, payload, headers = create_resource(resource, body)
            self._json(status, payload, headers=headers)
            return

        if path == "/api/realtime/events":
            body = self._body_json()
            if body is None:
                return
            event = {
                "id": int(time.time() * 1000),
                "channel": body.get("channel", "dashboard"),
                "event": body.get("event", "message.created"),
                "payload": body.get("payload", {}),
                "publishedAt": now_iso(),
                "transport": body.get("transport", "websocket-concept"),
            }
            with LOCK:
                events = read_json(REALTIME_EVENTS)
                events.append(event)
                write_json(REALTIME_EVENTS, events)
            self._json(201, event)
            return

        if path == "/api/webhook/inbox":
            body = self._body_json()
            if body is None:
                return
            event = {"id": int(time.time() * 1000), "receivedAt": now_iso(), "payload": body}
            with LOCK:
                inbox = read_json(WEBHOOK_INBOX)
                inbox.append(event)
                write_json(WEBHOOK_INBOX, inbox)
            self._json(201, event)
            return

        if path == "/api/mqtt/publish":
            body = self._body_json()
            if body is None:
                return
            if "topic" not in body or "payload" not in body:
                self._json(400, {"error": "topic and payload are required"})
                return
            message = store_mqtt_message(
                body.get("clientId", "student-client"),
                body["topic"],
                body.get("qos", 0),
                body.get("retained", False),
                body["payload"],
                "http-simulator",
            )
            self._json(201, message)
            return

        if path == "/api/mqtt/real-publish":
            body = self._body_json()
            if body is None:
                return
            result = mqtt_real_publish(body)
            self._json(200 if result.get("ok") else 503, result)
            return

        if path == "/api/mqtt/session/start":
            body = self._body_json()
            if body is None:
                return
            result = mqtt_session_start(body)
            self._json(200 if result.get("ok") else 503, result)
            return

        if path == "/api/mqtt/session/stop":
            body = self._body_json()
            if body is None:
                return
            self._json(200, mqtt_session_stop(body))
            return

        if path == "/api/mqtt/clear":
            with LOCK:
                write_json(MESSAGES, [])
            self._json(200, {"message": "MQTT simulator messages cleared"})
            return

        if path == "/api/reliability/reset":
            with LOCK:
                RATE_HITS.clear()
            self._json(200, {"message": "Reliability demo state reset"})
            return

        if path == "/api/microservices/orders":
            body = self._body_json()
            if body is None:
                return
            flow = _microservice_order_flow(body)
            self._json(201, flow)
            return

        if path == "/api/grpc/infer":
            body = self._body_json()
            if body is None:
                return
            features = body.get("features", {})
            score = 0.0
            score += min(float(features.get("avgOrderValue", 0)) / 500000, 1.0) * 0.55
            score += min(float(features.get("monthlyOrders", 0)) / 10, 1.0) * 0.45
            self._json(200, {
                "mock": True,
                "note": "This is a REST mock of a gRPC/Protobuf concept, not a real HTTP/2 gRPC server.",
                "requestMessage": "PredictionRequest",
                "responseMessage": "PredictionReply",
                "customerId": body.get("customerId"),
                "score": round(score, 3),
                "label": "high_value" if score >= 0.6 else "standard",
            })
            return

        if path == "/api/grpc/call":
            body = self._body_json()
            if body is None:
                return
            self._json(200, _grpc_call(body))
            return

        if path == "/api/grpc/http2-call":
            body = self._body_json()
            if body is None:
                return
            result = grpc_http2_call(body)
            self._json(200 if result.get("ok") else 503, result)
            return

        if path == "/api/encoding/convert":
            body = self._body_json()
            if body is None:
                return
            self._json(200, _encoding_convert(body))
            return

        if path == "/api/troubleshooting/test":
            body = self._body_json()
            if body is None:
                return
            status = int(body.get("status", 200))
            delay_ms = min(int(body.get("delayMs", 0)), 5000)
            if delay_ms:
                time.sleep(delay_ms / 1000)
            self._json(status, {
                "requestedStatus": status,
                "delayMs": delay_ms,
                "scenario": body.get("scenario", "custom troubleshooting test"),
                "headersToInspect": ["Content-Type", "Content-Length", "Status Code"],
                "teachingPoint": "Students should connect symptom, status code, delay, and probable cause.",
            })
            return

        if path == "/api/observability/custom-log":
            body = self._body_json()
            if body is None:
                return
            event = {
                "id": int(time.time() * 1000),
                "receivedAt": now_iso(),
                "event": body.get("event", "custom.observability.event"),
                "severity": body.get("severity", "info"),
                "service": body.get("service", "demo-service"),
                "message": body.get("message", "Custom log event from lab UI"),
                "traceId": body.get("traceId", "demo-trace-001"),
                "teachingPoint": "A log captures one event; compare it with metrics and traces for the same scenario.",
            }
            self._json(201, event)
            return

        if path == "/api/observability/capture-scenario":
            self._json(200, observability_capture_scenario())
            return

        if path == "/api/uts/evidence":
            body = self._body_json()
            if body is None:
                return
            evidence = {"id": int(time.time() * 1000), "submittedAt": now_iso(), "payload": body}
            with LOCK:
                inbox = read_json(WEBHOOK_INBOX)
                inbox.append(evidence)
                write_json(WEBHOOK_INBOX, inbox)
            self._json(201, evidence)
            return

        if path == "/api/postman/run":
            body = self._body_json()
            if body is None:
                return
            self._json(200, _postman_run(body))
            return

        if path == "/api/reliability/simulate-load":
            body = self._body_json()
            if body is None:
                return
            count = min(int(body.get("requests", 6)), 20)
            results = []
            for _ in range(count):
                results.append(load_balanced_response())
            self._json(200, {"requests": count, "results": results, "teachingPoint": "Use repeated calls to observe distribution and latency differences."})
            return

        if path == "/api/project/events":
            body = self._body_json()
            if body is None:
                return
            event = {"id": int(time.time() * 1000), "publishedAt": now_iso(), **body}
            protocol_evidence = None
            if body.get("wireCapture"):
                protocol_evidence = project_capture_demo(body)
                event["protocolEvidence"] = protocol_evidence
            with LOCK:
                messages = read_json(MESSAGES)
                messages.append({"topic": "project/events", "payload": event, "publishedAt": now_iso()})
                write_json(MESSAGES, messages)
            self._json(201, event)
            return

        if path == "/api/project/capture-demo":
            body = self._body_json()
            if body is None:
                return
            self._json(200, project_capture_demo(body))
            return

        if path == "/api/automation/inbox":
            body = self._body_json()
            if body is None:
                return
            event = {"id": int(time.time() * 1000), "receivedAt": now_iso(), "source": "n8n-or-postman", "payload": body}
            with LOCK:
                inbox = read_json(AUTOMATION_INBOX)
                inbox.append(event)
                write_json(AUTOMATION_INBOX, inbox)
            self._json(201, event)
            return

        if path == "/api/automation/workflow-run":
            body = self._body_json()
            if body is None:
                return
            result = _automation_run(body)
            with LOCK:
                inbox = read_json(AUTOMATION_INBOX)
                inbox.append({"id": int(time.time() * 1000), "receivedAt": now_iso(), "source": "workflow-run-simulator", "payload": result})
                write_json(AUTOMATION_INBOX, inbox)
            self._json(201, result)
            return

        self._json(404, {"error": "Route not found", "path": path})

    def do_PUT(self):
        path = urlparse(self.path).path
        resource, item_id, route_error = parse_api_resource_path(path)
        if route_error:
            self._json(400, {"error": route_error, "path": path})
            return
        if not resource or item_id is None:
            self._json(404, {"error": "Use PUT /api/{resource}/{id}", "resources": sorted(API_RESOURCES)})
            return
        body = self._body_json()
        if body is None:
            return
        status, payload = replace_resource(resource, item_id, body)
        self._json(status, payload)

    def do_PATCH(self):
        path = urlparse(self.path).path
        resource, item_id, route_error = parse_api_resource_path(path)
        if route_error:
            self._json(400, {"error": route_error, "path": path})
            return
        if not resource or item_id is None:
            self._json(404, {"error": "Use PATCH /api/{resource}/{id}", "resources": sorted(API_RESOURCES)})
            return
        body = self._body_json()
        if body is None:
            return
        status, payload = patch_resource(resource, item_id, body)
        self._json(status, payload)

    def do_DELETE(self):
        path = urlparse(self.path).path
        resource, item_id, route_error = parse_api_resource_path(path)
        if route_error:
            self._json(400, {"error": route_error, "path": path})
            return
        if not resource or item_id is None:
            self._json(404, {"error": "Use DELETE /api/{resource}/{id}", "resources": sorted(API_RESOURCES)})
            return
        status, payload = delete_resource(resource, item_id)
        if status != 204:
            self._json(status, payload)
            return
        self._no_content()

    def _websocket_echo(self):
        key = self.headers.get("Sec-WebSocket-Key")
        if not key:
            self._json(400, {"error": "Missing Sec-WebSocket-Key"})
            return
        accept = base64.b64encode(hashlib.sha1((key + WS_GUID).encode("ascii")).digest()).decode("ascii")
        self.send_response(101, "Switching Protocols")
        self.send_header("Upgrade", "websocket")
        self.send_header("Connection", "Upgrade")
        self.send_header("Sec-WebSocket-Accept", accept)
        self.end_headers()

        self.connection.settimeout(None)
        keepalive_stop = threading.Event()
        write_lock = threading.Lock()

        def send_ws_frame(message, opcode=0x1):
            with write_lock:
                self._write_ws_frame(message, opcode=opcode)

        def websocket_keepalive():
            while not keepalive_stop.wait(WEBSOCKET_KEEPALIVE_SECONDS):
                try:
                    send_ws_frame("server-keepalive", opcode=0x9)
                except OSError:
                    keepalive_stop.set()
                    break

        threading.Thread(target=websocket_keepalive, name="WebSocketKeepalive", daemon=True).start()
        try:
            while True:
                try:
                    frame = self._read_ws_frame()
                except (ConnectionError, OSError):
                    break
                if frame is None:
                    break
                opcode, payload = frame
                if opcode == 0x8:
                    send_ws_frame("", opcode=0x8)
                    break
                if opcode == 0x9:
                    send_ws_frame(payload, opcode=0xA)
                    continue
                if opcode == 0xA:
                    continue
                if opcode != 0x1:
                    continue
                message = payload.decode("utf-8", errors="replace")
                query = parse_qs(urlparse(self.path).query)
                channel = query.get("channel", ["dashboard"])[0]
                try:
                    parsed_message = json.loads(message)
                except json.JSONDecodeError:
                    parsed_message = {"text": message}
                event = {
                    "id": int(time.time() * 1000),
                    "channel": channel,
                    "event": parsed_message.get("event", "websocket.message"),
                    "payload": parsed_message,
                    "publishedAt": now_iso(),
                    "transport": "websocket",
                }
                with LOCK:
                    events = read_json(REALTIME_EVENTS)
                    events.append(event)
                    write_json(REALTIME_EVENTS, events)
                response = json.dumps({"type": "echo", "receivedAt": now_iso(), "channel": channel, "message": message})
                send_ws_frame(response)
        finally:
            keepalive_stop.set()

    def _read_ws_frame(self):
        header = self.rfile.read(2)
        if len(header) < 2:
            return None
        first, second = header
        opcode = first & 0x0F
        masked = second & 0x80
        length = second & 0x7F
        if length == 126:
            length = struct.unpack("!H", self.rfile.read(2))[0]
        elif length == 127:
            length = struct.unpack("!Q", self.rfile.read(8))[0]
        mask = self.rfile.read(4) if masked else b"\x00\x00\x00\x00"
        payload = bytearray(self.rfile.read(length))
        if masked:
            for index in range(length):
                payload[index] ^= mask[index % 4]
        return opcode, bytes(payload)

    def _write_ws_frame(self, message, opcode=0x1):
        payload = message.encode("utf-8") if isinstance(message, str) else message
        header = bytearray([0x80 | opcode])
        length = len(payload)
        if length < 126:
            header.append(length)
        elif length < 65536:
            header.extend([126])
            header.extend(struct.pack("!H", length))
        else:
            header.extend([127])
            header.extend(struct.pack("!Q", length))
        self.wfile.write(bytes(header) + payload)
        self.wfile.flush()


def _sample_records():
    return [
        {"id": 1, "sensor": "temperature", "value": 27.5, "unit": "celsius"},
        {"id": 2, "sensor": "humidity", "value": 61, "unit": "percent"},
        {"id": 3, "sensor": "latency", "value": 118, "unit": "ms"},
    ]


def _orders():
    source = ORDERS if ORDERS.exists() else ORDERS_SEED
    return read_json(source)


def _protocol_case():
    return {
        "scenario": "Retail analytics platform membutuhkan API ingestion, telemetry sensor, realtime notification, dan inference service.",
        "options": [
            {"protocol": "REST", "bestFor": "public API ingestion and CRUD", "tradeoff": "request-response, not real-time by default"},
            {"protocol": "WebSocket", "bestFor": "dashboard notification and bidirectional event", "tradeoff": "persistent connection management"},
            {"protocol": "MQTT", "bestFor": "IoT telemetry and pub/sub", "tradeoff": "needs broker and topic governance"},
            {"protocol": "gRPC", "bestFor": "internal service-to-service contract", "tradeoff": "less beginner-friendly for browser public API"},
        ],
        "discussionQuestion": "Protocol mana yang dipilih untuk tiap komponen dan evidence apa yang harus dikumpulkan?",
    }


def _proto_contract():
    return """syntax = "proto3";

package demo.inference;

service InferenceService {
  rpc Predict (PredictionRequest) returns (PredictionReply);
  rpc BatchPredict (BatchPredictionRequest) returns (BatchPredictionReply);
  rpc HealthCheck (HealthCheckRequest) returns (HealthCheckReply);
}

message PredictionRequest {
  string customer_id = 1;
  FeatureVector features = 2;
}

message FeatureVector {
  double avg_order_value = 1;
  int32 monthly_orders = 2;
}

message PredictionReply {
  string customer_id = 1;
  double score = 2;
  string label = 3;
  string model_version = 4;
}

message BatchPredictionRequest {
  repeated PredictionRequest items = 1;
}

message BatchPredictionReply {
  repeated PredictionReply predictions = 1;
}

message HealthCheckRequest {}

message HealthCheckReply {
  string status = 1;
  string transport = 2;
}
"""


def _telemetry_proto_schema():
    return """syntax = "proto3";

package demo.telemetry;

message TelemetryRecord {
  int32 id = 1;
  string sensor = 2;
  double value = 3;
  string unit = 4;
  int64 captured_at_unix_ms = 5;
}

message TelemetryBatch {
  repeated TelemetryRecord records = 1;
}
"""


def _grpc_services():
    return {
        "services": [
            {
                "name": "demo.inference.InferenceService",
                "methods": [
                    {
                        "name": "Predict",
                        "type": "unary",
                        "request": "PredictionRequest",
                        "response": "PredictionReply",
                        "samplePayload": {
                            "customerId": "C-1024",
                            "features": {"avgOrderValue": 250000, "monthlyOrders": 7},
                        },
                    },
                    {
                        "name": "BatchPredict",
                        "type": "unary",
                        "request": "BatchPredictionRequest",
                        "response": "BatchPredictionReply",
                        "samplePayload": {"items": default_batch_prediction_items()},
                    },
                    {
                        "name": "HealthCheck",
                        "type": "unary",
                        "request": "HealthCheckRequest",
                        "response": "HealthCheckReply",
                        "samplePayload": {},
                    },
                ],
            }
        ],
        "usage": {
            "editProtoRequired": False,
            "note": "Untuk demo P5 standar, mahasiswa cukup memilih method dan mengirim JSON payload. Edit .proto hanya diperlukan jika ingin menambah field atau RPC method baru.",
            "realHttp2Endpoint": "POST /api/grpc/http2-call",
            "conceptEndpoint": "POST /api/grpc/call",
        },
        "teachingPoint": "gRPC exposes service methods with schema-defined request and response messages.",
    }


def _grpc_call(body):
    method = body.get("method", "Predict")
    payload = body.get("payload", {})
    if method == "HealthCheck":
        return {
            "method": method,
            "requestMessage": "HealthCheckRequest",
            "responseMessage": "HealthCheckReply",
            "status": "SERVING",
            "transport": "concept mock over HTTP/1.1",
            "protoEditRequired": False,
            "protocolConcept": "Unary RPC without business payload, commonly used to check service readiness.",
        }
    if method == "BatchPredict":
        items = batch_prediction_items(payload)
        predictions = []
        for index, item in enumerate(items):
            score = score_prediction_payload(item)
            predictions.append({
                "index": index,
                "customerId": item.get("customerId", item.get("customer_id", f"C-BATCH-{index + 1:03d}")),
                "score": score,
                "label": "high_value" if score >= 0.6 else "standard",
                "modelVersion": GRPC_MODEL_VERSION,
            })
        return {
            "method": method,
            "requestMessage": "BatchPredictionRequest",
            "responseMessage": "BatchPredictionReply",
            "count": len(predictions),
            "predictions": predictions,
            "protoEditRequired": False,
            "protocolConcept": "BatchPredict sends repeated PredictionRequest items and receives repeated PredictionReply predictions.",
        }
    score = score_prediction_payload(payload)
    return {
        "method": method,
        "requestMessage": "PredictionRequest",
        "responseMessage": "PredictionReply",
        "customerId": payload.get("customerId", body.get("customerId")),
        "score": round(score, 3),
        "label": "high_value" if score >= 0.6 else "standard",
        "modelVersion": GRPC_MODEL_VERSION,
        "protoEditRequired": False,
        "protocolConcept": "This endpoint simulates a gRPC method call using JSON for classroom visibility.",
    }



def telemetry_message_classes():
    """Build dynamic Protocol Buffers classes for P6/P14/UAS telemetry encoding.

    This keeps the classroom demo self-contained: students don't need protoc,
    but the endpoint still returns real protobuf binary bytes encoded as base64
    for safe display in JSON/Postman.
    """
    global TELEMETRY_MESSAGE_CLASSES
    if TELEMETRY_MESSAGE_CLASSES is not None:
        return TELEMETRY_MESSAGE_CLASSES
    if descriptor_pb2 is None or descriptor_pool is None or message_factory is None:
        raise RuntimeError("protobuf belum terinstall. Jalankan: python -m pip install -r requirements.txt")

    file_proto = descriptor_pb2.FileDescriptorProto()
    file_proto.name = "telemetry.proto"
    file_proto.package = "demo.telemetry"
    file_proto.syntax = "proto3"

    telemetry_record = file_proto.message_type.add()
    telemetry_record.name = "TelemetryRecord"
    add_proto_field(telemetry_record, "id", 1, descriptor_pb2.FieldDescriptorProto.TYPE_INT32)
    add_proto_field(telemetry_record, "sensor", 2, descriptor_pb2.FieldDescriptorProto.TYPE_STRING)
    add_proto_field(telemetry_record, "value", 3, descriptor_pb2.FieldDescriptorProto.TYPE_DOUBLE)
    add_proto_field(telemetry_record, "unit", 4, descriptor_pb2.FieldDescriptorProto.TYPE_STRING)
    add_proto_field(telemetry_record, "captured_at_unix_ms", 5, descriptor_pb2.FieldDescriptorProto.TYPE_INT64)

    telemetry_batch = file_proto.message_type.add()
    telemetry_batch.name = "TelemetryBatch"
    add_proto_field(
        telemetry_batch,
        "records",
        1,
        descriptor_pb2.FieldDescriptorProto.TYPE_MESSAGE,
        label=descriptor_pb2.FieldDescriptorProto.LABEL_REPEATED,
        type_name=".demo.telemetry.TelemetryRecord",
    )

    pool = descriptor_pool.DescriptorPool()
    pool.Add(file_proto)
    TELEMETRY_MESSAGE_CLASSES = {
        "TelemetryRecord": message_class(pool, "demo.telemetry.TelemetryRecord"),
        "TelemetryBatch": message_class(pool, "demo.telemetry.TelemetryBatch"),
    }
    return TELEMETRY_MESSAGE_CLASSES


def encode_telemetry_protobuf(records):
    classes = telemetry_message_classes()
    batch = classes["TelemetryBatch"]()
    now_ms = int(time.time() * 1000)
    for item in records:
        rec = batch.records.add()
        rec.id = int(item.get("id", 0) or 0)
        rec.sensor = str(item.get("sensor", item.get("name", "unknown")))
        rec.value = float(item.get("value", 0) or 0)
        rec.unit = str(item.get("unit", ""))
        rec.captured_at_unix_ms = int(item.get("captured_at_unix_ms", item.get("capturedAtUnixMs", now_ms)) or now_ms)
    raw = batch.SerializeToString()
    if json_format is not None:
        decoded = json_format.MessageToDict(batch, preserving_proto_field_name=True)
    else:
        decoded = {"records": [dict(item) for item in records]}
    return raw, decoded

def _encoding_convert(body):
    records = body.get("records") or _sample_records()
    target = body.get("to", body.get("format", "json")).lower()
    if target == "json":
        encoded = json.dumps({"records": records}, indent=2)
        mime = "application/json"
    elif target == "xml":
        encoded_records = "".join(
            f"<record><id>{r.get('id')}</id><sensor>{r.get('sensor')}</sensor><value>{r.get('value')}</value><unit>{r.get('unit')}</unit></record>"
            for r in records
        )
        encoded = f'<?xml version="1.0" encoding="UTF-8"?><telemetry>{encoded_records}</telemetry>'
        mime = "application/xml"
    elif target == "csv":
        encoded = "id,sensor,value,unit\n" + "\n".join(
            f"{r.get('id')},{r.get('sensor')},{r.get('value')},{r.get('unit')}" for r in records
        )
        mime = "text/csv"
    elif target == "protobuf":
        try:
            raw, decoded = encode_telemetry_protobuf(records)
        except RuntimeError as exc:
            return {"error": str(exc), "install": "python -m pip install -r requirements.txt"}
        encoded = base64.b64encode(raw).decode("ascii")
        mime = "application/x-protobuf"
        return {
            "target": target,
            "mime": mime,
            "byteLength": len(raw),
            "encodedBase64": encoded,
            "decodedJson": decoded,
            "schema": _telemetry_proto_schema(),
            "note": "Actual Protocol Buffers binary is returned as base64 so Postman/browser can display it safely.",
        }
    else:
        return {"error": "Unsupported target format", "supported": ["json", "xml", "csv", "protobuf"]}
    return {
        "target": target,
        "mime": mime,
        "byteLength": len(encoded.encode("utf-8")),
        "encoded": encoded,
        "note": "Text encoding output for JSON/XML/CSV classroom comparison.",
    }


def _openapi_spec():
    return {
        "openapi": "3.0.3",
        "info": {
            "title": "Communication Protocols Demo API",
            "version": "1.0.0",
            "description": "Teaching API for Postman documentation, Newman-style testing, reliability, microservices, observability, and n8n automation labs.",
        },
        "servers": [{"url": "http://localhost:8088"}],
        "paths": {
            "/api/capture/matrix": {"get": {"summary": "Show Wireshark capture guide per meeting"}},
            "/api/capture/run": {"post": {"summary": "Run selected protocol capture scenario"}},
            "/api/realtime/events": {"get": {"summary": "Read realtime events by channel"}, "post": {"summary": "Publish realtime event"}},
            "/api/websocket/real-status": {"get": {"summary": "Show WebSocket capture guidance"}},
            "/api/websocket/real-send": {"post": {"summary": "Trigger real WebSocket HTTP Upgrade and text frame"}},
            "/api/products": {"get": {"summary": "List products"}, "post": {"summary": "Create product"}},
            "/api/products/{id}": {"get": {"summary": "Read product"}, "put": {"summary": "Replace product"}, "patch": {"summary": "Patch product"}, "delete": {"summary": "Delete product"}},
            "/api/users": {"get": {"summary": "List users"}, "post": {"summary": "Create user"}},
            "/api/users/{id}": {"get": {"summary": "Read user"}, "put": {"summary": "Replace user"}, "patch": {"summary": "Patch user"}, "delete": {"summary": "Delete user"}},
            "/api/profiles": {"get": {"summary": "List profiles"}, "post": {"summary": "Create profile"}},
            "/api/profiles/{id}": {"get": {"summary": "Read profile"}, "put": {"summary": "Replace profile"}, "patch": {"summary": "Patch profile"}, "delete": {"summary": "Delete profile"}},
            "/api/orders": {"get": {"summary": "List orders"}, "post": {"summary": "Create order"}},
            "/api/orders/{id}": {"get": {"summary": "Read order"}, "put": {"summary": "Replace order"}, "patch": {"summary": "Patch order"}, "delete": {"summary": "Delete order"}},
            "/api/transactions": {"get": {"summary": "List transactions"}, "post": {"summary": "Create transaction"}},
            "/api/transactions/{id}": {"get": {"summary": "Read transaction"}, "put": {"summary": "Replace transaction"}, "patch": {"summary": "Patch transaction"}, "delete": {"summary": "Delete transaction"}},
            "/api/uts/cases": {"get": {"summary": "List UTS REST API case resources and required fields"}},
            "/api/mqtt/messages": {"get": {"summary": "Read MQTT-style messages by topic or filter"}},
            "/api/mqtt/publish": {"post": {"summary": "Publish MQTT-style telemetry with clientId, QoS, retained flag, topic, and payload"}},
            "/api/mqtt/real-status": {"get": {"summary": "Check embedded real MQTT broker on TCP port 1883"}},
            "/api/mqtt/real-publish": {"post": {"summary": "Trigger real MQTT 3.1.1 packets to TCP port 1883 for Wireshark capture"}},
            "/api/mqtt/session/status": {"get": {"summary": "Show active persistent MQTT demo sessions"}},
            "/api/mqtt/session/start": {"post": {"summary": "Start persistent MQTT session with keepalive PINGREQ/PINGRESP packets"}},
            "/api/mqtt/session/stop": {"post": {"summary": "Stop one or all persistent MQTT demo sessions"}},
            "/api/grpc/services": {"get": {"summary": "List gRPC-style services and methods"}},
            "/api/grpc/call": {"post": {"summary": "Simulate dynamic gRPC method call"}},
            "/api/grpc/http2-status": {"get": {"summary": "Check integrated gRPC HTTP/2 server status"}},
            "/api/grpc/http2-call": {"post": {"summary": "Trigger a real local gRPC HTTP/2 call to port 50051"}},
            "/api/encoding/convert": {"post": {"summary": "Convert records to JSON, XML, CSV, or Protobuf demo encoding"}},
            "/api/tls/status": {"get": {"summary": "Show TLS capture guidance"}},
            "/api/tls/self-test": {"post": {"summary": "Trigger HTTPS/TLS request to port 8443"}},
            "/api/troubleshooting/test": {"post": {"summary": "Create controlled status code and delay scenario"}},
            "/api/reliability/rate-limited": {"get": {"summary": "Demonstrate 429 rate limiting"}},
            "/api/reliability/load-balanced": {"get": {"summary": "Demonstrate backend distribution"}},
            "/api/reliability/simulate-load": {"post": {"summary": "Simulate multiple load-balanced requests"}},
            "/api/microservices/order-flow": {"get": {"summary": "Show microservices communication pattern"}},
            "/api/microservices/orders": {"post": {"summary": "Simulate order flow with optional failure point"}},
            "/api/observability/metrics": {"get": {"summary": "Show request metrics"}},
            "/api/observability/custom-log": {"post": {"summary": "Create a custom log event"}},
            "/api/observability/capture-scenario": {"post": {"summary": "Trigger observability scenario with HTTP and MQTT evidence"}},
            "/api/automation/inbox": {"get": {"summary": "Read automation inbox"}, "post": {"summary": "Receive n8n workflow output"}},
            "/api/automation/workflow-run": {"post": {"summary": "Simulate n8n workflow execution"}},
            "/api/project/capture-demo": {"post": {"summary": "Run integrated UAS multi-protocol capture demo"}},
        },
        "teachingUse": "Pertemuan 9: document endpoints, define environment variables, add tests, and export collection evidence.",
    }


def _postman_run_summary():
    return {
        "meeting": 9,
        "topic": "API Design & Documentation using Postman and Newman/Postman CLI",
        "postmanCollection": "postman/Communication_Protocols_Demo_App.postman_collection.json",
        "environmentVariable": {"base_url": "http://localhost:8088"},
        "suggestedTests": [
            "Status code is expected",
            "Response has required field",
            "Latency is below a selected classroom threshold",
            "Mutation is verified by a read-back request",
        ],
        "newmanCommandExamples": [
            "newman run postman/Communication_Protocols_Demo_App.postman_collection.json --env-var base_url=http://localhost:8088",
            "newman run postman/Communication_Protocols_Demo_App.postman_collection.json --folder \"P9 API Documentation and Newman\" --env-var base_url=http://localhost:8088"
        ],
        "note": "Newman requires Node.js/npm installation. If unavailable, use Postman Collection Runner and export screenshots as fallback.",
    }


def _postman_run(body):
    folder = body.get("folder", "P9 API Documentation and Newman")
    iterations = min(int(body.get("iterations", 1)), 10)
    tests = [
        {"name": "status code is expected", "passed": True},
        {"name": "response time below classroom threshold", "passed": True},
        {"name": "required field exists", "passed": True},
    ]
    return {
        "runner": "postman-runner-simulator",
        "folder": folder,
        "iterations": iterations,
        "totalRequests": iterations * 3,
        "tests": tests,
        "summary": {"passed": len(tests) * iterations, "failed": 0},
        "teachingPoint": "Use this as a local stand-in if Newman is unavailable; real Newman should be run from CLI when installed.",
    }


def _microservice_order_flow(body=None):
    order_id = (body or {}).get("orderId", "ORD-DEMO-001")
    amount = (body or {}).get("amount", 450000)
    fail_at = (body or {}).get("failAt")
    protocol_evidence = None
    if (body or {}).get("wireCapture"):
        protocol_evidence = {
            "grpcInference": grpc_http2_call({
                "method": "Predict",
                "payload": {
                    "customerId": order_id,
                    "features": {"avgOrderValue": amount, "monthlyOrders": 6},
                },
            }),
            "mqttNotification": mqtt_real_publish({
                "clientId": "order-service",
                "topic": "class/commproto/orders/status",
                "filter": "class/commproto/+/status",
                "qos": 1,
                "payload": {"orderId": order_id, "status": "created", "amount": amount},
            }),
        }
    steps = [
        {"service": "api-gateway", "protocol": "HTTP/REST", "latencyMs": 24, "status": 200},
        {"service": "order-service", "protocol": "gRPC internal call", "latencyMs": 41, "status": "OK"},
        {"service": "inventory-service", "protocol": "HTTP/REST", "latencyMs": 38, "status": 200},
        {"service": "payment-service", "protocol": "HTTP/REST", "latencyMs": 76, "status": 200},
        {"service": "notification-service", "protocol": "WebSocket event", "latencyMs": 18, "status": "sent"},
    ]
    if fail_at:
        for step in steps:
            if step["service"] == fail_at:
                step["status"] = "FAILED"
                step["error"] = f"Simulated failure at {fail_at}"
    return {
        "traceId": f"trace-{order_id.lower()}",
        "pattern": "API gateway -> order service -> inventory service -> payment service -> notification service",
        "request": {"orderId": order_id, "amount": amount},
        "steps": steps,
        "protocolEvidence": protocol_evidence,
        "teachingPoint": "Microservices communication needs clear contracts, timeouts, retries, and observability across service boundaries.",
    }


def _metrics():
    status_counts = {}
    path_counts = {}
    for entry in REQUEST_LOGS:
        status_counts[str(entry["status"])] = status_counts.get(str(entry["status"]), 0) + 1
        path_counts[entry["path"]] = path_counts.get(entry["path"], 0) + 1
    return {
        "requestCount": len(REQUEST_LOGS),
        "statusCounts": status_counts,
        "topPaths": sorted(path_counts.items(), key=lambda item: item[1], reverse=True)[:8],
        "rateLimitClients": {client: len(hits) for client, hits in RATE_HITS.items()},
        "teachingPoint": "Metrics aggregate behavior; logs explain individual events; traces connect events across services.",
    }


def _trace(trace_id):
    return {
        "traceId": trace_id,
        "spans": [
            {"span": "gateway.receive", "durationMs": 12, "status": "OK"},
            {"span": "order.validate", "durationMs": 20, "status": "OK"},
            {"span": "inventory.reserve", "durationMs": 43, "status": "OK"},
            {"span": "payment.authorize", "durationMs": 88, "status": "OK"},
            {"span": "notification.publish", "durationMs": 16, "status": "OK"},
        ],
        "teachingPoint": "Trace shows one request path across multiple components.",
    }


def _n8n_workflow_spec():
    return {
        "meeting": "Pertemuan 13-15",
        "topic": "Automation using n8n for protocol integration and project phase",
        "recommendedWorkflow": [
            "Webhook Trigger receives JSON payload",
            "Set node normalizes fields: protocol, event, evidence",
            "HTTP Request node POSTs to http://localhost:8088/api/automation/inbox",
            "Respond to Webhook returns confirmation",
        ],
        "dockerNote": "If n8n runs inside Docker, replace localhost with host.docker.internal when calling the demo app.",
        "sampleWebhookPayload": {
            "protocol": "MQTT+REST",
            "event": "telemetry.ingested",
            "deviceId": "sensor-01",
            "evidence": "postman-screenshot",
        },
        "fallback": "If n8n setup fails, simulate the automation output by POSTing directly to /api/automation/inbox from Postman.",
    }


def _automation_run(body):
    workflow = body.get("workflow", "telemetry-to-inbox")
    source_event = body.get("event", "telemetry.workflow.completed")
    protocol_evidence = None
    if body.get("wireCapture"):
        trigger_payload = body.get("triggerPayload", {})
        protocol_evidence = {
            "mqttTelemetry": mqtt_real_publish({
                "clientId": "n8n-automation-simulator",
                "topic": "class/commproto/automation/telemetry",
                "filter": "class/commproto/+/telemetry",
                "qos": 1,
                "payload": trigger_payload or {"event": source_event, "workflow": workflow},
            }),
            "httpEndpoint": "/api/automation/workflow-run",
        }
    return {
        "workflow": workflow,
        "runId": f"run-{int(time.time() * 1000)}",
        "status": "success",
        "steps": [
            {"node": "Webhook Trigger", "status": "success", "output": {"event": source_event}},
            {"node": "Set/Edit Fields", "status": "success", "output": {"normalized": True}},
            {"node": "HTTP Request", "status": "success", "output": {"target": "/api/automation/inbox"}},
            {"node": "Respond to Webhook", "status": "success", "output": {"status": "accepted"}},
        ],
        "protocolEvidence": protocol_evidence,
        "teachingPoint": "Automation evidence should show trigger input, transformation, HTTP call, and final response.",
    }


def _project_summary():
    messages = read_json(MESSAGES)
    return {
        "minimumRequirements": [
            "Use at least two protocol concepts",
            "Provide Postman/curl evidence",
            "Explain status code or message flow",
            "Include troubleshooting notes",
            "Include automation or integration evidence when using n8n",
        ],
        "currentEvidenceCount": len(messages),
        "suggestedProject": "MQTT telemetry + WebSocket notification + n8n automation + Postman/Newman evidence",
    }


if __name__ == "__main__":
    DATA.mkdir(exist_ok=True)
    for config in API_RESOURCES.values():
        if not config["file"].exists():
            shutil.copyfile(config["seed"], config["file"])
    if not MESSAGES.exists():
        write_json(MESSAGES, [])
    if not WEBHOOK_INBOX.exists():
        write_json(WEBHOOK_INBOX, [])
    if not AUTOMATION_INBOX.exists():
        write_json(AUTOMATION_INBOX, [])
    if not REALTIME_EVENTS.exists():
        write_json(REALTIME_EVENTS, [])

    mqtt_server = start_mqtt_broker()
    grpc_server = start_grpc_http2_server()
    tls_server = start_tls_server()
    server = ThreadingHTTPServer((HOST, PORT), DemoHandler)
    print(f"Communication Protocols Demo App running at http://{HOST}:{PORT}")
    print("Press Ctrl+C to stop.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped.")
    finally:
        stop_all_mqtt_sessions()
        server.server_close()
        if grpc_server is not None:
            grpc_server.stop(grace=1)
            GRPC_SERVER_ACTIVE = False
        if mqtt_server is not None:
            mqtt_server.shutdown()
            mqtt_server.server_close()
        if tls_server is not None:
            tls_server.shutdown()
            tls_server.server_close()
