# MUSE_CODE_LOG.md — written ONLY by Muse Code (append-only)

Muse Code: you never commit and never add co-author or "Generated with" text. Log every task here. The human reads this to track your work and decides what to commit.
Time: `TZ=Asia/Kolkata date '+%Y-%m-%d %H:%M IST'`. Heading format must stay greppable: `## [T2.1] DONE · <YYYY-MM-DD HH:MM IST>`.
Status words: STARTED · DONE · PARTIAL · BLOCKED. Special tags in entries: `[CONTRACT vN → vN+1]`, `[REQ → H]`, `[REQ → CU]`, `[CONFLICT]`.

## Entry template (copy for each STARTED and final entry)
```
## [Txx.x] STARTED|DONE|PARTIAL|BLOCKED · <time>
- Task: <title>
- Files changed: <path (new|modified|deleted)>, ...
- What changed: <2–4 lines>
- Checks run: `make check-backend` → pass|fail (<counts or error>)
- Decisions / assumptions: <or none>
- Contract change: none | [CONTRACT vN → vN+1] <what>
- Requests: [REQ → H] ... | [REQ → CU] ... | none
- New-work note: <component built, date>
- Third-party added: <name version licence> | none
- Credit spend: <tokens / $> | none
- Ready for human commit: yes|no — suggested message: `Txx.x: <plain message, no trailers>`
```

---
## Log (newest at the bottom)
_(no entries yet)_

## [T0.4] STARTED · 2026-10-29 08:48 IST
- Task: Scaffold and CI (backend lane)
- Scope: `backend/` FastAPI scaffold with `/api/health`, `backend/tests/test_health.py`, Makefile verification, GitHub Actions CI workflow

## [T0.4] DONE · 2026-10-29 08:50 IST
- Task: Scaffold and CI (backend lane)
- Files changed: `backend/pyproject.toml` (new), `backend/app/__init__.py` (new), `backend/app/main.py` (new), `backend/tests/test_health.py` (new), `.github/workflows/ci.yml` (new), `docs/logs/MUSE_CODE_LOG.md` (modified); `Makefile` unchanged (starter targets already work); `backend/.venv/` created locally (gitignored, not committed)
- What changed: Minimal FastAPI app exposing `GET /api/health` → `{"status": "ok"}` (DATA_MODEL_API §7). Test written first (`test_health_returns_ok` via TestClient). `pyproject.toml` pins Python >=3.12 with fastapi/sqlalchemy/uvicorn plus a `dev` extra (pytest, httpx, ruff, mypy) matching the `make setup` / `check-backend` flow. CI runs `make check-backend` (Python 3.12) and `make check-frontend` (Node 22) on push/PR.
- Checks run: `make check-backend` → pass (ruff clean; mypy no issues in 3 files; pytest 1/1 passed); `make check-frontend` → pass, read-only re-run (oxlint clean on 9 files; vitest 1/1). CI workflow not executed (no runner here); YAML inspected only.
- Decisions / assumptions: Kept scaffold minimal for T0.4 — no `app/agent/llm.py`, `corpus/`, or `openapi/` (those belong to T0.7/T2.1). `.venv` lives at `backend/.venv` as the Makefile expects. One deprecation warning from `fastapi.testclient`/httpx is upstream noise, not a failure.
- Contract change: none (contract v0 lands in T0.7)
- Requests: [REQ → H] `.github/` is outside the lane list in AGENTS.md §4 but T0.4 explicitly requires GitHub Actions, so I added `.github/workflows/ci.yml` — please confirm placement or move it. Observation (no action): `.env.example` from T0.1 is absent from the repo root.
- New-work note: backend scaffold 2026-10-29
- Third-party added: fastapi 0.162.0 MIT · uvicorn 0.54.0 BSD-3 · sqlalchemy 2.1.6 MIT · pytest 9.2.0 MIT · httpx 0.28.1 BSD-3 · ruff 0.17.3 MIT · mypy 2.4.1 MIT (all via `backend` `dev` extra)
- Credit spend: none (no model calls; only local pip install)
- Ready for human commit: yes — suggested message: `T0.4: scaffold backend with FastAPI health check and CI`

## [T0.7] STARTED · 2026-10-29 09:13 IST
- Task: Contract v0 + stub mode
- Scope: `openapi/openapi.json` (v0), `openapi/examples/*.json`, Pydantic response models for every DATA_MODEL_API §7 endpoint, `API_STUB=1` mode returning the examples

## [T0.7] DONE · 2026-10-29 09:17 IST
- Task: Contract v0 + stub mode
- [CONTRACT v0] initial contract: all DATA_MODEL_API §7 paths with Pydantic response models; stub payloads in `openapi/examples/`
- Files changed: `backend/app/schemas.py` (new, ~30 response models), `backend/app/stub.py` (new, stub router serving examples), `backend/app/main.py` (modified: `version="v0"`, mount stub when `API_STUB=1` default), `backend/tests/test_contract_v0.py` (new, 30 tests), `openapi/openapi.json` (new, generated, `info.version v0`, 28 paths), `openapi/examples/*.json` (new, 26 payloads), `scripts/export_openapi.py` (new), `docs/logs/MUSE_CODE_LOG.md` (modified)
- What changed: Every §7 endpoint has a Pydantic response model and a stub handler returning its example file verbatim (ids accepted but ignored in stub). `POST /demo/*` returns 403 unless `DEMO_MODE=1`. `scripts/export_openapi.py` regenerates the contract from the app. Path params use `{id}` to match §7 literally.
- Checks run: `make check-backend` → pass (ruff clean; mypy clean on 6 files; pytest 30/30). Live: `curl localhost:8001/api/health` → `{"status":"ok"}` and `curl localhost:8001/api/claims/C-001/current` → finding FND-001 (port 8001: 8000 is held by an unrelated root process `memopops.api`, not touched). Test server stopped afterwards. CI workflow not executed (no runner); YAML unchanged from T0.4.
- Decisions / assumptions: Stub on by default (`API_STUB=1`) until T4.5 replaces handlers; paths stay identical. Provision texts are marked `[STUB — unverified illustrative text]` — real corpus lands in T1.2; no legal text asserted. Proof-step nulls written explicitly so examples equal responses exactly. `runs/{id}/events` returns JSON; SSE lands after v0. `finding.json`/`finding_current.json` share content; history/extract derived from them.
- Contract change: [CONTRACT v0] new contract, additive from here; Cursor should run `npm run gen:api` against it
- Requests: [REQ → CU] run `npm run gen:api` now that `[CONTRACT v0]` is landed. [REQ → H] confirm demo error shape `{"error": {...}}` is acceptable for CU's client. Note: `PROGRESS.md`/`HUMAN_LOG.md` show concurrent human edits — outside my lane, no [CONFLICT].
- New-work note: contract v0 + stub mode 2026-10-29
- Third-party added: none (fastapi/pytest stack from T0.4)
- Credit spend: none (no model calls)
- Ready for human commit: yes — suggested message: `T0.7: add contract v0 with stub mode and examples`
