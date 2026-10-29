# ClauseTrace

Version-aware legal verification for contract clauses (Meta Global AI Developer Hackathon).

## Stack

- **Backend:** Python 3.12, FastAPI, SQLite (port `8000`)
- **Frontend:** React 18, Vite, TypeScript, Tailwind (port `5173`)

## Setup

```bash
make setup
```

Copy `.env.example` to `.env` and set secrets before running the backend with live LLM mode.

## Development

Run backend and frontend in separate terminals:

```bash
cd backend && .venv/bin/uvicorn app.main:app --port 8000 --reload
cd frontend && npm run dev
```

Or see `make dev` for the same commands.

## Checks

- Backend (Muse Code lane): `make check-backend`
- Frontend (Cursor lane): `make check-frontend`
- Full suite (human): `make check`

## Agent workflow

See `AGENTS.md`, `PLAN.md`, and `docs/TASKS.md`. Agents log work in `docs/logs/` and do not commit; use `git hc` for human commits after review.
