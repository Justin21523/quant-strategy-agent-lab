#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

command -v python3 >/dev/null 2>&1 || { echo "python3 is required" >&2; exit 1; }
command -v node >/dev/null 2>&1 || { echo "Node.js is required" >&2; exit 1; }
command -v npm >/dev/null 2>&1 || { echo "npm is required" >&2; exit 1; }

python3 - <<'PY_CHECK'
import sys
minimum = (3, 11)
if sys.version_info < minimum:
    raise SystemExit(
        f"Python {minimum[0]}.{minimum[1]}+ is required; found {sys.version.split()[0]}"
    )
print(f"Python: {sys.version.split()[0]}")
PY_CHECK

node - <<'JS_CHECK'
const [major, minor] = process.versions.node.split('.').map(Number);
const supported = (major === 20 && minor >= 19) || (major === 22 && minor >= 12) || major > 22;
if (!supported) {
  console.error(`Node.js 20.19+, 22.12+, or newer is required; found ${process.versions.node}`);
  process.exit(1);
}
console.log(`Node.js: ${process.versions.node}`);
JS_CHECK

if [[ ! -d .venv ]]; then
  python3 -m venv .venv
fi

.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -r backend/requirements-dev.txt
npm --prefix frontend ci

if [[ ! -f .env ]]; then
  cp .env.example .env
  echo "Created .env from .env.example"
fi

printf '\nBootstrap complete. Run ./scripts/dev.sh\n'
