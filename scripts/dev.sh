#!/usr/bin/env bash
set -Eeuo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

find_free_port() {
  python3 - <<'PY'
import socket
with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
    sock.bind(("127.0.0.1", 0))
    print(sock.getsockname()[1])
PY
}

BACKEND_PORT="${BACKEND_PORT:-$(find_free_port)}"
FRONTEND_PORT="${FRONTEND_PORT:-$(find_free_port)}"

if [[ ! -x "${ROOT_DIR}/.venv/bin/uvicorn" || ! -d "${ROOT_DIR}/frontend/node_modules" ]]; then
  echo 'Dependencies are missing. Run make bootstrap first.' >&2
  exit 1
fi

backend_pid=''
frontend_pid=''

stop_process_group() {
  local pid="${1:-}"

  [[ -z "${pid}" ]] && return 0

  # Each service is started with setsid, so the PID is also its process-group ID.
  # Killing the whole group prevents Vite, npm, or Uvicorn reload children from
  # surviving after this script exits.
  kill -TERM -- "-${pid}" 2>/dev/null || kill -TERM "${pid}" 2>/dev/null || true
}

cleanup() {
  local code=$?
  trap - EXIT INT TERM

  stop_process_group "${frontend_pid}"
  stop_process_group "${backend_pid}"

  wait "${frontend_pid}" 2>/dev/null || true
  wait "${backend_pid}" 2>/dev/null || true

  exit "${code}"
}
trap cleanup EXIT INT TERM

setsid "${ROOT_DIR}/.venv/bin/uvicorn" app.main:app \
  --app-dir "${ROOT_DIR}/backend" \
  --reload \
  --host 0.0.0.0 \
  --port "${BACKEND_PORT}" &
backend_pid=$!

backend_ready=false
for _ in {1..80}; do
  if curl -fsS "http://127.0.0.1:${BACKEND_PORT}/api/v1/health" >/dev/null 2>&1; then
    backend_ready=true
    break
  fi
  sleep 0.1
done

if [[ "${backend_ready}" != true ]]; then
  echo "FastAPI did not become healthy at http://127.0.0.1:${BACKEND_PORT}/api/v1/health." >&2
  exit 1
fi

if ! kill -0 "${backend_pid}" 2>/dev/null; then
  echo 'FastAPI failed to start.' >&2
  exit 1
fi

BACKEND_PORT="${BACKEND_PORT}" \
FRONTEND_PORT="${FRONTEND_PORT}" \
VITE_API_DOCS_URL="http://127.0.0.1:${BACKEND_PORT}/docs" \
setsid npm --prefix "${ROOT_DIR}/frontend" run dev -- \
  --host 0.0.0.0 \
  --port "${FRONTEND_PORT}" \
  --strictPort &
frontend_pid=$!

cat <<EOF
FastAPI: http://127.0.0.1:${BACKEND_PORT}
Swagger: http://127.0.0.1:${BACKEND_PORT}/docs
ReDoc: http://127.0.0.1:${BACKEND_PORT}/redoc
Frontend: http://127.0.0.1:${FRONTEND_PORT}
Market Data Lab: http://127.0.0.1:${FRONTEND_PORT}/#/market-data
Strategy Builder: http://127.0.0.1:${FRONTEND_PORT}/#/strategy-builder
Backtest Lab: http://127.0.0.1:${FRONTEND_PORT}/#/backtest-lab
EOF

wait -n "${backend_pid}" "${frontend_pid}"
