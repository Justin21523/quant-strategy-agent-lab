#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

if [[ ! -x .venv/bin/python ]]; then
  echo "Missing .venv. Run ./scripts/bootstrap.sh first." >&2
  exit 1
fi

if [[ ! -d frontend/node_modules ]]; then
  echo "Missing frontend/node_modules. Run ./scripts/bootstrap.sh first." >&2
  exit 1
fi

if ! command -v setsid >/dev/null 2>&1; then
  echo "setsid is required (normally provided by util-linux on Linux)." >&2
  exit 1
fi

backend_pid=""
frontend_pid=""

stop_process_group() {
  local leader_pid="$1"
  if [[ -n "$leader_pid" ]] && kill -0 "$leader_pid" 2>/dev/null; then
    kill -TERM -- "-$leader_pid" 2>/dev/null || kill -TERM "$leader_pid" 2>/dev/null || true
  fi
}

cleanup() {
  local exit_code=$?
  trap - INT TERM EXIT
  stop_process_group "$backend_pid"
  stop_process_group "$frontend_pid"
  wait 2>/dev/null || true
  exit "$exit_code"
}
trap cleanup INT TERM EXIT

setsid .venv/bin/python -m uvicorn app.main:app \
  --app-dir backend \
  --host 127.0.0.1 \
  --port 8000 \
  --reload &
backend_pid=$!

backend_ready=0
for _ in $(seq 1 40); do
  if .venv/bin/python -c \
    "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/api/v1/health', timeout=0.5)" \
    >/dev/null 2>&1; then
    backend_ready=1
    break
  fi
  sleep 0.25
done

if [[ "$backend_ready" -ne 1 ]]; then
  echo "FastAPI did not become healthy on http://127.0.0.1:8000." >&2
  exit 1
fi

setsid npm --prefix frontend run dev -- --host 127.0.0.1 &
frontend_pid=$!

wait -n "$backend_pid" "$frontend_pid"
