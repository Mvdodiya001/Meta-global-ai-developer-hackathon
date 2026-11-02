# ClauseTrace — context through 2026-11-02 17:18 IST

One handoff for the next session. HEAD is `e1c130b` on `main`, in sync with `origin/main`. The OpenAPI contract is **v9** (33 paths). `PROGRESS.md`, `docs/TASKS.md`, `NEW_WORK.md`, and `docs/logs/HUMAN_LOG.md` still stop at the Day 6 core gate and contract v4. This file is the later picture.

A proof is conditional on accepted premises and a stated source version. The product does not assert that the law is true and it is not legal advice. Demo data is fictional. Simulated amendments are labelled.

## What it is

ClauseTrace is a version-aware legal verification engine for the Meta Global AI Developer Hackathon. A lawyer asks whether a contract clause meets a legal requirement. Muse Spark may call exactly six tools and draft a structured proof. A deterministic checker (no model) validates the proof. Only `backend/app/services/memory.py` sets the finding status. Old findings are never overwritten. When a legal source is amended, graph traversal finds the findings that depended on it, marks them stale, and a re-check writes a new finding. Every query is scoped by `matter_id` (`MAT-01`).

Demo domain: India's DPDP Act 2023 / DPDP Rules 2025, plus a commencement notification and a decoy statute, applied to a fictional Acme Retail–Nimbus Analytics data-processing agreement (12 clauses).

## Why the tree is split this way

Two coding agents work at the same time and must not edit the same file. The backend lane owns `backend/`, `corpus/`, `scripts/`, `openapi/`, and `Makefile`. The frontend lane owns `frontend/` and `README.md`. The human owns the other docs and git. The checker sits outside `backend/app` so a proof can be validated with no model and no network. The OpenAPI file is the contract both sides share: the server implements it, and the site generates TypeScript from it. Recorded model answers live in `corpus/cassettes/` so the demo can be replayed without spending credits.

Paths below are the tracked files at `e1c130b`, plus `context.md` (this file, not yet committed). Caches, `backend/.venv`, `frontend/node_modules`, `frontend/dist`, and `backend/db.sqlite3` are local runtime files and are not part of the product.

## Repository

### Root

| File | Why it exists |
|------|----------------|
| `LICENSE` | MIT (or Apache) licence required before any code, so the repo can be public. |
| `README.md` | How to run the demo and what the product claims. Frontend lane. Still thinner than the submission sales document. |
| `AGENTS.md` | Rules for both coding agents: lanes, invariants, logging, no commits. |
| `PLAN.md` | Who builds what, in what order, and the sync points. |
| `PROMPT.md` | The single prompt pasted to start an agent session. |
| `PROGRESS.md` | Human status board. Still says contract v4 and "do not start T7". Use this file for the later picture. |
| `NEW_WORK.md` | Judge-facing list of what was built during the hackathon, with commit ranges. Stops at the Dockerfile. |
| `NOTICE.md` | Sources and third-party licences. Official legal texts and library versions go here. |
| `context.md` | This handoff: status, the lawyer walk, and this tree. |
| `Makefile` | `setup`, `dev`, `check-backend`, `check-frontend`, `check`, `seed`, `reset-demo`, `record`, `status`, `hooks`. |
| `env.example` | Env template (`API_STUB`, `LLM_MODE`, `DEMO_MODE`, `CHALLENGER`, Meta key name). Named without a leading dot. `.env` is gitignored. |
| `.gitignore` | Ignores `.env`, `db.sqlite3`, `node_modules`, caches. Does not ignore `db.sqlite3-wal` / `db.sqlite3-shm`. Do not `git add` those. |

### `.github/`

| File | Why it exists |
|------|----------------|
| `workflows/ci.yml` | GitHub Actions runs the backend and frontend lane checks on push. |

### `docs/`

The design the code was built from. Agents do not edit these except their own log.

| File | Why it exists |
|------|----------------|
| `PRD.md` | What the product is and why: the lawyer question, the four statuses, the demo domain. |
| `ARCHITECTURE.md` | How a run moves from question to tools to checker to memory to graph. |
| `DATA_MODEL_API.md` | Tables, the six tools, and the HTTP endpoints. Source for the contract. |
| `TASKS.md` | Task list T0–T9 with owners and done-when lines. T7 checkboxes are still open even though T7.1–T7.4 are in the code. |
| `DEMO_AND_SUBMISSION.md` | Video script, README shape, judge prompt, submit checklist. |
| `logs/MUSE_CODE_LOG.md` | Append-only backend-lane log. |
| `logs/CURSOR_LOG.md` | Append-only frontend-lane log. |
| `logs/HUMAN_LOG.md` | Human commits and decisions. Stops at `59025a7`. |
| `logs/meta_usage.jsonl` | Token and cost lines from model calls. |

### `openapi/`

The contract. After the first stable version, changes are additive. Breaking changes need the human.

| File | Why it exists |
|------|----------------|
| `openapi.json` | Contract v9, 33 paths. Regenerated from the FastAPI app. |
| `examples/health.json` | Stub body for the health check. |
| `examples/matter.json` | Stub matter `MAT-01`. |
| `examples/documents.json` | Stub document list. |
| `examples/clauses.json` | Stub clause list for the DPA. |
| `examples/extract_result.json` | Stub extraction result. |
| `examples/facts.json` | Stub facts with trust classes. |
| `examples/fact_action.json` | Stub approve/challenge result. |
| `examples/claim_created.json` | Stub `POST /api/claims` response. |
| `examples/finding.json` | Stub finding with proof. |
| `examples/finding_current.json` | Stub current finding for a claim. |
| `examples/finding_history.json` | Stub finding history (old rows kept). |
| `examples/sources.json` | Stub legal-source list. |
| `examples/source_versions.json` | Stub versions, including the simulated one. |
| `examples/diff.json` | Stub provision diff. |
| `examples/ingest_result.json` | Stub ingest result. |
| `examples/impact.json` | Stub impact report. |
| `examples/graph.json` | Stub dependency graph. |
| `examples/audit.json` | Stub audit rows. |
| `examples/run.json` | Stub agent run. |
| `examples/run_events.json` | Stub tool-trace events. |
| `examples/proofs_verify.json` | Stub proof-verify result. |
| `examples/reverify_result.json` | Stub re-check result. |
| `examples/review_result.json` | Stub lawyer-review result. |
| `examples/counterfactual.json` | Stub what-if result. |
| `examples/demo_scenario.json` | Named demo scenario for the stub. |
| `examples/demo_reset.json` | Stub reset acknowledgement. |

`API_STUB=1` (the server default) returns these files. The demo sets `API_STUB=0`.

### `corpus/`

Fictional contract, official-text snapshots, rule cards, and recorded model traffic. No live client data.

| File | Why it exists |
|------|----------------|
| `NOTES.md` | Which provisions were taken, from which official page, and on which date. |
| `contracts/master_dpa.md` | The fictional 12-clause Acme–Nimbus agreement the lawyer reviews. |
| `raw/manifest.json` | Version ids, hashes, which text file is which provision, and which version supersedes which. |
| `raw/DPDP-Act-2023_s1.txt` | Act section 1, short title and commencement. |
| `raw/DPDP-Act-2023_s8-1-2.txt` | Act s8(1)–(2), processor obligations. |
| `raw/DPDP-Act-2023_s8-4-5.txt` | Act s8(4)–(5), security safeguards. |
| `raw/DPDP-Act-2023_s8-6.txt` | Act s8(6) as enacted. The breach-intimation rule cites this span. |
| `raw/DPDP-Act-2023_s8-6.v2sim.txt` | Simulated s8(6) with a fictional 48-hour Board line. `is_simulated=true`. |
| `raw/DPDP-Act-2023_s8-7-8-s12.txt` | Later Act provisions kept so the snapshot is not only the demo sections. |
| `raw/DPDP-Rules-2025_r1.txt` | Rules rule 1. |
| `raw/DPDP-Rules-2025_r6.txt` | Rules rule 6. |
| `raw/DPDP-Rules-2025_r7.txt` | Rules rule 7. |
| `raw/DPDP-Rules-2025_r8.txt` | Rules rule 8. |
| `raw/GSR-843E-2025.txt` | Commencement notification. Used for the as-of / in-force check. |
| `raw/DECOY_Emblems-Act-1950_s3.txt` | Unrelated statute. Ingesting it must flag no findings. |
| `rulecards/RC-CT1-CONTRACT-SEC-01.yaml` | Card: a processor needs a valid contract. |
| `rulecards/RC-CT1-ENGAGE-01.yaml` | Card: engagement only on documented instructions. |
| `rulecards/RC-CT2-ENC-01.yaml` | Card: encryption safeguard. |
| `rulecards/RC-CT2-SAFE-01.yaml` | Card: security safeguards. |
| `rulecards/RC-CT2-LOGRET-01.yaml` | Card: log retention. |
| `rulecards/RC-CT3-BREACH-01.yaml` | Card: breach intimation duty on s8(6). This is the finding the simulated amendment stales. |
| `rulecards/RC-CT3-BREACH-CONFLICT-01.yaml` | Fictional opposite reading (`no_breach_intimation_duty`) so two cards can conflict. |
| `rulecards/RC-CT3-72H-01.yaml` | Card: the 72-hour updated-intimation reading. |
| `scans/clause_9_2_page.png` | Fictional scanned page of clause 9.2. The scan cassette was recorded against this image. |
| `audio/dictation_fact.wav` | Fictional WAV dictation. The speech cassette was recorded against this file. |
| `cassettes/*.json` | 55 recorded Responses API exchanges, named by the sha256 of the exact request. Replay serves these. A different request (for example after approving a fact) misses the file and returns 502. |
| `cassettes/2ac4b57a….asr.json` | The one recorded speech-to-text response for `dictation_fact.wav`. |

### `scripts/`

| File | Why it exists |
|------|----------------|
| `seed_demo.py` | Loads corpus, contract, cards, and extraction facts into SQLite. `make seed`. |
| `reset_demo.sh` | Deletes the demo DB and seeds it again. Run this before a recording. |
| `record_cassettes.py` | Re-records model and speech cassettes. Spends credits. At most once per task. |
| `export_openapi.py` | Writes `openapi/openapi.json` from the FastAPI app. |
| `hellometamodl.py` | Day-1 Meta API hello-world used to measure cost. Filename kept as committed. |
| `git-hooks/pre-commit` | Blocks a normal `git commit` and blocks committing secrets. |
| `git-hooks/commit-msg` | Blocks co-author and "generated by" lines. `git hc` is the allowed commit path. |
| `git-hooks/pre-push` | Push guard installed by `make hooks`. |

### `backend/`

Python 3.12, FastAPI, SQLAlchemy 2, SQLite. `make check-backend` is ruff, mypy, and pytest.

| File | Why it exists |
|------|----------------|
| `pyproject.toml` | Package metadata and tool settings for ruff, mypy, and pytest. |
| `Dockerfile` | Image for the API. Compose and an off-machine check are not done. |
| `nohup.out` | Leftover server log that was committed. Not part of the product. Do not add it again. |
| `app/main.py` | FastAPI app, version pin (v9), `GET /` and `GET /health`. |
| `app/api.py` | HTTP routes: matter, claims, findings, sources, ingest, impact, re-check, counterfactual, reverify list, facts, scans, dictations, audit. |
| `app/schemas.py` | Pydantic request and response models, including the v9 display-label fields. |
| `app/models.py` | SQLAlchemy tables. |
| `app/db.py` | Engine and session. `NullPool` so a reset mid-run opens the new database file. Append-only triggers live with the schema. |
| `app/stub.py` | `API_STUB=1` responses read from `openapi/examples/`. |
| `app/core/errors.py` | Typed errors (`SourceUnavailable`, `ProofRejected`, and the API envelope). |
| `app/agent/llm.py` | The only Responses API client. Live, replay, and mock. Logs tokens and cost. |
| `app/agent/prompts.py` | Prompts for extraction, claims, the proof loop, scan, and the six tool schemas. |
| `app/agent/tools.py` | The six tools. Unknown tools are rejected. Calls are logged. |
| `app/agent/loop.py` | Tool loop that drafts a proof. Caps calls and retries. |
| `app/agent/claims.py` | Turns a question into a typed claim. Anything outside the types is UNKNOWN. |
| `app/agent/extract.py` | Clause and fact extraction from the contract. |
| `app/agent/challenger.py` | Second Muse Spark pass. Objections can force needs-review. |
| `app/agent/scan.py` | Image transcription for a scanned page. PNG/JPEG only. |
| `app/agent/transcribe.py` | WAV dictation client for the speech endpoint. Replay uses the `.asr.json` cassette. |
| `services/sources.py` | Store and load hashed source versions and provisions. |
| `services/rulecards.py` | Load YAML cards and reject a card whose span is not in the snapshot. |
| `services/seed.py` | Demo seed, including one current finding per rule card. |
| `services/diff.py` | Provision diff and as-of / in-force. |
| `services/memory.py` | The only place a finding status is decided and written. |
| `services/graph.py` | Dependency edges and reverse traversal. |
| `services/impact.py` | Ingest → diff → stale events → impact report. |
| `services/reverify.py` | Re-check: new finding, old row kept, requires a fresh lookup. |
| `services/premises.py` | Approve, challenge, and reject. Each trust change is a new fact row. |
| `services/counterfactual.py` | Read-only what-if. Does not write stale events. |
| `checker/verify.py` | Deterministic proof checker. No model import, no network. |
| `checker/proplogic.py` | Propositional entailment for the what-if and for conflicting cards. |
| `checker/__main__.py` | `python -m checker verify proof.json`. |

`app/__init__.py`, `app/agent/__init__.py`, `app/core/__init__.py`, `app/services/__init__.py`, and `checker/__init__.py` mark those folders as Python packages.

### `backend/tests/`

Every test file exists so a regression fails before a behaviour change is trusted. Tests never call the live model.

| File | Why it exists |
|------|----------------|
| `test_health.py` | `/api/health`, `GET /`, and `GET /health`. |
| `test_schema.py` | Tables exist and append-only triggers reject update and delete. |
| `test_contract_v0.py` | Pins `info.version` so a silent contract drift fails. Now pins v9. |
| `test_services_sources.py` | Snapshot hashing, idempotent ingest, simulated and decoy versions. |
| `test_rulecards.py` | A card span that is not in the snapshot is rejected. |
| `test_seed.py` | Seed is deterministic and loads 8 cards. |
| `test_diff.py` | Diff by provision key, and in-force before and after commencement. |
| `test_llm_gateway.py` | Replay matches the cassette. Live is blocked under pytest. |
| `test_extract.py` | Extraction cassette returns the 12 clauses. |
| `test_claims.py` | Supported questions get a type. Unsupported ones are UNKNOWN. |
| `test_checker.py` | Proof schema, admission rules, span and hash. |
| `test_checker_steps.py` | Each step kind, plus tamper, wrong value, out-of-force, and superseded version. |
| `test_checker_isolation.py` | AST scan: the checker does not import the agent or an LLM client. |
| `test_tools.py` | Six tools only. Cross-matter access, a 13th call, and an unknown tool fail. |
| `test_loop.py` | The loop drafts a proof the checker accepts for clause 9.2. |
| `test_memory.py` | The model cannot set status. Each status path is covered. |
| `test_graph.py` | A changed provision stales only dependents. A decoy stales none. |
| `test_impact.py` | Impact report flags the expected findings. |
| `test_reverify.py` | Re-check supersedes, keeps the old row, and rejects a stale lookup. |
| `test_premises.py` | Approve and challenge create a new row. NullPool survives a reset. |
| `test_challenger.py` | A blocking objection forces needs-review. |
| `test_proplogic.py` | Truth-table entailment, including negation and the atom cap. |
| `test_counterfactual.py` | What-if writes nothing and flags the s8(6) dependents. |
| `test_conflicting.py` | Contradictory cards become CONFLICTING. An invalid proof does not. |
| `test_display_labels.py` | v9 lawyer labels sit beside the machine fields. |
| `test_scan.py` | Replay scan, stored fact, bad base64, and PDF rejected. |
| `test_transcribe.py` | Replay transcript, unapproved fact fails verify, approved fact passes. |
| `test_scenarios.py` | T8.1: decoy, future provision, stale chain, matter isolation, source failure. |
| `test_api.py` | HTTP paths: ask, ingest, re-check, audit, clause-ref, review, and the gate regressions. |

### `frontend/`

React 18, Vite, TypeScript, Tailwind. `make check-frontend` is oxlint and vitest. The dev server proxies `/api` to port 8000.

| File | Why it exists |
|------|----------------|
| `package.json` | Dependencies and scripts (`dev`, `build`, `test`, `gen:api`). |
| `package-lock.json` | Locked install. |
| `index.html` | Vite entry document. |
| `vite.config.ts` | Dev server on 5173 and the API proxy. |
| `tsconfig.json` | TypeScript project references. |
| `tsconfig.app.json` | App compiler options. Strict. |
| `tsconfig.node.json` | Config-file compiler options. |
| `tailwind.config.js` | Design tokens, including light and dark. |
| `postcss.config.js` | Tailwind PostCSS pipeline. |
| `.oxlintrc.json` | Linter config. |
| `.gitignore` | Frontend build and local ignores. |
| `README.md` | Vite starter note. The product README is the repo root. |
| `public/favicon.svg` | Browser tab icon. |
| `public/icons.svg` | Icon sprite. |
| `src/main.tsx` | React mount. |
| `src/App.tsx` | Router: `/review`, `/impact`, `/control`. |
| `src/App.test.tsx` | The three routes render. |
| `src/index.css` | Tailwind layers and shared panel styles. |
| `src/assets/hero.png` | Unused starter image from the Vite template. |
| `src/assets/react.svg` | Unused starter asset. |
| `src/assets/vite.svg` | Unused starter asset. |
| `src/test/setup.ts` | Vitest DOM setup. |
| `src/api/schema.d.ts` | Generated from OpenAPI v9. Do not hand-edit. Regenerate with `npm run gen:api`. |
| `src/api/types.ts` | App types over the generated schema, including `FindingStatus`. |
| `src/api/client.ts` | Live fetch client. This is what the demo uses. |
| `src/api/client.test.ts` | Client calls the expected paths. |
| `src/api/config.ts` | Matter and document ids. Mocks only when `MODE=test` or `VITE_USE_MOCKS=1`. |
| `src/api/demoSession.ts` | Remembers the claim id for the session so Screen 3 can load the current answer. |
| `src/api/mocks/index.ts` | Test doubles fed from the OpenAPI examples. |
| `src/api/mocks/stretch.ts` | Test doubles for what-if, reverify list, scan, and dictation. |
| `src/api/mocks/impactDemo.ts` | Test graph and impact fixtures. |
| `src/api/mocks/lawyerControl.ts` | Local sample findings for the uncovered question, the as-of card, and the post-challenge card. These three are not server decisions. |
| `src/api/mocks/runTrace.ts` | Sample tool-trace events for tests. |
| `src/api/mocks/challenger.ts` | Sample second-review report for tests. |
| `src/api/mocks/challenger.test.ts` | The sample report parses. |
| `src/content/disclaimer.ts` | The banner sentence. It is on every screen. |
| `src/content/glossary.ts` | Lawyer sentences for status, trust, and reasons. Fallback when a v9 label is empty. |
| `src/utils/displayFields.ts` | Picks a display label, then the glossary. Never an id. |
| `src/utils/displayFields.test.ts` | Empty labels fall back. Ids do not leak. |
| `src/utils/lawyerCopy.ts` | Drops error text that contains ids, hashes, cassette, 502, or tool names. |
| `src/utils/findingTraces.ts` | Pulls the clause quote, section quote, and fact lines out of a finding. |
| `src/utils/findingTraces.test.ts` | Trace extraction. |
| `src/utils/trustClass.ts` | Maps a trust class string onto the chip type. |
| `src/utils/fileBase64.ts` | Reads a PNG, JPEG, or WAV into base64 for scan and dictation. |
| `src/components/layout/AppLayout.tsx` | Page shell: banner, nav, outlet. |
| `src/components/layout/DisclaimerBanner.tsx` | The legal-limits banner. |
| `src/components/layout/SiteNav.tsx` | Review a clause / Law changes / Your control room. |
| `src/components/FindingCard.tsx` | One answer: legal test, status, quotes, law-version date, draft badge. |
| `src/components/FindingCard.test.tsx` | The card shows the glossary sentence, not an id. |
| `src/components/ProofSyllogism.tsx` | The three-step reasoning block under an answer. |
| `src/components/TrustChip.tsx` | Taken from the document / Confirmed by you / Disputed by you / Proposed. |
| `src/components/DiffView.tsx` | Before/after section text on Law changes. |
| `src/components/StaleGraph.tsx` | React Flow graph of answers and provisions, with the re-check count. |
| `src/components/AuditList.tsx` | History list. |
| `src/components/ChallengerPanel.tsx` | Second-review pass: flagged or not flagged. |
| `src/components/ChallengerPanel.test.tsx` | The panel copy. |
| `src/components/badges/StatusBadge.tsx` | Status text and icon, including Conflicting. |
| `src/components/badges/AiDraftBadge.tsx` | "AI draft — not yet reviewed". |
| `src/components/badges/LawyerReviewedBadge.tsx` | "Reviewed by lawyer". |
| `src/components/badges/SimulatedBadge.tsx` | SIMULATED on a fictional amendment. |
| `src/components/clause-review/ClauseList.tsx` | The 12 contract clauses. Clause 9.2 is selected on load. |
| `src/components/clause-review/AskBox.tsx` | Question, as-of date, Ask. |
| `src/components/clause-review/SourceTrace.tsx` | Cited clause and cited section. |
| `src/components/clause-review/PremiseTrace.tsx` | Facts the answer used. |
| `src/components/clause-review/WhatWouldChangePanel.tsx` | What would change this answer. |
| `src/components/clause-review/ToolTracePanel.tsx` | Tool-call trace. Kept for tests. Not shown on the lawyer screen. |
| `src/pages/ClauseReviewPage.tsx` | Review a clause. Ask, poll the run, show the answer, mark lawyer-reviewed. |
| `src/pages/ClauseReviewPage.test.tsx` | Ask and the answer card on mock data. |
| `src/components/impact/VersionPicker.tsx` | Legal source, law version, preview, apply. |
| `src/components/impact/WhatIfPanel.tsx` | Preview a law change — nothing is saved. |
| `src/components/impact/ReverifyListPanel.tsx` | Queue of answers already waiting (stale or conflicting). |
| `src/components/impact/AffectedFindings.tsx` | Queue for the amendment just applied, plus the Re-check button. |
| `src/components/impact/BeforeAfterSplit.tsx` | Earlier answer and later answer. The later card stays empty until a re-check result is passed in. |
| `src/pages/SourceImpactPage.tsx` | Law changes. Wires preview, apply, graph, re-check, and history. |
| `src/pages/SourceImpactPage.test.tsx` | Preview does not save. Re-check copy has no ids. |
| `src/components/lawyer/FactTrustList.tsx` | Facts awaiting approval, with Approve and Challenge. |
| `src/components/lawyer/FactWordingEditor.tsx` | Edit one fact sentence and re-check it against the document. |
| `src/components/lawyer/ProofEditor.tsx` | Older proof editor. The screen uses the wording editor. |
| `src/components/lawyer/AsOfPanel.tsx` | Law-version date. The in-force line is computed in the browser. |
| `src/components/lawyer/UnknownClaimDemo.tsx` | "When the file does not cover it." The button shows a local sample. |
| `src/components/lawyer/ScanPagePanel.tsx` | Add a scanned clause page. Posts base64 PNG or JPEG. |
| `src/components/lawyer/DictationPanel.tsx` | Dictate a fact. Posts base64 WAV. The fact stays proposed until approve. |
| `src/pages/LawyerControlPage.tsx` | Your control room. Facts, wording, as-of, uncovered question, scan, dictation. |
| `src/pages/LawyerControlPage.test.tsx` | Approve, challenge, wording re-check, and the uncovered-question sample. |

## Status

| Item | State |
|------|--------|
| Calendar | Day 6 work is done. Stretch T7.1–T7.4 is in the tree. Day 7 deploy and the video are not. |
| Core gate | Green on replay after `make reset-demo` (2026-11-02). Ask clause 9.2 → meets the requirement. Simulated s8(6) ingest → only the dependent answers need re-check. Re-check stores a new answer that needs review. |
| Contract | v0 → v9, additive after v1. Current `openapi/openapi.json` `info.version` is `v9`. |
| Last logged backend check | `make check-backend` pytest **248/248**, ruff clean, mypy clean (`[approve-500]`, 2026-11-02 15:55 IST). |
| Last logged frontend check | `make check-frontend` oxlint 0, vitest **34/34**, `tsc -b` pass (`[phase3-workflows]`, 2026-11-02 15:17 IST). |
| Latest browser walk | 2026-11-02 ~16:50–17:15 IST, replay, no code changes. Results are in the walk section below. |
| Servers | Both were stopped after that walk. API was port 8000, site was http://127.0.0.1:5173. |
| Demo database | Dirty from that walk. Reset before the next recording. |

## What is built

### Engine

- SQLite (WAL) with SQLAlchemy 2. `findings`, `source_versions`, `provisions`, and `audit_log` are append-only. State changes are new `finding_events` rows.
- Hashed source snapshots. Versions: DPDP Act v1, simulated Act v2 (`is_simulated=true`, supersedes v1), DPDP Rules, commencement notification, and a decoy (Emblems and Names Act, 1950). The simulated change is section 8(6): a fictional 48-hour Board intimation. Changed key: `DPDP-Act-2023_s8(6)`.
- Eight rule cards. Seven topic cards plus `RC-CT3-BREACH-CONFLICT-01` (`requires: [no_breach_intimation_duty]` on the same s8(6) span). Cards are still `ai_inferred`. Seed writes one current finding per card. The 9.2 transfer-log finding stays separate and does not depend on s8(6).
- LLM gateway in `backend/app/agent/llm.py`: `LLM_MODE=live|replay|mock`, default replay. Tests never use live. Temperature 0. Max 12 tool calls, max 2 retries. Cassettes in `corpus/cassettes/`. Models: `muse-spark-1.3-contributor` for extraction, claims, and the loop; `muse-spark-1.2` for the challenger only. Dictation uses `muse-voice-transcribe-1.0` through `backend/app/agent/transcribe.py` (not the Responses API).
- Exactly six tools: `lookup_source`, `list_dependent_claims`, `get_premise`, `verify_derivation`, `propose_finding`, `request_lawyer_review`.
- Checker in `backend/checker/` imports nothing from the agent and does not call the network. `checker/proplogic.py` is a separate propositional entailment helper used by the counterfactual and the conflict check. It does not replace `verify.py`.
- Statuses: `FOLLOWS`, `RULED_OUT`, `UNKNOWN`, `REQUIRES_REVIEW`, `CONFLICTING`. States include `CURRENT`, `STALE`, `SUPERSEDED`, `REVIEWED`. Premises used in a proof must be `lawyer_confirmed` or `document_extracted`.
- `CONFLICTING` is set only when a checker-valid proof cites cards whose `requires` contradict (`no_` / `not_` means negation) . An invalid proof stays `REQUIRES_REVIEW`. On a full demo seed, Act v2 supersedes v1, so a cite of the v1 s8(6) span fails as superseded. The conflict pair is proven in tests on a v1-current corpus. The lawyer walk did not surface a "Conflicting" label.
- Impact: identical-content ingest of a stored version still runs `impact.apply_version`. A finding goes stale only when it depends on a card whose provision key changed. Decoy ingest flags nothing.
- Re-check writes a new finding and keeps the old one. The seeded s8(6) proof, re-checked after v2, becomes **Needs your review** because the cited v1 span is superseded.
- Challenger is optional (`CHALLENGER=on`). As-of `2026-11-20` on the recorded 9.2 question returns meets-the-requirement when the challenger does not block. As-of `2025-10-17` with the challenger on returns needs-review (no challenger cassette for that date; the finding is kept).
- UNKNOWN questions skip the agent loop and store an UNKNOWN finding.
- A question that names `clause 9.2` is stored against that clause even if the caller sent another `clause_id`.
- `POST /api/claims` returns the agent loop's run id, so the UI polls the real tool trace.
- Matter-scoped audit includes `impact.applied`.
- Approve after `make reset-demo` no longer 500s. The engine uses `NullPool`, and premise results are refreshed and expunged before return. A second approve of an already-superseded fact is **400**. The control-room page shows no message for that 400.
- Display labels (contract v9) sit beside the machine fields: `status_label`, `clause_quote`, `section_quote`, `law_version_label`, `law_version_date`, `fact_lines`, `reason_label`, `would_follow_label`, trust labels, and plain error text. Machine ids, hashes, proof JSON, and error codes stay in the API. The recorded 9.2 proof cites a fact, not a rule card, so its section fields are empty and the screen falls back to "A cited section of the law".

### Contract versions

| Version | What was added |
|---------|----------------|
| v0 | Stub examples |
| v1 | Real router when `API_STUB=0` |
| v2 | Ask loop returns the finding; challenger report |
| v3 | Proof step fields round-trip |
| v4 | `GET /` and `GET /health` |
| v5 | Real `POST /api/counterfactual`; `GET /api/reverify-list` |
| v6 | Status value `CONFLICTING` |
| v7 | `POST /api/scans` (PNG/JPEG base64 JSON, not multipart) |
| v8 | `POST /api/dictations` (WAV base64). Fact is `ai_inferred` until approve |
| v9 | Lawyer display labels. Machine fields unchanged |

### Stretch (coded; task checkboxes in `docs/TASKS.md` are still open)

- **T7.3** Counterfactual: read-only dry run. Does not write STALE events. For the simulated Act version it reports section 8(6) and both clause 10 answers would no longer follow.
- **T7.4** CONFLICTING status, plus the approved eighth demo card. Two challenger cassettes were re-recorded (~$0.0004).
- **T7.2** Scan. Fixture `corpus/scans/clause_9_2_page.png`. Replay cassette exists. PDF is rejected. A scan is stored as its own document, so the demo DPA clause list is unchanged. The fact is `document_extracted` only once stored.
- **T7.1** Dictation. Fixture `corpus/audio/dictation_fact.wav`. Replay ASR cassette exists. Unapproved dictation fails verify with `PREMISE_UNTRUSTED`. Approve uses the existing premise flow.
- **T7.5** Open-weights challenger: not started. Needs partner access. Nothing else depends on it.

### Frontend

Three routes, lawyer navigation:

- `/review` — Review a clause
- `/impact` — Law changes
- `/control` — Your control room

Every screen shows the disclaimer and **AI draft — not yet reviewed** until a review action. Status is text plus an icon. Vite proxies `/api` to `127.0.0.1:8000`. Mocks are for tests (`MODE=test` or `VITE_USE_MOCKS=1`), not the demo path.

Wired to the live API: ask, current finding, lawyer review, sources, diff, ingest, impact, graph, audit, counterfactual preview, reverify list, re-check, facts approve/challenge, proof verify, scan, dictation.

Glossary is in `frontend/src/content/glossary.ts`. Rendered copy prefers the v9 display fields and falls back to that glossary, not to ids.

These control-room moments are drawn in the browser and do **not** call the server:

- "Ask a question this file does not cover" uses a local sample finding.
- Moving the law-version date across 2025-10-01 only toggles the local "Section 6 is in force / not in force" line.
- After a real challenge, the "current answer" card is replaced by a local cannot-be-determined sample. The approve and challenge requests themselves are real.

### Demo script that works on replay

```text
make reset-demo
API_STUB=0 LLM_MODE=replay DEMO_MODE=1 CHALLENGER=on \
  backend/.venv/bin/uvicorn app.main:app --app-dir backend --port 8000
# other terminal
cd frontend && npm run dev -- --host 127.0.0.1 --port 5173
```

Order:

1. Reset first.
2. Ask "Does clause 9.2 require Nimbus to keep transfer logs?" as of **2026-11-20** before approving any fact.
3. Law changes: Digital Personal Data Protection Act, 2023, version **v2-simulated**. Preview, then apply. Two clause 10 answers need re-check. Re-check once.
4. Optional: apply the Emblems Act version. Nothing needs re-check.
5. Then, and only then, approve or challenge facts, or edit a fact sentence and re-check.

Approving or challenging inserts a new premise row. The recorded Ask hashes the premise list. The next Ask returns 502 until `make reset-demo`. The page shows "This request could not be completed. Try again."

`CHALLENGER=on` changes the 2025-10-17 ask to needs-review. Turn it off if that date must meet the requirement.

## Lawyer walk on 2026-11-02 (browser, no code changes)

Fresh reset, then replay with `CHALLENGER=on`. No credits spent.

| Step | Result |
|------|--------|
| Ask 9.2 / 2026-11-20 | Pass. "Meets the requirement — on the facts and law listed below." Second review did not flag the draft. Clause quote is the real 9.2 text. Section line is the fallback "A cited section of the law". |
| Preview simulated Act v2 | Pass. Section 8(6) text includes the simulated 48-hour sentence. Both clause 10 answers "would no longer follow". Nothing saved. |
| Apply simulated Act v2 | Pass. "2 of 9 answers need re-check", both clause 10. The 9.2 answer stays current. Badge SIMULATED is shown. |
| Re-check | Partial. `POST /api/impact/IMP-SV-DPDP-ACT-V2SIM/reverify` returned 200. The new finding is `REQUIRES_REVIEW` / "Needs your review before it can be relied on". The page never shows that new answer. Both queue rows stay. The button becomes "Re-checked" and cannot be used for the second clause 10 answer. The before/after block still shows the commencement text under the heading Section 8(6). |
| Apply the Emblems Act version | Pass. 200. "0 of 11 answers need re-check". |
| Approve the transfer-log fact | Pass. "Confirmed by you". `POST /api/facts/F-LOOP-92/approve` 200. |
| Approve that same fact again | Server 400, page silent. |
| Challenge the parties fact | Pass. "Disputed by you". `POST /api/facts/F-SEED-01/challenge` 200. The current-answer card then shows a local "Cannot be determined" sample. |
| Change the fact sentence and re-check | Pass. `POST /api/proofs/verify` 200. "This fact no longer matches the document." |
| Law-version date 2025-09-01 | Local only. "Section 6 is not in force on 2025-09-01." |
| Uncovered question button | Local only. Shows "Cannot be determined" with no `POST /api/claims`. |
| Ask 9.2 again after the approve | Fail, expected on replay. 502. Page text: "This request could not be completed. Try again." |
| Mark lawyer-reviewed | Not completed. The button was on screen after the first answer. The failed second ask removed it. |
| Scan and dictate | Controls are on the page. This browser session cannot choose a local file, so they were not submitted. Replay cassettes exist only for the repo fixtures, not for an arbitrary file. |

Leftovers still visible to a lawyer: graph keys such as `DPDP-Act-2023_s8(6)`, nodes labelled only "Answer", and history rows that are a UTC timestamp plus "A record was added". No screen showed a conflicting-readings label.

The walk dirtied the demo database: simulated amendment applied, one confirmed fact, one disputed fact, one new needs-review finding, one failed second claim. `make reset-demo` before the next demo.

## Checks and commits

Recent commits, newest first:

| Hash | What |
|------|------|
| `e1c130b` | Contract v9, scan, dictation, schemas, tests. WAL/SHM removed from git. |
| `ae001d6` | Stored-amendment tracking, counterfactual tests, conflicting-card scenarios. T7.3 and T7.4. |
| `59025a7` | Stored-version impact, UNKNOWN without the loop, lawyer review, contract v4, T8.1 scenarios, Dockerfile. |
| `6264d22` | Docs snapshot from before the gate was closed in the status files. |
| `82fc307` | Seed facts at reset, stable ask cassette, Screen 1 defaults. |
| `6b62985` | Ask loop, cassettes, contract v2. |
| `9c65591` | T2.3 through T6: checker, tools, loop, memory, graph, impact, screens, challenger, live wire. |

Earlier Day 1–2 commits run from `91fc1f3` (docs only) through `010a2c9` (seed and diff).

Logged credit spend is about **$0.88**, plus about $0.0012 for the T7.1, T7.2, and T7.4 record runs. The 2026-11-02 gate walk and the lawyer walk were replay and spent $0. Billing page was not re-checked. Cap is $150. Do not run `make record` unless a task says so.

## Not done

- T8.2: `backend/Dockerfile` exists and was built once. There is no root Compose file, no check from another network, and no timed `make reset-demo` recorded here as under 60 seconds.
- T8.3 rough video, T8.4 judge pass, T9 README-as-sales-doc, final video, X post, submission.
- T7.5 open weights.
- Status docs (`PROGRESS.md`, `TASKS.md` T7 checkboxes, `NEW_WORK.md`, `HUMAN_LOG.md`) do not yet mention T7.1–T7.4 or contract v5–v9.
- Rule-card `trust_class` is still `ai_inferred`. Card topic names still differ from the CT1–CT4 names in the architecture note.
- Template file is `env.example`, not `.env.example`.
- Backend default is still `API_STUB=1`. The demo must set `API_STUB=0` and `LLM_MODE=replay`.
- No CORS. The Vite proxy is the demo path. A browser pointed straight at port 8000 fails.
- Do not `git add` `backend/db.sqlite3-wal`, `backend/db.sqlite3-shm`, or `backend/nohup.out`.

## Invariants that must stay

1. `backend/checker/` does not import `app.agent`, open the network, or call a model.
2. Append-only tables stay append-only.
3. The model gets exactly those six tools.
4. Only the memory service sets a finding status.
5. Proof premises are `lawyer_confirmed` or `document_extracted`.
6. Every citation is `(source_version_id, provision_id, span, sha256)` and the quote matches the snapshot.
7. A stale finding is replaced only by a new finding whose tool log shows a fresh `lookup_source` of the current version.
8. Simulated amendments stay `is_simulated=true` and show the SIMULATED badge.
9. Every screen keeps the disclaimer. Unreviewed output stays "AI draft — not yet reviewed".
10. Every query is scoped by `matter_id`.

## Next session

1. `make reset-demo` before any demo or recording.
2. Fix the lawyer-visible holes if that is the task: re-check never shows the new answer and only consumes the first stale row; the section-change panel shows the wrong body; a second approve is silent; the uncovered-question, as-of, and post-challenge cards are local samples; the 9.2 section quote is the glossary fallback; the graph and history still show machine strings.
3. Bring `PROGRESS.md`, `docs/TASKS.md`, `NEW_WORK.md`, and `docs/logs/HUMAN_LOG.md` up to contract v9 and T7.1–T7.4. Those files are the human's to commit.
4. T8.2 deploy, then the three-minute lawyer video. Ask before approving facts. Reset first.
