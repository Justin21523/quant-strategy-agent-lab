SHELL := /usr/bin/env bash
.DEFAULT_GOAL := help

.PHONY: help bootstrap dev backend frontend seed test lint format build check clean init-git

help:
	@printf '%s\n' \
	  'Quant Strategy Agent Lab commands:' \
	  '  make bootstrap  Install backend and frontend dependencies' \
	  '  make dev        Start FastAPI and Vite together' \
	  '  make backend    Start only FastAPI' \
	  '  make frontend   Start only Vite' \
	  '  make seed       Regenerate deterministic offline OHLCV fixtures' \
	  '  make test       Run backend and frontend tests' \
	  '  make lint       Run Python and JavaScript linters' \
	  '  make format     Format backend and frontend code' \
	  '  make build      Build the frontend' \
	  '  make check      Run all Phase 3 quality gates' \
	  '  make clean      Remove generated files and local cache' \
	  '  make init-git   Initialize a local Git repository'

bootstrap:
	./scripts/bootstrap.sh

dev:
	./scripts/dev.sh

backend:
	@test -x .venv/bin/uvicorn || (echo 'Run make bootstrap first.' && exit 1)
	@PORT=$${BACKEND_PORT:-$$(python3 -c "import socket; s=socket.socket(); s.bind((\"127.0.0.1\",0)); print(s.getsockname()[1]); s.close()")} ; \
	printf 'FastAPI: http://127.0.0.1:%s\nSwagger: http://127.0.0.1:%s/docs\nReDoc: http://127.0.0.1:%s/redoc\n' $$PORT $$PORT $$PORT ; \
	.venv/bin/uvicorn app.main:app --app-dir backend --reload --host 0.0.0.0 --port $$PORT

frontend:
	@test -d frontend/node_modules || (echo 'Run make bootstrap first.' && exit 1)
	@PORT=$${FRONTEND_PORT:-$$(python3 -c "import socket; s=socket.socket(); s.bind((\"127.0.0.1\",0)); print(s.getsockname()[1]); s.close()")} ; \
	BACKEND_PORT=$${BACKEND_PORT:-8000} FRONTEND_PORT=$$PORT npm --prefix frontend run dev -- --host 0.0.0.0 --port $$PORT --strictPort

seed:
	python3 scripts/generate_demo_market_data.py

test:
	@test -x .venv/bin/python || (echo 'Run make bootstrap first.' && exit 1)
	cd backend && ../.venv/bin/python -m pytest
	npm --prefix frontend run test

lint:
	@test -x .venv/bin/ruff || (echo 'Run make bootstrap first.' && exit 1)
	.venv/bin/ruff check backend scripts --config backend/pyproject.toml
	npm --prefix frontend run lint

format:
	@test -x .venv/bin/ruff || (echo 'Run make bootstrap first.' && exit 1)
	.venv/bin/ruff format backend scripts --config backend/pyproject.toml
	npm --prefix frontend run format

build:
	npm --prefix frontend run build

check:
	./scripts/check.sh

clean:
	rm -rf .ruff_cache frontend/dist frontend/.vite backend/.pytest_cache backend/.ruff_cache backend/htmlcov
	rm -f .coverage backend/.coverage backend/coverage.xml backend/data/cache/*.sqlite3
	find backend scripts -type d -name '__pycache__' -prune -exec rm -rf {} +
	find backend scripts -type f -name '*.py[co]' -delete

init-git:
	./scripts/init-git.sh
