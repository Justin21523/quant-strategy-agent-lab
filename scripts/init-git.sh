#!/usr/bin/env bash
set -Eeuo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT_DIR}"
if [[ -d .git ]]; then
  echo 'Git repository already exists.'
  exit 0
fi
git init
git branch -M main
git add .
printf 'Git initialized. Suggested commit:\n  git commit -m "chore: bootstrap phase 0 project foundation"\n'
