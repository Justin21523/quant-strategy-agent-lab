#!/usr/bin/env bash
set -Eeuo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT_DIR}"

if [[ ! -x .venv/bin/python || ! -d frontend/node_modules ]]; then
  echo 'Dependencies are missing. Run make bootstrap first.' >&2
  exit 1
fi

printf '\n[1/6] Python lint and format\n'
.venv/bin/ruff check backend scripts --config backend/pyproject.toml
.venv/bin/ruff format --check backend scripts --config backend/pyproject.toml

printf '\n[2/6] Backend tests and coverage\n'
(cd backend && ../.venv/bin/python -m pytest)

printf '\n[3/6] Frontend lint\n'
npm --prefix frontend run lint

printf '\n[4/6] Frontend format check\n'
npm --prefix frontend run format:check

printf '\n[5/6] Frontend unit tests\n'
npm --prefix frontend run test

printf '\n[6/6] Frontend production build\n'
npm --prefix frontend run build

printf '\nAll Phase 4 checks passed.\n'
