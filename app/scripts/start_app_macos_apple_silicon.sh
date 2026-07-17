#!/usr/bin/env bash
set -euo pipefail

# Communication Protocols Demo App - macOS Apple Silicon (M1/M2/M3/M4)
# Run from any location; this script resolves the package root automatically.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PACKAGE_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
APP_DIR="$PACKAGE_ROOT/app"
VENV_DIR="$APP_DIR/.venv-macos-arm64"

cd "$APP_DIR"

if ! command -v python3 >/dev/null 2>&1; then
  echo "ERROR: python3 not found. Install Python 3 from https://www.python.org/downloads/macos/ or Homebrew."
  exit 1
fi

ARCH="$(uname -m)"
if [[ "$ARCH" != "arm64" ]]; then
  echo "WARNING: This script is optimized for Apple Silicon arm64. Current arch: $ARCH"
fi

PY_VERSION="$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")')"
echo "Using Python $PY_VERSION on $ARCH"

if [[ ! -d "$VENV_DIR" ]]; then
  echo "Creating virtual environment: $VENV_DIR"
  python3 -m venv "$VENV_DIR"
fi

source "$VENV_DIR/bin/activate"
python -m pip install --upgrade pip setuptools wheel
python -m pip install -r requirements.txt

echo ""
echo "Starting Communication Protocols Demo App..."
echo "HTTP UI/API : http://localhost:8088"
echo "MQTT broker : 127.0.0.1:1883"
echo "gRPC demo  : 127.0.0.1:50051"
echo "TLS demo   : https://127.0.0.1:8443"
echo ""
echo "For n8n running in Docker Desktop, use this target URL inside HTTP Request node:"
echo "  http://host.docker.internal:8088/api/reliability/rate-limited"
echo ""

# Keep localhost binding on macOS. Docker Desktop can reach host loopback through host.docker.internal.
export COMM_PROTO_HOST="${COMM_PROTO_HOST:-127.0.0.1}"
python server.py
