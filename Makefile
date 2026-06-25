.PHONY: help bootstrap backend-dev frontend-dev dev test test-backend test-frontend lint format build check clean

VENV_DIR ?= .venv
VENV_PYTHON := $(VENV_DIR)/bin/python

help:
	@printf '%s\n' \
	  'Quant Strategy Agent Lab commands:' \
	  '  make bootstrap      Install backend and frontend dependencies' \
	  '  make dev            Start FastAPI and Vite together' \
	  '  make backend-dev    Start FastAPI only' \
	  '  make frontend-dev   Start Vite only' \
	  '  make test           Run backend and frontend tests' \
	  '  make lint           Run Ruff and ESLint' \
	  '  make format         Format backend code' \
	  '  make build          Build the frontend production bundle' \
	  '  make check          Run lint, tests, and frontend build' \
	  '  make clean          Remove local build and cache artifacts'

bootstrap:
	./scripts/bootstrap.sh

backend-dev:
	$(VENV_PYTHON) -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000 --reload

frontend-dev:
	npm --prefix frontend run dev

dev:
	./scripts/dev.sh

test: test-backend test-frontend

test-backend:
	$(VENV_PYTHON) -m pytest backend/tests

test-frontend:
	npm --prefix frontend test

lint:
	$(VENV_PYTHON) -m ruff check backend
	npm --prefix frontend run lint

format:
	$(VENV_PYTHON) -m ruff format backend

build:
	npm --prefix frontend run build

check:
	./scripts/check.sh

clean:
	rm -rf .pytest_cache .ruff_cache backend/.pytest_cache backend/.ruff_cache frontend/dist
	find backend -type d -name __pycache__ -prune -exec rm -rf {} +
