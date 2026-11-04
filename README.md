# ClauseTrace

When a law changes, ClauseTrace finds which legal conclusions depended on it, re-checks only those, and shows exactly why each follows — or why it can't be established.

A version-aware legal verification engine, started at the Meta Global AI Developer Hackathon. Demo domain: India's DPDP Act 2023 / DPDP Rules 2025 applied to a fictional data-processing agreement (Acme Retail / Nimbus Analytics).

ClauseTrace shows what follows from accepted premises and stated source versions. It does not assert that the law or premises are true, and it is not legal advice.

**3-minute demo video:** not uploaded yet.

## Why it's different

- **A dependency graph says what to re-check.** When a source version changes, reverse traversal marks only the findings that actually depended on the changed provision. An unrelated decoy source flags none.
- **An independent checker validates proofs.** The checker is a separate Python package with no model and no network. It never imports the agent. Muse Spark drafts; it cannot set a finding's status.
- **Validity is decided by propositional logic, deterministically.** Each proof is also checked as propositions (premises + inference rule ⊢ conclusion), which powers the what-if preview and the conflicting-interpretations state.
- **History is never overwritten.** Findings, source versions, provisions, and the audit log are append-only. A stale finding is replaced by a new row; the old one stays.

## What it does

- **Review a clause** — ask a question, get a checked answer with numbered reasoning, exact clause and section quotes, and the facts relied on (each labelled: confirmed by you / taken from the document / proposed, not yet approved).
- **Law changes** — preview a law change without saving anything (what-if), apply it, see only the affected answers move to a re-check queue, re-check them, and compare before/after answers.
- **Conflicting readings** — when two legal tests cited in one proof contradict each other, the answer is stored as "Two readings of the law conflict — your call", never silently resolved.
- **Your control room** — approve or challenge facts (approval mints a new confirmed copy; nothing is edited), correct fact wording, dictate a fact by voice or add a scanned page — both arrive as *proposed* facts that cannot support any answer until a lawyer approves them.
- **Evidence page** — every answer has a page with its reasoning, citations, facts, and earlier versions.
- Uploads run as tracked background jobs, including PDF files (text layer read directly; image-only pages transcribed).

## Architecture

Backend (Python 3.12, FastAPI) as a modular monolith with explicit domain boundaries (`backend/app/modules/`): **verification** (agent loop + memory, the only place a status is decided), **law** (sources, legal tests, diff), **impact** (amendment → stale → re-verify, what-if), **intake** (extraction, scans, dictation, PDF, jobs), **evidence** (facts, trust actions, graph), **matters**, **identity** (tenancy). The deterministic checker (`backend/checker/`, plus a propositional-logic module) is a pure library inside verification. Domain events (`finding.decided`, `fact.approved`, `impact.applied`) connect the modules.

Data: SQLite for the demo and local development; the same models run on PostgreSQL (`CLAUSETRACE_DB_URL`), with the evidence graph projected to FalkorDB as a rebuildable read model (parity-tested against the record). Contract: `openapi/openapi.json`, currently **v12**, additive-only, with lawyer display labels beside every machine field. Frontend: React 18 + Vite + TypeScript, generated API types.

Invariants: only the memory service decides FOLLOWS / RULED_OUT / UNKNOWN / REQUIRES_REVIEW / CONFLICTING. A stale finding is replaced only after a fresh `lookup_source` of the current version. Premises must be lawyer-confirmed or document-extracted; AI-inferred facts can never support a proof. Simulated amendments carry a SIMULATED badge.

## How Meta models are used

| Model | Used for | Bound |
|-------|----------|--------|
| Muse Spark (`muse-spark-1.3-contributor`) | Clause extraction, question → typed claim, six-tool proof loop, scanned-page transcription (image input) | Temperature 0; max 12 tool calls; replay cassettes in CI |
| Muse Spark (`muse-spark-1.2`) | Challenger only: a different prompt returning structured objections | Blocking objection → REQUIRES_REVIEW. Reviewer, not a second checker |
| Muse Voice Transcribe (`muse-voice-transcribe-1.0`) | Voice dictation → transcript → proposed fact | Stored `ai_inferred`; inadmissible until a lawyer approves it |
| Muse Spark Open | Not wired | Optional later (`CHALLENGER_PROVIDER=openweights`) |

Every model call goes through one gateway with per-tenant spend metering and an optional budget cap (`CT_TENANT_BUDGET_USD`). A golden-set evaluation harness (`scripts/run_evals.py`) gates releases: verdict agreement must be total and premise-admission violations zero. The UI Challenger panel **shows** a second-pass report only if the server was started with `CHALLENGER=on`.

## The six bounded tools

The model may call exactly these. No web search, no shell, no extra tools.

| Tool | Role |
|------|------|
| `lookup_source` | Provisions of a source at a version (default: valid on as-of). Max 5. |
| `list_dependent_claims` | Findings in this matter that depend on a source or provision. Max 20. |
| `get_premise` | One fact plus trust class and origin span. |
| `verify_derivation` | Run the deterministic checker on a draft proof. Read-only. |
| `propose_finding` | Propose a proof. The memory service re-checks it and sets status. The model cannot set status. |
| `request_lawyer_review` | Flag an item for a lawyer with a reason. |

Every query is scoped by `matter_id`. Cross-matter ids are rejected.

## What we built during the hackathon

See [`NEW_WORK.md`](NEW_WORK.md). The public repo started on Day 1 before application code; the first commit is docs and the licence. The production-grade rewrite that followed the demo (modular services, Postgres/graph data layer, intake pipelines, eval gate) is designed in [`docs/rewrite/`](docs/rewrite/).

## Honest limitations

- One fictional contract (plus a fictional variant for upload testing) and a small official DPDP corpus. No real client or personal data.
- Rule cards were written by the developer from official text. No lawyer has reviewed them; they stay `ai_inferred`.
- The simulated DPDP Act v2 amendment is labelled SIMULATED.
- Not legal advice. No compliance certification.
- Replay mode answers only recorded questions and as-of dates. Anything else needs `LLM_MODE=live` and a Meta API key.
- Auth/multi-tenant enforcement and the source-approval workflow are designed and schema-ready; the shipped demo runs as a single demo tenant.
- Open-weights challenger is not wired.

## Run (replay, no API key)

```bash
make setup
cp .env.example .env
make reset-demo
```

Two terminals:

```bash
# API — contract v13, replay
cd backend && set -a; [ -f ../.env ] && . ../.env; set +a
API_STUB=0 LLM_MODE=replay CHALLENGER=on \
  .venv/bin/uvicorn app.main:app --port 8000 --reload

cd frontend && npm run dev
```

You do **not** need `DEMO_MODE=1` for the app itself. That flag only enables
the scripted-demo helpers (`POST /api/demo/reset`, `POST /api/demo/scenario/*`).
Asking, law changes, approvals, scans, dictation, clause updates, and sign-in
all work without it. Sign-in is at `/signin`; account enforcement across the
API is opt-in with `CT_AUTH_REQUIRED=1` (off for the demo).

- UI: http://localhost:5173 · API: http://localhost:8000
- Vite proxies `/api` to `http://127.0.0.1:8000`.
- Always `make reset-demo` before a demo or `make record`. Approving a fact mints new rows and breaks cassette hashes.
- Screen 1 default question: `Does clause 9.2 require Nimbus to keep transfer logs?` Recorded as-of dates: **2026-11-20** (default) and **2025-10-17**.
- Run Screen 1 before Screen 3 (lawyer control uses that `claim_id`).
- UNKNOWN-typed questions store UNKNOWN without drafting a proof. If the challenger cassette is missing, the finding is kept as REQUIRES_REVIEW (not a 502).
- Backend image: `docker build -f backend/Dockerfile -t clausetrace-backend .` Compose file is not in-repo yet.
- Unit tests still use `openapi/examples` mocks (`MODE=test` or `VITE_USE_MOCKS=1`).
- Upload a document from the Your matters page (PDF, DOCX, or text). Text pages are read directly; scanned pages are transcribed and labelled per page so you can spot-check them on the clause page before relying on answers.
- Sign in from the nav. Dictate a fact on the Dictate page (microphone → transcript → save as proposed → confirm) or dictate new clause wording on the clause page; saving writes a new version and never edits history.

Live model calls: set `MODEL_API_KEY` in `.env`, `LLM_MODE=live`. Tests never use live.

## Checks

```bash
make check-frontend   # oxlint + vitest
make check-backend    # ruff, mypy, pytest
make check            # both (human)
```

Latest runs (2026-11-02): backend pytest **280 passed** (+2 infrastructure-gated skips for Postgres/FalkorDB parity), frontend vitest **44/44**, production build passes, eval gate **5/5 with 0 premise violations**. Contract is **v14**.

## Source provenance

Official DPDP Act 2023, DPDP Rules 2025, commencement notification G.S.R. 843(E), and the unrelated decoy (Emblems Act 1950) are listed with retrieval dates in [`NOTICE.md`](NOTICE.md). The Master DPA text and its Beacon/Stratus variant are fictional and written for this project.
