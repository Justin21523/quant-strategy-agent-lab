#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

if [[ ! -x .venv/bin/python || ! -d frontend/node_modules ]]; then
  echo "Dependencies are missing. Run ./scripts/bootstrap.sh first." >&2
  exit 1
fi

.venv/bin/python -m ruff check backend
npm --prefix frontend run lint
.venv/bin/python -m pytest backend/tests
npm --prefix frontend test
npm --prefix frontend run build

echo "All Phase 0 checks passed."
