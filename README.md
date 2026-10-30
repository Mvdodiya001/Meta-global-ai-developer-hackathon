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

Run backend and frontend in separate terminals. The demo path uses the **real v1 API** in replay mode, not bundled `openapi/examples` mocks.

```bash
make reset-demo
cd backend && API_STUB=0 LLM_MODE=replay DEMO_MODE=1 .venv/bin/uvicorn app.main:app --port 8000 --reload
cd frontend && npm run dev
```

Vite proxies `/api` to `http://127.0.0.1:8000`. Override with `VITE_API_BASE` if the UI is not served from the Vite dev server. Unit tests still use example mocks (`MODE=test` or `VITE_USE_MOCKS=1`).

Or see `make dev` for the two-terminal commands without the demo env flags.

## Checks

- Backend (Muse Code lane): `make check-backend`
- Frontend (Cursor lane): `make check-frontend`
- Full suite (human): `make check`

## Models

- **Muse Spark (`muse-spark-1.3`)** drafts claims, extractions, and proofs. It may call only six tools (`lookup_source`, `list_dependent_claims`, `get_premise`, `verify_derivation`, `propose_finding`, `request_lawyer_review`).
- **Muse Spark (`muse-spark-1.2`)** is used only as the **challenger**: a second pass with a different prompt that returns structured objections. A blocking objection forces `REQUIRES_REVIEW`. This pass is a reviewer, not independent verification; the checker has no model in it.

Enable the challenger with `CHALLENGER=on` (default `off`). Provider switch: `CHALLENGER_PROVIDER=meta`. Turn it off with `CHALLENGER=off`. Open-weights swap (`CHALLENGER_PROVIDER=openweights`) is optional later and is not wired yet.

The UI Challenger panel on clause review and lawyer control shows these objections. It does not assert that the law or premises are true, and it is not legal advice.

## Agent workflow

See `AGENTS.md`, `PLAN.md`, and `docs/TASKS.md`. Agents log work in `docs/logs/` and do not commit; use `git hc` for human commits after review.
