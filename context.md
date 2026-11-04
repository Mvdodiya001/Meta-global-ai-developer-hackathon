# ClauseTrace — context through 2026-11-02 19:07 IST

One handoff for the next session. HEAD is `cc6ff47` on `main`. The OpenAPI
contract is **v12** (37 paths). The production rewrite (P0–P5, `docs/rewrite/`)
is complete **in the working tree and not yet committed** (~60 entries: modules,
tests, rewrite docs, README/docs refresh). Agents never commit; the owner does.

A proof is conditional on accepted premises and a stated source version. The
product does not assert that the law is true and it is not legal advice. Demo
data is fictional. Simulated amendments are labelled.

## What it is

ClauseTrace is a version-aware legal verification engine (Meta Global AI
Developer Hackathon). A lawyer asks whether a contract clause meets a legal
requirement. Muse Spark may call exactly six tools and draft a structured
proof. A deterministic checker (no model) validates the proof, and a
propositional-logic module decides entailment for what-if and conflict checks.
Only the memory service sets a finding's status: FOLLOWS, RULED_OUT, UNKNOWN,
REQUIRES_REVIEW, or CONFLICTING. Old findings are never overwritten. When a
legal source is amended, graph traversal finds the findings that depended on
it, marks them stale, and a re-check writes a new finding. Every query is
scoped by `matter_id` (`MAT-01` in the demo, `tenant_id` default `demo`).

Demo domain: India's DPDP Act 2023 / DPDP Rules 2025, a commencement
notification, and a decoy statute, applied to a fictional Acme Retail–Nimbus
Analytics data-processing agreement (12 clauses), plus a fictional
Beacon–Stratus variant used to prove the upload pipeline.

## Stack and layout

- **Backend:** Python 3.12, FastAPI, SQLAlchemy 2. `make check-backend` =
  ruff + mypy + pytest. Modular monolith under `backend/app/modules/` with
  enforced boundaries (tests): `verification` (agent loop, tools, memory —
  the only status decider), `law` (sources, rule cards, diff), `impact`
  (impact, re-verify, counterfactual), `intake` (extract, scan, transcribe,
  pdf, jobs), `evidence` (graph, premises, FalkorDB projection), `matters`
  (seed), `identity` (tenancy). Old `app/services/*` and
  `app/agent/{extract,scan,transcribe}` paths are typed compatibility
  re-exports. Domain events (`app/core/events.py`): `finding.decided`,
  `fact.approved/challenged/rejected/corrected`, `impact.applied`.
- **Checker:** `backend/checker/` (verify + proplogic). No model, no network,
  no `app.agent` imports (AST-enforced).
- **Data:** SQLite (WAL, NullPool) is the demo/default store. The same models
  run on PostgreSQL via `CLAUSETRACE_DB_URL`; `scripts/migrate_sqlite_to_postgres.py`
  copies a seeded SQLite DB with full parity (verified). The evidence graph is
  projected to **FalkorDB** (`app/modules/evidence/graph_projection.py`,
  rebuildable, parity-tested). Drivers are the optional `prod` extra
  (psycopg, falkordb, pypdf); the demo needs none.
- **Frontend:** React 18 + Vite + TypeScript + Tailwind, generated types from
  the contract (`npm run gen:api`). Routes: `/` (Your matters),
  `/review` (Review a clause), `/impact` (Law changes), `/control` (Your
  control room), `/evidence/:findingId`, `/admin` (internal overview).
- **Models (Meta only):** `muse-spark-1.3-contributor` (extraction, claims,
  loop, scans), `muse-spark-1.2` (challenger), `muse-voice-transcribe-1.0`
  (dictation, ASR endpoint — not the Responses gateway). Gateway modes
  live/replay/mock; replay is the default and what CI/demo use; tests never
  call live. Per-tenant spend is metered in `llm_calls` with an optional
  `CT_TENANT_BUDGET_USD` cap enforced at the live loop entry.
- **Eval gate:** `scripts/run_evals.py` runs `corpus/evals/golden.json`
  (5 cases) — verdict agreement + premise-admission violations; exit code
  gates releases. Currently **5/5, 0 violations**.

## Contract history (additive after v1)

| Version | What was added |
|---------|----------------|
| v0–v2 | Stub examples → real router → ask loop returns the finding |
| v3 | Proof-step fields round-trip |
| v4 | `GET /` and `GET /health` |
| v5 | Real counterfactual; `GET /api/reverify-list` |
| v6 | Status value `CONFLICTING` |
| v7 | `POST /api/scans` (PNG/JPEG base64 JSON) |
| v8 | `POST /api/dictations` (WAV base64); fact is `ai_inferred` until approved |
| v9 | Lawyer display labels beside machine fields |
| v10 | Reverify `skipped` list (F1) |
| v11 | Document upload + intake jobs + fact correction (P3) |
| v12 | `GET /api/admin/overview` (P5) |

`openapi/openapi.v11-draft.json` + `openapi/FREEZE.md` record the freeze/
promotion discipline used during the rewrite.

## Status (2026-11-02 evening)

| Item | State |
|------|-------|
| Hackathon features T0–T6, T7.1–T7.4, T8.1 | Done. T7.5 (open weights) not started. |
| Finish list | F1 (every stale row re-checks; proof-less rows reported as `skipped`), F2 ("Already confirmed"; illustration labels on the two remaining local-sample cards), F3 (real server UNKNOWN) done. F4 done by owner (`704f865`). F5 deploy, F6/F7 submission flow remain. |
| Rewrite P0–P5 | Done and gated: boundaries + events, tenancy schema, Postgres migration parity, FalkorDB projection parity, service split, async intake (jobs, PDF, correction), matters/evidence/admin pages, eval gate, budgets, runbooks (`docs/rewrite/01–09`). |
| Last checks | Backend **264 passed + 2 infra-gated skips** (ruff/mypy clean); frontend **39/39** + production build; eval gate exit 0. |
| Servers / DB | Both stopped. Demo DB was reset clean after the last live verification. Reset again before any demo/recording. |
| Credit spend | ≈ $0.89 logged lifetime, plus ≈ $0.01 across the T7/F3/P3 record runs (each a single approved `make record`). Cap $150. |

## Demo that works on replay

```text
make reset-demo
API_STUB=0 LLM_MODE=replay DEMO_MODE=1 CHALLENGER=on \
  backend/.venv/bin/uvicorn app.main:app --app-dir backend --port 8000
cd frontend && npm run dev   # http://127.0.0.1:5173
```

Order: reset → ask the 9.2 question (as-of 2026-11-20) **before** approving
any fact → Law changes (preview, apply v2-simulated, re-check) → only then
approve/challenge/correct facts, scan, or dictate. Approving inserts a new
premise row, which changes the recorded Ask hash; the next Ask needs a new
reset (the reset is safe while the server runs — NullPool). Known honest
outcomes: re-checked s8(6) answers become "Needs your review" (old proofs
cited replaced text); the 2025-10-17 ask with `CHALLENGER=on` also lands
there (no challenger cassette for that date).

## Honest leftovers

- The as-of card and the post-challenge card on the control-room page are
  still browser-side illustrations, now labelled "Illustration, not a server
  answer". Everything else there (approve, challenge, correct, scan,
  dictation, wording re-check, uncovered question) calls the real API.
- Auth is schema-ready (`tenants`, `tenant_id` everywhere) but not enforced;
  the app runs as the single demo tenant. Admin overview has no auth yet.
- Rule cards stay `ai_inferred` (no lawyer has reviewed them); card topic
  names still differ from the ARCHITECTURE CT1–CT4 mapping.
- Backend default remains `API_STUB=1`; the demo must set `API_STUB=0`.
  No CORS; the Vite proxy is the demo path. No Compose file in-repo yet.
- `docs/logs/*` lag the rewrite (owner waived per-task logging for the
  P0–P5 work; `docs/rewrite/08-execution-roadmap.md` carries the evidence).
- `SHOWDOWN.md` (the major-update plan) lives outside the repo at
  `/home/shiv/.opencode/plan/showdown.md`; decisions D0–D6: hackathon first,
  then SHOWDOWN — the P0–P5 rewrite was executed early **at the owner's
  direction**, so on submission the owner must keep the submitted state
  identifiable (tag the submitted commit; do not blur what was built when).

## Invariants that must stay

1. `backend/checker/` imports nothing from `app.agent`; no network, no model.
2. Append-only tables stay append-only (`findings`, `source_versions`,
   `provisions`, `audit_log`).
3. The model gets exactly six tools. No web search, no shell.
4. Only the memory service (`app.modules.verification.memory`) sets status.
5. Proof premises are `lawyer_confirmed` or `document_extracted`, never
   `ai_inferred` or `disputed`.
6. Every citation is `(source_version_id, provision_id, span, sha256)` and
   quotes match the stored snapshot verbatim.
7. A stale finding is replaced only after a fresh `lookup_source` of the
   current version in the same run.
8. Simulated amendments stay `is_simulated=true` with a SIMULATED badge.
9. Every screen keeps the disclaimer; unreviewed output stays
   "AI draft — not yet reviewed". Lawyer UI shows no ids, hashes, or JSON.
10. Every query is scoped by matter (and tenant, default `demo`).

## Next session

1. Owner: commit the working tree by lane (backend, frontend, docs) — the
   rewrite is uncommitted. Then F5 deploy (split hosting per DECISIONS:
   Oracle VM backend + Vercel frontend) and the submission flow.
2. Do not start pilot/SHOWDOWN-beyond-rewrite work until the §12 decisions
   (design partners, client-document data terms, practising-lawyer review)
   are acted on — fictional/redacted documents only until Meta's API data
   terms are confirmed in writing.
3. `make reset-demo` before any demo or recording; `make record` at most
   once per task and only when a cassette hash actually breaks.
