# AGENTS.md — ClauseTrace

Rules for every AI coding agent (Cursor, Muse Code) in this repo. Read it with `PLAN.md`.
**Session start:** read this file, `PLAN.md`, `docs/TASKS.md`, your own log in `docs/logs/`, and (read-only) the other agent's log. Do ONLY the task you were given.
**Session end:** append your final log entry, run your lane check. **Do not commit.**

## 1. Project (one paragraph)
ClauseTrace is a version-aware legal verification engine, built for the Meta Global AI Developer Hackathon (solo build: 8 days plus a buffer day). A lawyer asks whether a contract clause meets a legal requirement. Muse Spark calls six bounded tools and drafts a structured proof. A deterministic checker (no model) validates the proof. The memory service records the finding as FOLLOWS / RULED_OUT / UNKNOWN / REQUIRES_REVIEW. When a legal source is amended, graph traversal finds the findings that depended on it, marks them stale, and forces the agent to re-query. Old findings are never overwritten. A proof is conditional on accepted premises; it never claims the law is true. Demo domain: India's DPDP Act 2023 / DPDP Rules 2025 applied to a fictional data-processing agreement.

## 2. Stack and commands
- Backend: Python 3.12, FastAPI, SQLAlchemy 2, SQLite (WAL), pytest, ruff, mypy.
- Frontend: React 18 + Vite + TypeScript, Tailwind, React Flow (graph), Vitest.
- Models: Meta Model API only (`https://api.meta.ai/v1`, Responses API, Muse Spark). Open weights (Muse Spark Open on a partner host) is optional and added only if the human starts task T7.5.
- Commands: `make setup` · `make dev` · `make check-backend` · `make check-frontend` · `make seed` · `make reset-demo` · `make status` · `make record` (refreshes LLM cassettes; spends credits).
- Muse Code runs `check-backend`; Cursor runs `check-frontend`. Only the human runs the full `make check`.

## 3. Layout
```
AGENTS.md PLAN.md PROGRESS.md NEW_WORK.md NOTICE.md README.md Makefile
docs/        PRD, ARCHITECTURE, DATA_MODEL_API, TASKS, DEMO_AND_SUBMISSION
docs/logs/   MUSE_CODE_LOG.md  CURSOR_LOG.md  HUMAN_LOG.md
backend/app/ api/ core/ models/ services/ (sources, impact, memory, audit) agent/ (llm, tools, loop, prompts)
backend/checker/   deterministic proof checker (NO imports from app.agent or any LLM client)
corpus/      raw/ rulecards/ contracts/ cassettes/        backend/tests/
frontend/src/ pages/ components/ api/        openapi/ openapi.json + examples/
scripts/     seed_demo.py reset_demo.sh record_cassettes.py git-hooks/
```

## 4. Ownership — two tools run at the same time, never on the same file
- **Muse Code owns:** `backend/**`, `corpus/**`, `scripts/**`, `openapi/**`, `Makefile`, `docs/logs/MUSE_CODE_LOG.md`.
- **Cursor owns:** `frontend/**`, `README.md`, `docs/logs/CURSOR_LOG.md`. Cursor never calls models and never opens the database; it uses the API (`API_STUB=1` or mocks).
- **Human only:** `docs/**` (except the two agent logs), `AGENTS.md`, `PLAN.md`, `PROGRESS.md`, `NEW_WORK.md`, `NOTICE.md`, `docs/logs/HUMAN_LOG.md`, `.git/`.
- Need something outside your files? Write `[REQ → H]` or `[REQ → CU]`/`[REQ → MC]` in your log and stop that part. Never edit it yourself.
- Contract: source of truth is `openapi/openapi.json` + `openapi/examples/`. After SP1 only additive changes; breaking changes need human approval. Log every change as `[CONTRACT vN → vN+1]`. Cursor regenerates types when the version moves.
- Ports: backend 8000, frontend 5173. If you see changes in your lane that you did not make, stop and log `[CONFLICT]`.

## 5. Git: agents are READ-ONLY. Agents never commit.
- **Allowed:** `git status`, `git diff`, `git log`, `git show`, `git blame`.
- **Forbidden, always:** `git add`, `commit` (including `--amend`), `push`, `pull`, `fetch`, `merge`, `rebase`, `reset`, `checkout`, `switch`, `restore`, `branch`, `tag`, `stash`, `cherry-pick`, `clean`, `worktree`, `config`, `gh pr …`, and any editor button or setting that stages, commits, or pushes.
- **No attribution anywhere:** no `Co-authored-by`, `Generated with`, `Signed-off-by`, robot emoji, or "written by Cursor / Muse Code / AI" text in commits, files, comments, docs, or PR text. Tool disclosure in the README is written by the human only.
- You may *suggest* a commit message in your log. Messages are plain: `T2.1: add LLM gateway with replay mode`.
- The human commits per lane. Hooks in `scripts/git-hooks/` block agent commits, but the rule is what you must follow.

## 6. Logging — mandatory, so the human can track everything
- Write only to your own log. Append-only; never rewrite old entries.
- Append `## [<task>] STARTED · <time>` when you begin and `## [<task>] DONE|PARTIAL|BLOCKED · <time>` when you finish. Time: `TZ=Asia/Kolkata date '+%Y-%m-%d %H:%M IST'`.
- Fields: files changed · what changed · checks run + result · decisions/assumptions · contract change · requests · new-work note · third-party added (name, version, licence) · credit spend · **ready for human commit (yes/no) + suggested message**.
- Log blockers, surprises, and anything you skipped. Never claim a check passed that you did not run.

## 7. Architecture invariants (non-negotiable)
1. `backend/checker/` imports nothing from `app.agent`, no network, no LLM client. Enforced by `tests/test_checker_isolation.py` (AST scan). Never weaken the checker to make a test pass.
2. `findings`, `source_versions`, `provisions`, `audit_log` are append-only (DB triggers). State changes are new rows in `finding_events`.
3. The model may call exactly six tools (`lookup_source`, `list_dependent_claims`, `get_premise`, `verify_derivation`, `propose_finding`, `request_lawyer_review`). No web search, no shell, no extras. Changing the list needs human approval.
4. Only `services/memory.py` decides a finding's status. No path lets LLM output set a status.
5. Proof premises must be trust class `lawyer_confirmed` or `document_extracted`; never `ai_inferred` or `disputed`.
6. Every citation is `(source_version_id, provision_id, span, sha256)`; quotes match the stored snapshot verbatim.
7. A stale finding is replaced only by a new finding whose tool log shows a fresh `lookup_source` of the current version.
8. Simulated amendments carry `is_simulated=true` and a SIMULATED badge in the UI.
9. Every screen shows the disclaimer banner; unreviewed output shows "AI draft — not yet reviewed".
10. Every query is scoped by `matter_id`.

## 8. LLM and credit rules ($150 total) — Muse Code only
- Use only the Meta Model API. Do not integrate Baseten, Modal, Fireworks or any open-weights host unless the human assigns T7.5.
- All model calls go through `app/agent/llm.py`; it logs model, tokens, latency, cost estimate to `llm_calls`.
- `LLM_MODE=live|replay|mock`, default `replay`. Tests never use `live`.
- Temperature 0 for extraction and proofs. Max 12 tool calls per run, max 2 retries. Cache by request hash in `.cache/llm/`; demo cassettes live in `corpus/cassettes/`.
- Run `make record` at most once per task. Log spend each time; stop and log `[REQ → H]` if the daily budget in `PROGRESS.md` is exceeded.

## 9. Code conventions
- Python: type hints, `ruff format`, small functions, docstrings name the requirement ID (e.g. `F6`). Typed exceptions (`SourceUnavailable`, `ProofRejected`); never swallow errors.
- Tests first for `checker/` and `services/impact.py`; every bug gets a regression test.
- TypeScript: strict, no `any`, components under 150 lines, accessible labels, status shown by text/icon plus color, light and dark safe.
- Dates: UTC ISO-8601 for timestamps; plain dates for legal dates.

## 10. Never
- Never change the DB schema, API contract (breaking), or tool list without approval.
- Never add a dependency without asking (log `[REQ → H]`). Never commit or print secrets (`.env` is git-ignored; keep `.env.example`).
- Never work outside the current task or refactor unrelated files.
- Never use real client or personal data; demo data is fictional. No political, war, or medical content in demo data or copy.
- Never add legal text from paid or unclear-rights sources; list each source in your log so the human can record it in `NOTICE.md`.
- Never write UI or README text saying the system proves the law is true or gives legal advice.
- Never give the model browsing, shell, or file tools.

## 11. Always
- Run your lane check before DONE. Write tests first where the task says so.
- Put new-work notes and third-party additions in your log; the human copies them to `NEW_WORK.md` and `NOTICE.md`.
- Ask (via `[REQ → H]`) when a requirement is ambiguous instead of guessing.

## 12. Pointers
`PLAN.md` (who/what order/how) · `PROMPT.md` (the one prompt) · `docs/PRD.md` (what/why) · `docs/ARCHITECTURE.md` (how) · `docs/DATA_MODEL_API.md` (tables, tools, endpoints) · `docs/TASKS.md` (task list) · `docs/DEMO_AND_SUBMISSION.md` (video, README, checklist). The one prompt to paste: `PROMPT.md`.
