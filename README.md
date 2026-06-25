# Quant Strategy Agent Lab

> A local-first quantitative strategy research and backtesting workbench built with Python, FastAPI, and modular Vanilla JavaScript.

![Phase](https://img.shields.io/badge/phase-0%20foundation-4f46e5)
![Frontend](https://img.shields.io/badge/frontend-Vanilla%20JavaScript-f7df1e)
![Backend](https://img.shields.io/badge/backend-FastAPI-009688)

## Project status

**Phase 0 — Foundation is implemented.** The repository currently provides:

- a runnable FastAPI application with automatic OpenAPI documentation;
- a runnable Vite-powered Vanilla JavaScript application;
- a modular frontend router, store, event bus, API client, layout, and page structure;
- frontend-to-backend health checking through the Vite development proxy;
- Linux bootstrap, development, lint, test, and build scripts;
- initial architecture, API, development, project-specification, and roadmap documents;
- Dockerfiles and a Compose definition for reproducible container builds.

Market data, indicators, strategy parsing, and backtesting are deliberately **not mocked as finished features**. They enter the project in later phases.

## Product vision

A user will describe a trading strategy using a template or natural language. The system will convert it into a validated Strategy JSON DSL, calculate indicators, generate signals, execute historical backtests, analyze performance, explain risks, scan parameters, and produce a reproducible research report.

```text
Natural-language or template strategy
            ↓
Validated Strategy JSON DSL
            ↓
Indicators → Signals → Backtest
            ↓
Performance and risk analysis
            ↓
Agent timeline and research report
```

## Important disclaimer

> **Educational and research use only.** Historical backtesting estimates how a strategy would have behaved on selected historical data. It does not guarantee future results. This application does not provide financial, investment, tax, or legal advice.

## Technology choices

### Frontend

- HTML5 and CSS
- Vanilla JavaScript with ES modules
- native DOM APIs and Fetch API
- Vite as the development server and production build tool
- ESLint and Node's built-in test runner

### Backend

- Python 3.11+
- FastAPI and Uvicorn
- Pydantic Settings
- Pytest and Starlette TestClient (HTTPX2 transport)
- Ruff for linting and formatting

### Planned quantitative stack

- pandas and NumPy
- backtesting.py for the first backtest engine
- vectorbt for high-volume parameter scanning later
- SQLite, DuckDB, and Parquet where each is appropriate
- optional local LLM integration through a constrained Strategy JSON DSL

## Requirements

- Linux or another Unix-like environment
- Python 3.11 or newer
- Node.js 20.19+ or 22.12+
- npm
- Git
- Optional: Docker Engine with Docker Compose

## Quick start on Linux

```bash
cp .env.example .env
./scripts/bootstrap.sh
./scripts/dev.sh
```

Then open:

- Frontend: `http://127.0.0.1:5173`
- Backend root: `http://127.0.0.1:8000`
- Swagger UI: `http://127.0.0.1:8000/docs`
- ReDoc: `http://127.0.0.1:8000/redoc`
- Health endpoint: `http://127.0.0.1:8000/api/v1/health`

Stop both development servers with `Ctrl+C`.

## Manual setup

### Backend

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r backend/requirements-dev.txt
python -m uvicorn app.main:app --app-dir backend --reload
```

### Frontend

```bash
cd frontend
npm ci
npm run dev
```

## Quality checks

```bash
make check
```

This runs:

1. Ruff linting for Python;
2. ESLint for JavaScript;
3. backend API tests;
4. frontend unit tests;
5. a production frontend build.

Individual commands are available through `make help`.

## Current API

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/` | Human-readable backend metadata |
| `GET` | `/api/v1/health` | Liveness and application identity |
| `GET` | `/api/v1/system/info` | Phase and capability information |

The API is versioned from the first commit so future quantitative endpoints can evolve without breaking the frontend unexpectedly.

## Repository structure

```text
quant-strategy-agent-lab/
├── backend/                 FastAPI application and backend tests
├── frontend/                Modular Vanilla JavaScript application
├── docs/                    Technical and product documentation
├── scripts/                 Linux workflow scripts
├── docker-compose.yml       Container orchestration
├── Makefile                 Common development commands
└── README.md
```

See [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) for module boundaries and [`docs/ROADMAP.md`](docs/ROADMAP.md) for the implementation sequence.

## Engineering rules

- Domain logic must not be placed directly inside API route handlers or DOM event handlers.
- The frontend may depend on services and core modules; services must not depend on page modules.
- The backend will validate every Strategy JSON payload before execution.
- An LLM will never be allowed to execute arbitrary generated Python code.
- Backtests must record data range, costs, assumptions, parameters, and engine version.
- Every financial metric added later must include a documented formula and test case.

## Docker Compose

```bash
docker compose up --build
```

The containerized frontend is available at `http://localhost:8080` and proxies `/api` requests to the backend container.

## Documentation index

- [Project specification](docs/PROJECT_SPEC.md)
- [Architecture](docs/ARCHITECTURE.md)
- [Frontend architecture](docs/FRONTEND_ARCHITECTURE.md)
- [API specification](docs/API_SPEC.md)
- [Strategy DSL contract](docs/STRATEGY_DSL.md)
- [Backtest engine design](docs/BACKTEST_ENGINE.md)
- [Agent workflow](docs/AGENT_WORKFLOW.md)
- [Data pipeline](docs/DATA_PIPELINE.md)
- [Linux development workflow](docs/DEVELOPMENT.md)
- [Roadmap](docs/ROADMAP.md)
- [Architecture decisions](docs/DECISIONS.md)
- [Phase 0 acceptance record](docs/PHASE_0_ACCEPTANCE.md)

## License and contribution status

This is currently a portfolio and learning project. A public license can be selected before publishing the repository.
