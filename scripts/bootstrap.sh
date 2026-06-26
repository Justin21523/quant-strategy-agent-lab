#!/usr/bin/env bash
set -Eeuo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT_DIR}"

command -v node >/dev/null 2>&1 || { echo 'Node.js is required.' >&2; exit 1; }
command -v npm >/dev/null 2>&1 || { echo 'npm is required.' >&2; exit 1; }

PYTHON_BIN="${PYTHON:-}"
if [[ -z "${PYTHON_BIN}" ]]; then
  for candidate in python3.12 python3.11 python3; do
    if command -v "${candidate}" >/dev/null 2>&1 \
      && "${candidate}" -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 11) else 1)'; then
      PYTHON_BIN="${candidate}"
      break
    fi
  done
fi

if [[ -z "${PYTHON_BIN}" ]] || ! command -v "${PYTHON_BIN}" >/dev/null 2>&1; then
  echo 'Python 3.11+ is required.' >&2
  exit 1
fi

"${PYTHON_BIN}" -c 'import sys; assert sys.version_info >= (3, 11), "Python 3.11+ is required"'
node -e 'const [M,m]=process.versions.node.split(".").map(Number); if(!((M===20&&m>=19)||(M===22&&m>=12)||M>22)){throw new Error("Use Node 20.19+, 22.12+, or newer")}'

if [[ ! -d .venv ]]; then
  "${PYTHON_BIN}" -m venv .venv
fi

.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -r backend/requirements-dev.txt

if [[ ! -f backend/.env ]]; then
  cp backend/.env.example backend/.env
fi

npm --prefix frontend ci \
  --registry "${NPM_CONFIG_REGISTRY:-https://registry.npmjs.org/}" \
  --replace-registry-host=always \
  --no-audit \
  --no-fund

printf '\nBootstrap complete. Run: make dev\n'
