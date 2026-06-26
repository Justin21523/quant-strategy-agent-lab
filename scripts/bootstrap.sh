#!/usr/bin/env bash
set -Eeuo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT_DIR}"

command -v python3 >/dev/null 2>&1 || { echo 'python3 is required.' >&2; exit 1; }
command -v node >/dev/null 2>&1 || { echo 'Node.js is required.' >&2; exit 1; }
command -v npm >/dev/null 2>&1 || { echo 'npm is required.' >&2; exit 1; }

python3 -c 'import sys; assert sys.version_info >= (3, 11), "Python 3.11+ is required"'
node -e 'const [M,m]=process.versions.node.split(".").map(Number); if(!((M===20&&m>=19)||(M===22&&m>=12)||M>22)){throw new Error("Use Node 20.19+, 22.12+, or newer")}'

if [[ ! -d .venv ]]; then
  python3 -m venv .venv
fi

.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -r backend/requirements-dev.txt

if [[ ! -f backend/.env ]]; then
  cp backend/.env.example backend/.env
fi

npm --prefix frontend ci --no-audit --no-fund

printf '\nBootstrap complete. Run: make dev\n'
