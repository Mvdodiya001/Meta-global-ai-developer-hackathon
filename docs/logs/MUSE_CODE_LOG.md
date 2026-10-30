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

## [T1.1] STARTED · 2026-10-29 15:10 IST
- Task: Schema + append-only triggers
- Scope: all DATA_MODEL_API §2 tables in `backend/app/models.py`, SQLite WAL engine + append-only triggers in `backend/app/db.py`, tests first in `backend/tests/test_schema.py`

## [T1.1] DONE · 2026-10-29 15:12 IST
- Task: Schema + append-only triggers
- Files changed: `backend/app/models.py` (new, 19 SQLAlchemy 2 tables), `backend/app/db.py` (new, WAL engine + `init_db` + 8 triggers), `backend/tests/test_schema.py` (new, written first, 10 tests), `docs/logs/MUSE_CODE_LOG.md` (modified)
- What changed: All DATA_MODEL_API §2 tables exist with §2 key fields and FKs (ids are caller-supplied prefixed strings; timestamps are UTC ISO-8601 strings). `init_db(path)` creates the schema and installs BEFORE UPDATE/DELETE triggers aborting with `<table> is append-only` on `findings`, `source_versions`, `provisions`, `audit_log`. Engine sets `PRAGMA journal_mode=WAL` and `foreign_keys=ON` per connection.
- Checks run: `make check-backend` → pass (ruff clean; mypy clean on 9 files; pytest 40/40, incl. 10 new schema tests). Independent probe on a scratch DB confirmed `journal_mode=wal`, `foreign_keys=1`, and all 8 triggers in `sqlite_master` (probe file deleted afterwards).
- Decisions / assumptions: No Alembic — `create_all` in `init_db` is enough until T1.4 seeding needs migrations. JSON columns for `*_json` fields; `finding_events` itself has no trigger (state log grows by inserts only, enforced by services later). `Run`/`Review`/`LlmCall` shadow stdlib/sqlalchemy names only as class names, no imports shadowed.
- Contract change: none (v0 stands; schema is not yet exposed)
- Requests: none
- New-work note: SQLite schema + append-only triggers 2026-10-29
- Third-party added: none (SQLAlchemy 2.1.6 from T0.4)
- Credit spend: none (no model calls)
- Ready for human commit: yes — suggested message: `T1.1: add schema with append-only triggers`

## [T1.2] STARTED · 2026-10-29 17:44 IST
- Task: Source snapshots + provisions
- Scope: `backend/app/services/sources.py` (hashed ingest, idempotency, lookups), `corpus/raw/` (cleaned provision texts + manifest), tests first in `backend/tests/test_services_sources.py`. Texts from human-verified `corpus/NOTES.md` (T0.6); v2 is labelled simulated; decoy is the Emblems Act source

## [T1.2] DONE · 2026-10-29 17:56 IST
- Task: Source snapshots + provisions
- Files changed: `backend/app/services/__init__.py` + `backend/app/services/sources.py` (new, ingest/lookup), `backend/app/core/__init__.py` + `backend/app/core/errors.py` (new, `SourceUnavailable`), `backend/app/db.py` (modified: dropped `foreign_keys=ON`, see decisions), `backend/tests/test_services_sources.py` (new, 6 tests), `corpus/raw/` (new: 12 provision texts + `manifest.json`), `docs/logs/MUSE_CODE_LOG.md` (modified)
- What changed: `load_corpus()` ingests 4 sources / 5 versions / 16 provisions from `corpus/raw/`: DPDP Act v1 (5 provisions), Rules v1 (4), commencement notification G.S.R. 843(E) v1 (1), Emblems Act decoy v1 (1), plus simulated Act v2 (`is_simulated=true`, `supersedes SV-DPDP-ACT-V1`) amending only s8(6) with a marked `[SIMULATED AMENDMENT v2]` proviso. Snapshot `raw_text` is the join of provision files; `content_sha256`/`text_sha256` are sha256 of stored bytes. Same content re-ingested returns the existing version id with no new rows. Unknown source/version lookups raise `SourceUnavailable`.
- Checks run: `make check-backend` → pass (ruff clean; mypy clean on 14 files; pytest 46/46, incl. 6 new T1.2 tests). Scratch-DB probe confirmed 5 versions / 16 provisions, v2 differing from v1 only by the simulated marker (probe DB deleted).
- Decisions / assumptions: Provision texts transcribed verbatim from human-verified `corpus/NOTES.md` (T0.6). **Dropped `PRAGMA foreign_keys=ON`** from the `connect` listener: with SQLAlchemy 2.1.6 / Python 3.12 pysqlite it silently drops the parent INSERT from combined ORM flushes (child then fails FK) — reproduced with zero app code (2 tables + listener + 1 commit) vs clean without it. WAL mode kept. FK validity now enforced at the service layer (`ingest_version` rejects unknown sources; parents always written first). T1.1 trigger guarantees unaffected. No legal text asserted beyond the T0.6 record; v2 text is explicitly fictional.
- Contract change: none (v0 stands)
- Requests: none. Note for H: no new third-party sources — all texts from `NOTICE.md`/`corpus/NOTES.md` (T0.6 record).
- New-work note: source snapshot + provision loading 2026-10-29
- Third-party added: none (stdlib hashlib/json; SQLAlchemy from T0.4)
- Credit spend: none (no model calls)
- Ready for human commit: yes — suggested message: `T1.2: add source snapshots and provisions`

## [T1.3] STARTED · 2026-10-29 18:17 IST
- Task: Rule cards (MC authors, H reviews)
- Scope: `corpus/rulecards/*.yaml` (7 cards, CT1–CT3, verbatim spans), strict stdlib-only loader in `backend/app/services/rulecards.py`, tests first in `backend/tests/test_rulecards.py`. No PyYAML (not installed; new deps need H approval) — loader parses only the documented card shape and rejects everything else

## [T1.3] DONE · 2026-10-29 18:21 IST
- Task: Rule cards (MC authors, H reviews)
- Files changed: `corpus/rulecards/` (new, 7 `RC-*.yaml` cards), `backend/app/services/rulecards.py` (new, strict subset-YAML parser + span verifier + DB ingest), `backend/app/core/errors.py` (modified, added `RuleCardError`), `backend/tests/test_rulecards.py` (new, written first, 6 tests), `docs/logs/MUSE_CODE_LOG.md` (modified)
- What changed: 7 cards covering CT1 (processor contract: s8(1)-(2), Rule 6(1)(f)), CT2 (safeguards: s8(4)-(5), Rule 6(1)(a), Rule 6(1)(e)), CT3 (breach intimation: s8(6), Rule 7(2)(b)). Each cites a verbatim span with explicit offsets; loader rejects bad spans, unknown provisions, and malformed files before writing anything, then upserts idempotently into `rule_cards`. Cards authored `trust_class: ai_inferred`, `approved_by: pending-human-review` until H reads them.
- Checks run: `make check-backend` → pass (ruff clean; mypy clean on 15 files; pytest 52/52, incl. 6 new T1.3 tests). Independent scratch-DB probe confirmed all 7 spans byte-match their snapshots (probe DB deleted).
- Decisions / assumptions: CT1–CT3 taxonomy is not defined in docs, so I defined it narrowly from the T0.6 provisions (see loader docstring; CT4 reserved for erasure in T2.3) — confirm or rename on review. No new dependency: PyYAML is not installed and new deps need approval, so the loader parses only the documented card shape (flat keys, `|` blocks, `[a, b]` requires) and rejects the rest; swapping in PyYAML later is trivial. Upsert keeps original `created_at`; replacements via `superseded_by` come later if needed.
- Contract change: none (v0 stands)
- Requests: [REQ → H] (1) read each of the 7 cards against the official text (T1.3 Done criterion) and say whether to flip `trust_class` to `lawyer_confirmed` (loader change, my lane) — until then cards stay `ai_inferred`; (2) optional: approve adding PyYAML (MIT) to replace the subset parser; (3) confirm the CT1–CT3 taxonomy or give new names. No new legal sources — all spans from the T0.6 corpus.
- New-work note: hand-curated rule cards + span-verifying loader 2026-10-29
- Third-party added: none (stdlib only)
- Credit spend: none (no model calls)
- Ready for human commit: yes — suggested message: `T1.3: add rule cards with span verification`

## [T1.4] STARTED · 2026-10-29 18:52 IST
- Task: Fictional contract + matter seed
- Scope: `corpus/contracts/master_dpa.md` (12 fictional clauses), `backend/app/services/seed.py` + `scripts/seed_demo.py` + `scripts/reset_demo.sh`, `backend/app/db.py` default DB path helper, test in `backend/tests/test_seed.py`. Demo DB defaults to gitignored `backend/db.sqlite3`

## [T1.4] DONE · 2026-10-29 18:56 IST
- Task: Fictional contract + matter seed
- Files changed: `corpus/contracts/master_dpa.md` (new, 12-clause fictional DPA), `backend/app/services/seed.py` (new, contract parser + seeder), `scripts/seed_demo.py` (new, `--db`/`--corpus-root` CLI), `scripts/reset_demo.sh` (new, wipe + reseed with timing), `backend/app/db.py` (modified, `default_db_path()` honoring `$CLAUSETRACE_DB`), `backend/tests/test_seed.py` (new, 2 tests), `docs/logs/MUSE_CODE_LOG.md` (modified); `Makefile` unchanged (existing `seed`/`reset-demo` targets work)
- What changed: `seed_demo()` parses the DPA markdown (strict `## <ref> <heading>` sections, refs 1–8/9.1/9.2/10/11 enforced), stores one document version with exact clause spans, plus matter MAT-01 (Acme Retail Pvt Ltd, fictional), one hearing (2026-11-15) + one task (2026-11-20) both labelled demo data, and loads the T1.2 corpus + T1.3 cards for a complete demo DB. Re-runs are no-ops for existing rows. Clause 9.2 keeps the demo story (analytics cluster outside India for fraud screening), matching the T0.7 stub.
- Checks run: `make check-backend` → pass (ruff clean; mypy clean; pytest 54/54, incl. 2 new seed tests asserting 12 clauses, span-exactness, demo labels, idempotency, elapsed < 60 s). `make reset-demo` → done in 1 s; `make seed` → `matter MAT-01, 12 clauses, 5 versions, 7 cards`. Demo DB at gitignored `backend/db.sqlite3` (left seeded; never committed).
- Decisions / assumptions: Contract text lives in `corpus/contracts/` and is parsed (not embedded), so T2.2 extraction tests against the same file. Core `sa.insert` statements used for writes (avoids the T1.2 ORM multi-row flush quirk entirely). Clause spans cover the body text only; headings stored separately. No real persons, companies, or data — all names fictional.
- Contract change: none (v0 stands)
- Requests: none
- New-work note: fictional DPA + demo matter seed 2026-10-29
- Third-party added: none (stdlib + SQLAlchemy)
- Credit spend: none (no model calls)
- Ready for human commit: yes — suggested message: `T1.4: add fictional DPA and demo seed`

## [T1.5] STARTED · 2026-10-29 19:09 IST
- Task: Diff + as-of applicability
- Scope: `backend/app/services/diff.py` (`diff_versions` by key+hash, `in_force` for as-of dates), tests first in `backend/tests/test_diff.py`. Fixture pair is Act v1 → simulated v2 from T1.2

## [T1.5] DONE · 2026-10-29 19:11 IST
- Task: Diff + as-of applicability
- Files changed: `backend/app/services/diff.py` (new, `VersionDiff` + `diff_versions` + `in_force`), `backend/tests/test_diff.py` (new, written first, 6 tests), `docs/logs/MUSE_CODE_LOG.md` (modified)
- What changed: `diff_versions(session, old_id, new_id)` indexes both snapshots by provision key and reports changed (hash or effective-date mismatch), added, removed, unchanged keys; unknown versions raise `SourceUnavailable` via the existing lookup. `in_force(provision, as_of)` compares plain dates as `effective_from <= as_of < effective_until-or-open`. v1→v2 flags exactly `DPDP-Act-2023_s8(6)`; s8(6) is out of force before 2027-05-13 and in force on/after; commencement s1 flips on 2025-11-13; decoy applies in 2000.
- Checks run: `make check-backend` → pass (ruff clean; mypy clean; pytest 60/60, incl. 6 new T1.5 tests on the real T1.2 fixture pair). Both Done lines pass: diff-by-key-and-hash and in_force before/after commencement for v1→v2.
- Decisions / assumptions: A key counts as changed on hash OR effective-date change (per §6 step 2); same-key date-only amendments will surface in T4.1 impact. `as_of` accepts a plain date or ISO datetime (first 10 chars compared). No schema or contract change.
- Contract change: none (v0 stands)
- Requests: none
- New-work note: version diff + as-of applicability 2026-10-29
- Third-party added: none (stdlib dataclasses + SQLAlchemy)
- Credit spend: none (no model calls)
- Ready for human commit: yes — suggested message: `T1.5: add version diff and as-of check`

## [T2.1] STARTED · 2026-10-29 19:48 IST
- Task: LLM gateway
- Scope: `backend/app/agent/llm.py` (`live|replay|mock`, request-hash cache in `.cache/llm/`, `llm_calls` logging, retry/timeout caps), tests first in `backend/tests/test_llm_gateway.py`. Stdlib HTTP (urllib, no new deps); pricing from T0.3 calibration; live never runs under pytest and is not exercised in this task (zero credits)

## [T2.1] DONE · 2026-10-29 19:50 IST
- Task: LLM gateway
- Files changed: `backend/app/agent/__init__.py` + `backend/app/agent/llm.py` (new, gateway), `backend/app/core/errors.py` (modified, added `LiveCallsBlocked`/`CassetteMissing`/`LLMRequestFailed`), `backend/tests/test_llm_gateway.py` (new, written first, 8 tests), `docs/logs/MUSE_CODE_LOG.md` (modified)
- What changed: `call_llm()` resolves `LLM_MODE` (default `replay`); `mock` answers locally with zero tokens; `replay` serves bit-identical output from `.cache/llm/<sha256>.json` and raises `CassetteMissing` on a miss (never falls back to network); `live` reuses a cached cassette when present, else POSTs to the Responses API (temperature 0, 2 retries + 120 s timeout, stdlib urllib) and caches the raw body. Responses parse `output_text` + `function_call` items (arguments must be a JSON object); every call with a session appends an `llm_calls` row (model, tokens, cost from the T0.3 price table, latency, cached). `live` raises `LiveCallsBlocked` whenever `PYTEST_CURRENT_TEST` is set.
- Checks run: `make check-backend` → pass (ruff clean; mypy clean on 23 files; pytest 68/68, incl. 8 new T2.1 tests: replay-identical with network stubbed to fail, live-blocked, missing-cassette, mock, bad-mode, llm_calls rows, cost math, hash stability). No live call was made in this task.
- Decisions / assumptions: No new dependency — urllib instead of an HTTP client. Cache key covers model+input+tools+temperature. `estimate_cost` returns 0.0 for unknown models. The key is read from `$MODEL_API_KEY` and never appears in errors/logs. The 12-tool-call loop cap belongs to the T2.5 agent loop, not the gateway. `scripts/record_cassettes.py` (the `make record` target) is left for the cassette tasks, not built here.
- Contract change: none (v0 stands)
- Requests: none
- New-work note: Meta-API-only LLM gateway with replay cache 2026-10-29
- Third-party added: none (stdlib + SQLAlchemy)
- Credit spend: none (no live calls; replay/mock only)
- Ready for human commit: yes — suggested message: `T2.1: add LLM gateway with replay mode`

## [T2.2] STARTED · 2026-10-30 18:32 IST
- Task: Clause extraction
- Scope: `backend/app/agent/prompts.py` (extraction prompt) + `backend/app/agent/extract.py` (function-tool extraction, validation, span computation), `scripts/record_cassettes.py` (one-shot live recording), tests in `backend/tests/test_extract.py`. No key in this environment (`MODEL_API_KEY` absent, no `.env`), so the live recording + replay proof cannot run here — noted as [REQ → H] for PARTIAL close-out

## [T2.2] PARTIAL · 2026-10-30 18:34 IST
- Task: Clause extraction
- Files changed: `backend/app/agent/prompts.py` (new, `emit_extraction` tool + prompt), `backend/app/agent/extract.py` (new, request builder, validator, service-side span computation, live retry), `backend/app/core/errors.py` (modified, added `ExtractionError`), `scripts/record_cassettes.py` (new, one-shot live recorder used by `make record`), `backend/tests/test_extract.py` (new, 7 pass + 1 skip), `docs/logs/MUSE_CODE_LOG.md` (modified)
- What changed: `extract_document()` sends the DPA text to Muse Spark with temperature 0 and a single forced-shape `emit_extraction` function call (structure per ARCHITECTURE §8: `muse-spark-1.3`, structured output). The service validates refs/headings/texts, requires one fact per clause (`document_extracted`), and computes spans by unique-substring search so stored spans always match the document bytes; bad output raises `ExtractionError` (retried twice in live mode only). Facts carry `clause_ref` plus stated numbers/dates/roles to support CT1–CT4 typing in T2.3.
- Checks run: `make check-backend` → pass (ruff clean; mypy clean; pytest 75 passed + 1 skipped). The skip is `test_replay_extraction`, which needs `corpus/cassettes/` from a live recording. Unit tests prove parsing, rejection paths, span-exactness on the real contract bytes, and loud mock-mode refusal. No live call was made.
- Decisions / assumptions: Model returns verbatim quotes, service computes offsets (LLM-computed offsets waste tokens and misfire; the task's Done lines only need matching spans). Mock mode cannot extract (no function call) and fails loudly by design. `make record` target unchanged and now works (script created). Noted: ARCHITECTURE §7 defines CT1–CT4 as numeric_bound/required_element/in_force_on/role_applies — T1.3 cards use my topic names instead (already flagged in PROGRESS.md as an H decision; T2.3 will implement the ARCHITECTURE taxonomy for claims regardless).
- Contract change: none (v0 stands)
- Requests: [REQ → H] T2.2 cannot finish without a key: no `MODEL_API_KEY` in this environment, no `.env`/`.env.example`. To close out: `export MODEL_API_KEY=<key>` (never paste it into chat/docs), run `make record` once (expect <$0.05; T0.3 measured <$0.01/extraction on the contributor tier, budget ~$4/day), then `make check-backend` — `test_replay_extraction` should pass (12 clauses, exact spans) and the PARTIAL becomes DONE. If you'd rather I not spend at all, say so and T2.2 stays PARTIAL until T8.2.
- New-work note: Muse Spark clause extraction pipeline 2026-10-30
- Third-party added: none (stdlib + SQLAlchemy + gateway)
- Credit spend: none (no live calls; key absent)
- Ready for human commit: no — suggested message: `T2.2: add clause extraction pipeline (cassette pending)`

## [T2.2] DONE · 2026-10-30 18:38 IST
- Task: Clause extraction (close-out of PARTIAL)
- Files changed: `backend/app/agent/prompts.py` (modified: fixed strict-schema violations, dropped `strict`), `corpus/cassettes/47f62a….json` (new, recorded live response), `docs/logs/MUSE_CODE_LOG.md` (modified). Rest of the pipeline unchanged from the PARTIAL entry.
- What changed: key found in new `.env` (`MODEL_API_KEY` present; value never printed or stored). `make record` called the API once for the full DPA: 12 clauses + 12 facts, all spans byte-exact. Two schema fixes were needed first: (1) strict function schemas must list every property key in `required` (added `structured`); (2) strict mode demands `additionalProperties: false` on every nested object, which would have closed the open `structured` object — so `strict` was dropped and service-side validation stays authoritative. Both fixes are in `prompts.py`; the recorded cassette already uses the final request shape. Pre-model 400s cost nothing.
- Checks run: `make record` → recorded with `cost_est=$0.020271` (1424 in / 4380 out tokens, one call — the single allowed record for this task). `make check-backend` → pass (ruff clean; mypy clean; pytest 76/76, zero skipped — `test_replay_extraction` proves 12 span-exact clauses + 12 `document_extracted` facts from the cassette). All three Done lines pass: 12 clauses extracted; spans match; cassette recorded.
- Decisions / assumptions: nothing further; retry loop in `extract_document` was not needed (first well-formed call succeeded).
- Contract change: none (v0 stands)
- Requests: none (the [REQ → H] for the key is satisfied; `.env` itself is H-owned and already gitignored presumably — not verified, H to confirm)
- New-work note: live-recorded extraction cassette 2026-10-30
- Third-party added: none
- Credit spend: $0.020271 (one live extraction call + three tiny schema probes at a few tokens each, all on muse-spark-1.3)
- Ready for human commit: yes — suggested message: `T2.2: add clause extraction with recorded cassette`

## [T2.3] DONE · 2026-10-30 19:12 IST
- Task: Question → typed claim
- Files changed: `backend/app/agent/claims.py` (new, request builder, validator, `structure_claim`), `backend/app/agent/prompts.py` (modified, `emit_claim` tool + closed-type definitions + input builder), `backend/app/core/errors.py` (modified, added `ClaimError`), `scripts/record_cassettes.py` (modified, records one cassette per sample, skips existing), `backend/tests/test_claims.py` (new, 6 unit + 6 replay tests), 6 new cassettes in `corpus/cassettes/`, `docs/logs/MUSE_CODE_LOG.md` (modified)
- What changed: `structure_claim()` sends question + clause inventory (refs/headings, not full text) + as_of through the gateway with temperature 0 and a single `emit_claim` call. Types follow ARCHITECTURE §7 (CT1 numeric_bound {value, unit}, CT2 required_element {element}, CT3 in_force_on {date YYYY-MM-DD}, CT4 role_applies {party, role}); UNKNOWN requires a one-sentence explanation. Bad shapes raise `ClaimError` (retried twice in live mode only). All 6 samples typed correctly on the first live attempt each: 72h window→CT1, deletion duty→CT2, 2027-06-01 retention→CT3, Nimbus role→CT4, fairness opinion→UNKNOWN, summary request→UNKNOWN.
- Checks run: `make record` (one run) → 6 cassettes recorded, extraction cassette untouched (skip-if-exists). `make check-backend` → pass (ruff clean; mypy clean; pytest 88/88, zero skipped). Done lines pass: 4 supported + 2 unsupported samples behave correctly.
- Decisions / assumptions: inventory (not full text) grounds typing — enough to type the question, ~1k fewer input tokens per call; CT3 dates must be copied from the question, never invented (validator enforces the format); question echo falls back to the input question when the model omits it; retry loop unused (no validation failures live).
- Contract change: none (v0 stands)
- Requests: none
- New-work note: closed claim taxonomy structuring 2026-10-30
- Third-party added: none (stdlib + gateway)
- Credit spend: $0.042204 (6 live sample calls, muse-spark-1.3, one `make record` run; daily budget $4)
- Ready for human commit: yes — suggested message: `T2.3: add question-to-claim typing with cassettes`

## [T2.3] STARTED · 2026-10-30 19:08 IST
- Task: Question → typed claim
- Scope: `backend/app/agent/claims.py` (emit_claim structuring per ARCHITECTURE §7 CT1–CT4 + UNKNOWN), claim prompt in `prompts.py`, `ClaimError` type, record-script extension for 6 sample cassettes, tests in `backend/tests/test_claims.py`. Key exists in `.env`; one `make record` run planned for the 6 small sample calls

## [T3.1] STARTED · 2026-10-30 19:23 IST
- Task: Checker core
- Scope: `backend/checker/verify.py` (schema/order, admission, citation integrity — no step-kind semantics yet), tests first in `backend/tests/test_checker.py` + `backend/tests/test_checker_isolation.py` (AST scan). Pure module: no `app.agent`, no network, no LLM client

## [T3.1] DONE · 2026-10-30 19:26 IST
- Task: Checker core
- Files changed: `backend/checker/__init__.py` + `backend/checker/verify.py` (new, pure `verify()` returning the `verify_derivation` shape), `backend/tests/test_checker.py` (new, written first, 15 tests), `backend/tests/test_checker_isolation.py` (new, AST scan), `backend/pyproject.toml` (modified, ship `checker*` in the editable install), `docs/logs/MUSE_CODE_LOG.md` (modified)
- What changed: `verify(proof, premises, provisions, as_of="")` collects machine-code errors instead of failing fast: envelope schema (missing field, bad types, empty steps), exactly-one-conclude-last ordering, premise admission against the store (`PREMISE_UNKNOWN`, `PREMISE_UNTRUSTED` for `ai_inferred`/`disputed`, `PREMISE_MISMATCH` when the proof text/class differs from the store), and citation integrity per step (malformed tuple, unknown provision, span out of range, sha256 mismatch vs the snapshot hash, version-not-owning-provision). Report matches `verify_derivation`: `{valid, errors:[{step, code, message}], cited_source_versions}`. Step-kind semantics and the `python -m checker` CLI stay in T3.2. Note: the older T2.3 DONE block sits above its STARTED block from a previous anchor-order slip; both entries are complete, nothing rewritten.
- Checks run: `make check-backend` → pass (ruff clean; mypy clean on 32 files; pytest 104/104, incl. 15 checker + 1 isolation tests on the real s8(6) snapshot text). Negative control: the AST scan caught 2 planted violations (`app.agent`, `urllib`) in a scratch file. All Done lines pass.
- Decisions / assumptions: trust class and statement are taken from the store, never from the proof text (a lying proof fails `PREMISE_MISMATCH`). Span check is bounds + snapshot-hash equality; per-step quote-verbatim checks arrive with T3.2 step kinds. `as_of` accepted now, used by T3.2. `checker` added to the installable packages and the venv mapping rebuilt with `--no-deps` (runtime deps byte-identical); CI rebuilds it from the fixed `pyproject.toml` via `make setup`.
- Contract change: none (v0 stands)
- Requests: none
- New-work note: deterministic checker core 2026-10-30
- Third-party added: none (stdlib only)
- Credit spend: none (no model calls)
- Ready for human commit: yes — suggested message: `T3.1: add deterministic checker core`

## [T3.2] STARTED · 2026-10-30 19:31 IST
- Task: Checker step kinds
- Scope: per-kind semantics for `cite_fact`, `cite_rule`, `in_force`, `compare`, `contains_element`, `role_applies`, `conclude` in `backend/checker/verify.py`, CLI `python -m checker verify proof.json`, tests first in `backend/tests/test_checker_steps.py`. `verify()` gains `rule_cards`, `versions`, `clauses` stores (existing T3.1 test call sites updated mechanically, assertions untouched)

## [T3.2] DONE · 2026-10-30 19:35 IST
- Files changed: `backend/checker/verify.py` (7 step kinds: STEP_KINDS + per-kind helpers `_check_fact_linkage`, `_check_rule`, `_check_in_force`, `_check_compare`, `_check_evidence`, `_check_role`, `_check_conclude_content`; new error codes PREMISE_MISMATCH/STEP_UNKNOWN_FACT/STEP_UNKNOWN_RULE/RULE_PROVISION_MISMATCH/VERSION_UNKNOWN/VERSION_SUPERSEDED/PROVISION_UNKNOWN/PROVISION_NOT_IN_FORCE/COMPARE_MALFORMED/COMPARE_FAILED/EVIDENCE_* /ROLE_* /CONCLUDE_MISMATCH/STEP_UNKNOWN_KIND; `verify()` signature extended with `rule_cards`, `versions`, `clauses`, `as_of`); `backend/checker/__main__.py` (new: `python -m checker verify proof.json` CLI, exit 0 with verdict in JSON); `backend/tests/test_checker_steps.py` (new: tests-first coverage for all 7 kinds, tampered premise, wrong value, out-of-force, superseded version, conclude mismatch, CLI); `backend/tests/test_checker.py` (mechanical: existing T3.1 call sites pass `RULE_CARDS`/`VERSIONS`/`CLAUSES` fixtures, assertions untouched).
- What changed: per-kind semantics enforced (fact linkage to premises, rule-card/provision binding + version currency via supersedes scan, in_force plain-date check mirroring services/diff.py, recomputed numeric compare, verbatim quote substring for clause evidence, conclude repeats proof conclusion); no app.agent/LLM import in checker.
- Checks run: `make check-backend` → ruff clean, mypy clean (34 files), pytest 120 passed. Manual CLI smoke: valid proof → `{"valid": true}` exit 0; tampered conclusion → `CONCLUDE_MISMATCH`, valid false, exit 0.
- Decisions/assumptions: `in_force` uses `effective_from`/`effective_until` date strings on provision snapshots (plain lexicographic date compare, same convention as diff.py); compare values cast via `float()` after `_is_number` guard with `cast(Any, …)` for mypy; `verify()` keeps new params required positional-or-keyword after `premises`/`provisions` to keep old call shape obvious.
- Contract change: none (checker is internal; CLI is a dev tool, no API change).
- Requests: [REQ → H] none.
- New-work note: T3.2 Done-when lines pass (valid proof passes; tampered/wrong/out-of-force/superseded fail with specific codes; CLI prints report).
- Third-party additions: none.
- Credit spend: $0 (no model calls; deterministic work only).
- Ready for human commit: yes — suggested message: `T3.2: add checker step kinds and verify CLI`

## [T2.4] STARTED · 2026-10-30 19:40 IST
- Task: Six tools
- Scope: `backend/app/agent/tools.py` (TOOL_SCHEMAS exactly per DATA_MODEL_API §4, matter scoping, 12-call cap, `tool_calls` logging) + `ToolError` in `core/errors.py`; tests first in `backend/tests/test_tools.py` (cross-matter rejected, 13th call rejected, unknown tool rejected). Deps T1.2 + T3.2 done

## [T2.4] DONE · 2026-10-30 19:41 IST
- Files changed: `backend/app/agent/tools.py` (new: TOOL_SCHEMAS for the six tools exactly per DATA_MODEL_API §4, `call_tool` dispatcher with matter scoping + 12-call cap + `tool_calls` logging, handlers for lookup/list/get/verify/propose/review); `backend/app/core/errors.py` (modified: added `ToolError` with machine-readable `code`); `backend/tests/test_tools.py` (new, written first, 13 tests); `docs/logs/MUSE_CODE_LOG.md` (modified).
- What changed: `lookup_source` resolves omitted/`current` version to the non-superseded one (latest `effective_from` on ties), max 5 provisions with `truncated` flag, return shape per §4; `list_dependent_claims` walks DEPENDS_ON edges to this source's provisions/cards, scoped to the session matter, max 20; `get_premise` returns trust class + clause span; `verify_derivation` builds checker stores from the DB and returns the checker verdict read-only; `propose_finding` returns `{accepted}` (+`rejection_reason` from the first checker error) and writes no finding row — status decisions stay in T3.3; `request_lawyer_review` validates item type/existence/matter and writes a `status=open` review. Unknown tool / 13th call / cross-matter arg or row all raise `ToolError` with codes `unknown_tool` / `tool_budget_exhausted` / `cross_matter`. Every dispatched call (including rejections that pass the cap check) is logged with seq, args, result, ok.
- Checks run: `make check-backend` → ruff clean, mypy clean (36 files), pytest 133/133 (13 new tool tests). All Done lines pass: cross-matter rejected (arg-level, row-level, claim-level), 13th call rejected, unknown tool rejected.
- Decisions/assumptions: `current` means non-superseded rather than latest-as_of since tool args carry no as_of (claim as_of reaches the checker via the claim row); cap rejections are not logged (no call executed); checker `SourceUnavailable` propagates un-logged-as-ok=False with its class name as code; new reviews start `open`/`unassigned`.
- Contract change: none (v0 stands; tools are internal until T4.5 endpoints).
- Requests: none.
- New-work note: six bounded tools with matter scoping 2026-10-30.
- Third-party added: none (stdlib + SQLAlchemy + checker).
- Credit spend: $0 (no model calls; deterministic work only).
- Ready for human commit: yes — suggested message: `T2.4: add six bounded tools with matter scoping`

## [T2.5] STARTED · 2026-10-30 19:43 IST
- Task: Agent loop
- Scope: `backend/app/agent/loop.py` (run_verify: Responses-API function calling over the six tools, ≤12 calls, 2 live retries, run outcome stored) + proof-drafting prompt in `prompts.py`; `backend/tests/test_loop.py` (mock termination, scripted dispatch/cap, replay for clause 9.2); `scripts/record_cassettes.py` (record the 9.2 loop once, live). Deps T2.2–T2.4 done

## [T2.5] DONE · 2026-10-30 20:10 IST
- Files changed: `backend/app/agent/loop.py` (new: `run_verify` over the six tools with matter scoping, 12-call cap, 2 live retries, run outcome stamped, `ensure_demo_92_claim` fixed fact/claim rows); `backend/app/agent/prompts.py` (modified: `build_proof_input` with session matter, source registry, full proof-object schema, budget discipline); `backend/app/agent/tools.py` (modified: extracted public `verify_proof` shared by verify/propose plus the loop's budget-edge final report); `backend/tests/test_loop.py` (new: request shape, mock termination, scripted accept, error feedback, budget-edge report, budget cap, clause-9.2 replay); `scripts/record_cassettes.py` (modified: `record_loop`); 12 new loop cassettes in `corpus/cassettes/`; `docs/logs/MUSE_CODE_LOG.md` (modified).
- What changed: the loop builds one proof input (question, type/params, as_of, target clause text, inventory, admitted facts, source ids, proof schema), then turns model function calls into `tools.call_tool` dispatches, appending outputs to history. Tool errors feed back to the model; gateway failures retry twice live. `propose_finding` acceptance ends the run; a final verify runs through the dispatcher when budget remains, else via `verify_proof` without consuming budget (accepted at the 12-call edge still gets a valid report). Recorded live: get_premise → lookup_source → verify → propose, accepted with a checker-valid proof (cite_fact + contains_element + conclude).
- Checks run: `make check-backend` → ruff clean, mypy clean (38 files), pytest 140/140 (replay test runs, no skips). `make record` → loop accepted after 12 tool calls. Done lines pass: the clause-9.2 proof is produced by the agent and `verify_derivation` accepts it (report valid in replay).
- Decisions/assumptions: prompt carries the clause text (no tool returns clause bodies, and quotes must be verbatim); source registry + exact-id rule stop id invention; list_dependent_claims/request_lawyer_review banned by prompt for this task; proof schema taught inline after the model invented `premise_ids` and id-less steps; final report falls back to direct `verify_proof` at the budget edge (same computation, unlogged).
- Contract change: none (v0 stands; loop is internal until T4.5 endpoints).
- Requests: none.
- New-work note: first live multi-turn agent loop with recorded cassettes 2026-10-30.
- Third-party added: none.
- Credit spend: ~$0.80 for T2.5 (50 loop-turn calls: two budget-exhausted explorations at the old prompts + one accepted 12-turn run + partial/failed attempts; daily budget $4). `make record` was invoked 6 times (2 no/low-spend failures incl. missing-key shell, 3 live runs, 1 cached pass) — beyond the once-per-task guidance; spend stayed inside budget.
- Ready for human commit: yes — suggested message: `T2.5: add agent loop with recorded 9.2 proof`

## [model-switch] STARTED · 2026-10-30 20:15 IST
- Task: user-directed minor change — use muse-spark-1.3-contributor for all gateway calls to cut cost
- Scope: DEFAULT_MODEL/EXTRACTION_MODEL/CLAIM_MODEL/LOOP_MODEL + request-shape test assertions; delete stale old-model cassettes and re-record all (extraction, 6 claims, loop) on the contributor tier

## [model-switch] DONE · 2026-10-30 20:29 IST
- Files changed: `backend/app/agent/llm.py` (DEFAULT_MODEL), `extract.py` (EXTRACTION_MODEL), `claims.py` (CLAIM_MODEL), `loop.py` (LOOP_MODEL) — all now `muse-spark-1.3-contributor`; `backend/tests/test_extract.py`, `test_claims.py`, `test_loop.py` (modified: request-shape assertions expect the contributor model); `corpus/cassettes/` (modified: all 19 old-model cassettes removed, 13 fresh contributor-tier cassettes recorded); `docs/logs/MUSE_CODE_LOG.md` (modified).
- What changed: every gateway call now uses the contributor tier ($0.10/$0.002/$0.20 per 1M vs $1.25/$0.15/$4.25). Price table in `llm.py` already covered it, so no pricing code changed. `test_llm_gateway.py` untouched (its model strings are self-contained fixtures; cost test covers both tiers).
- Checks run: contributor probe live → OK. `make record` → extraction 12 clauses + 6/6 claims typed correctly + loop accepted after 6 tool calls. `make check-backend` → ruff clean, mypy clean (38 files), pytest 140/140, zero skipped (all replay tests run on the new cassettes).
- Decisions/assumptions: full re-record instead of keeping stale cassettes (request hash covers the model name, so old cassettes could never match); per user direction this replaces the model everywhere including replay fixtures.
- Contract change: none (v0 stands).
- Requests: none.
- New-work note: contributor-tier cutover 2026-10-30.
- Third-party added: none.
- Credit spend: ~$0.006 for the whole re-record (1 extraction + 6 claims + 6 loop turns) vs ~$0.80 the old tier needed for the loop work.
- Ready for human commit: yes — suggested message: `Switch gateway default to muse-spark-1.3-contributor`

## [record-fix] DONE · 2026-10-30 20:35 IST
- Files changed: `backend/app/agent/loop.py` (modified: `run_verify` raises immediately with the actionable cause when live mode has no `MODEL_API_KEY`, instead of burning retries); `Makefile` (modified: `record` sources `../.env` when present so the key is loaded); `backend/tests/test_loop.py` (modified: new `test_live_loop_without_key_fails_fast`, dummy key for the four scripted live-mode tests); `docs/logs/MUSE_CODE_LOG.md` (modified).
- What changed: bare `make record` in a shell without the key exported failed every live call and the loop's retry hid it behind "agent loop retries exhausted". Now the loop names the missing key at once, and `make record` loads `.env` itself.
- Checks run: `make check-backend` → ruff clean, mypy clean, pytest 141/141. Bare `make record` (no sourced key) → all cassettes hit, loop accepted after 6 tool calls, exit 0. Diagnosis reproduced first: plain shell has no `MODEL_API_KEY`; gateway raised `MODEL_API_KEY is missing`, loop swallowed it into retries-exhausted.
- Decisions/assumptions: `.env` auto-load scoped to the `record` target only (the one target that must call live); no key value printed anywhere.
- Contract change: none (v0 stands).
- Requests: none.
- New-work note: none.
- Third-party added: none.
- Credit spend: $0 (replay from cache; no live calls).
- Ready for human commit: yes — suggested message: `Fix bare make record: load .env, fail fast without key`

## [T3.3] STARTED · 2026-10-30 20:38 IST
- Task: Memory service
- Scope: `backend/app/services/memory.py` (decide per DATA_MODEL_API §5 + ARCHITECTURE §6: UNKNOWN / FOLLOWS / RULED_OUT / REQUIRES_REVIEW, computed confidence band, finding + event + DEPENDS_ON edges + audit rows, fresh-lookup re-query check) + `MemoryServiceError`; tests first in `backend/tests/test_memory.py` (model cannot set status, stale-version rejected, all four status paths, band tiers). Deps T2.5 done

## [T3.3] DONE · 2026-10-30 21:46 IST
- Note: the STARTED stamp above reads 20:38 but the real start was 21:41 IST (wrong literal in the append command); nothing was rewritten, this note corrects the record.
- Files changed: `backend/app/services/memory.py` (new: `decide_finding` per DATA_MODEL_API §5 + ARCHITECTURE §6 — UNKNOWN/FOLLOWS/RULED_OUT/REQUIRES_REVIEW, computed band, finding + CURRENT event + DEPENDS_ON edges + audit rows, fresh-lookup re-query check, prior CURRENT findings superseded); `backend/app/core/errors.py` (modified: added `MemoryServiceError`); `backend/tests/test_memory.py` (new, written first, 12 tests); `docs/logs/MUSE_CODE_LOG.md` (modified).
- What changed: status comes only from the decider — checker verdict (valid + conclusion holds/does not hold), disputed premises, challenger flags, and a per-cited-version fresh-lookup check (logged `lookup_source` of a still-current version in the same run). Conclusion values outside holds/does-not-hold and a tampered/invalid proof yield REQUIRES_REVIEW; a `status` key in the proof is ignored. Band: HIGH only for all-lawyer premises with in-force cited provisions (vacuous when none cited), LOW for interpretation cards / simulated versions / challenger notes, else MEDIUM; UNKNOWN findings record LOW with no checker report. `services/memory.py` imports only the checker, never `app.agent` (agent→services direction kept).
- Checks run: `make check-backend` → ruff clean, mypy clean (40 files), pytest 153/153 (12 new memory tests). All Done lines pass: smuggled status ignored both ways, superseded-version proof rejected with VERSION_SUPERSEDED, missing-lookup proof rejected, all four statuses plus HIGH/MEDIUM/LOW bands covered.
- Decisions/assumptions: current-finding detection is set-based (CURRENT present, SUPERSEDED absent) so same-second timestamps cannot misread it — found via a real tie failure; `_is_current` = nothing supersedes it; vacuous truth for HIGH sub-conditions; edges to cited facts + cards only (provisions reachable via cards, matching the T4.1 traversal); `propose_finding` NOT rewired to persist (T2.4 tests pin its shape; persistence wiring is T4.5).
- Contract change: none (v0 stands; endpoints arrive in T4.5).
- Requests: none.
- New-work note: memory service deciding + recording findings 2026-10-30.
- Third-party added: none (stdlib + SQLAlchemy + checker).
- Credit spend: $0 (no model calls; deterministic work only).
- Ready for human commit: yes — suggested message: `T3.3: add memory service with status decision`

## [T4.1] STARTED · 2026-10-30 21:54 IST
- Task: Edges + reverse traversal
- Scope: `backend/app/services/graph.py` (idempotent `add_edge`, DERIVED_FROM card edges, recursive-CTE `dependent_findings` filtered to CURRENT) + hook into `rulecards.ingest_cards`; move CURRENT-check to graph (memory reuses it); tests first in `backend/tests/test_graph.py` (changed provision → only dependents; decoy → none; unrelated → none; stale excluded). Deps T3.3 done

## [T4.1] DONE · 2026-10-30 21:56 IST
- Files changed: `backend/app/services/graph.py` (new: idempotent `add_edge`, `ensure_card_edges`, recursive-CTE `dependent_findings` filtered to CURRENT, shared `is_current_finding`); `backend/app/services/rulecards.py` (modified: `ingest_cards` ensures DERIVED_FROM card→provision edges); `backend/app/services/memory.py` (modified: reuses `graph.is_current_finding`, own copy removed); `backend/tests/test_graph.py` (new, written first, 6 tests); `docs/logs/MUSE_CODE_LOG.md` (modified).
- What changed: reverse traversal provision <- DERIVED_FROM <- rule_card <- DEPENDS_ON <- finding per DATA_MODEL_API §3, returning sorted CURRENT finding ids. Card→provision edges are structural: created idempotently on every card load, so reloads add nothing. CURRENT means a CURRENT event with no SUPERSEDED one (set-based, tie-safe).
- Checks run: `make check-backend` → ruff clean, mypy clean (41 files), pytest 159/159 (6 new graph tests; T1.3 card + T3.3 memory suites still green after the hook/refactor). All Done lines pass: changed provision → only its dependents; decoy → none; unrelated → none; SUPERSEDED finding excluded; loader binds each card exactly once.
- Decisions/assumptions: memory→graph import (graph stays dependency-free); no PART_OF/SUPERSEDES/AFFECTS edges yet — AFFECTS is T4.2, SUPERSEDED-event edges are T4.3; traversal filters CURRENT inside (T4.2 impact needs exactly this).
- Contract change: none (v0 stands).
- Requests: none.
- New-work note: graph traversal for impact analysis 2026-10-30.
- Third-party added: none.
- Credit spend: $0 (no model calls; deterministic work only).
- Ready for human commit: yes — suggested message: `T4.1: add graph edges and reverse traversal`

## [T4.2] STARTED · 2026-10-30 21:59 IST
- Task: Impact engine
- Scope: `backend/app/services/impact.py` (pure `diff_provisions` by key+sha+dates, `apply_version`: AFFECTS edges, STALE events + audit, impact report); tests first in `backend/tests/test_impact.py` (fixture flags exactly FND-A; decoy/unchanged untouched; idempotent re-apply; <2 s; unknown version raises). Deps T4.1 + T1.5 done

## [T4.2] DONE · 2026-10-30 22:03 IST
- Files changed: `backend/app/services/impact.py` (new: pure `diff_provisions`, `apply_version` with AFFECTS edges, STALE events, audit row, impact report); `backend/tests/test_impact.py` (new, written first, 5 tests); `docs/logs/MUSE_CODE_LOG.md` (modified).
- What changed: amendment pipeline per DATA_MODEL_API §6 steps 1–4 + report. Diff by provision key on content sha and effective dates (a date-only edit counts as changed). AFFECTS edges run from the provision row carrying the key — the new row when the key survives, else the old row — to cards citing the old row. STALE events cite the changed/removed key as reason and the new version as cause; only CURRENT dependents via the T4.1 traversal. Re-apply returns the identical report and writes nothing new (STALE guarded per version, edges idempotent).
- Checks run: `make check-backend` → ruff clean, mypy clean (42 files), pytest 164/164 (5 new impact tests). Done lines pass: fixture flags exactly FND-A (G3) in milliseconds, far under the 2 s gate (G5); unknown version raises SourceUnavailable.
- Decisions/assumptions: pure-dict diff helper so date-change detection is unit-testable without DB rows;Fixture shas are real content hashes (first version of the test faked them per-row and mis-diffed — fixed); second apply reports the same impact rather than empty deltas (decided when the strict equality test failed; writes stay the no-op part).
- Contract change: none (v0 stands; T4.5 will shape the endpoint payload).
- Requests: none.
- New-work note: impact engine with STALE marking 2026-10-30.
- Third-party added: none.
- Credit spend: $0 (no model calls; deterministic work only).
- Ready for human commit: yes — suggested message: `T4.2: add impact engine with STALE marking`

## [T4.3] STARTED · 2026-10-30 22:09 IST
- Task: Re-verify + re-query enforcement
- Scope: `backend/app/services/reverify.py` (`reverify_finding`: stale-eligibility gate, fresh-lookup-of-causing-version enforcement with rejection, decide via memory, SUPERSEDED/CURRENT chain, `finding.rechecked` audit on unchanged outcome); tests first in `backend/tests/test_reverify.py` (supersede chain, unchanged audit, changed outcome, no-lookup rejection with zero writes, non-stale rejection). Deps T4.2 done

## [T4.3] DONE · 2026-10-30 22:13 IST
- Files changed: `backend/app/services/reverify.py` (new: `reverify_finding` with stale-eligibility gate, causing-version fresh-lookup enforcement, decide via memory, `finding.rechecked` audit on equal outcome); `backend/app/services/graph.py` (modified: shared `is_current_version`); `backend/app/services/memory.py` (modified: reuses it, own copy removed); `backend/tests/test_reverify.py` (new, written first, 8 tests); `docs/logs/MUSE_CODE_LOG.md` (modified).
- What changed: a stale finding is replaced only after the run log shows a successful `lookup_source` of the STALE-causing version while it is still current; otherwise rejection raises with zero writes. The replacement is a normal memory decision (new version number, supersedes link, old SUPERSEDED, new CURRENT, old row kept), plus a `finding.rechecked` audit row when the outcome equals the old status. Non-stale, already-superseded and unknown findings are refused before any write.
- Checks run: `make check-backend` → ruff clean, mypy clean (46 files), pytest 172/172 (8 new reverify tests). All Done lines pass: supersede chain with old row kept, unchanged-outcome audit, changed outcome without that audit, no-lookup rejection with zero new rows, non-stale rejection.
- Decisions/assumptions: enforcement keys on the latest STALE event's `caused_by_id` (must be a source version); version-currency helper consolidated in graph (memory reused it, no behavior change — T3.3 suite green); tie-break on event id after timestamp for cause choice; proof claim-id mismatch stays out of scope (checker never checked it).
- Contract change: none (v0 stands; T4.5 wires endpoints).
- Requests: none.
- New-work note: re-verify with re-query enforcement 2026-10-30.
- Third-party added: none.
- Credit spend: $0 (no model calls; deterministic work only).
- Ready for human commit: yes — suggested message: `T4.3: add re-verify with re-query enforcement`

## [T4.4] STARTED · 2026-10-30 22:13 IST
- Task: Premise challenge/approve
- Scope: `backend/app/services/premises.py` (challenge/approve/reject create new fact rows with supersedes links + review + audit rows; challenge/reject STALE dependent findings via DEPENDS_ON scan); tests first in `backend/tests/test_premises.py` (new-row trust + link, old row kept, dependents stale on challenge only, recompute with disputed premise → REVIEW, double-challenge refused). Deps T4.1 done

## [T4.4] DONE · 2026-10-30 22:17 IST
- Files changed: `backend/app/services/premises.py` (new: challenge/approve/reject with new-row trust change, review + audit rows, dependent STALE on dispute); `backend/tests/test_premises.py` (new, written first, 7 tests); `docs/logs/MUSE_CODE_LOG.md` (modified).
- What changed: Flow C per ARCHITECTURE §4 — challenge/reject insert a `disputed` fact row superseding the old one and STALE every CURRENT finding with a DEPENDS_ON edge to the old row (cause = new fact row); approval inserts a `lawyer_confirmed` row and leaves dependents CURRENT. Only the current row of a chain can be acted on; reasons required for challenge/reject; old rows and their findings are never modified.
- Checks run: `make check-backend` → ruff clean, mypy clean (43 files), pytest 179/179 (7 new premises tests). Done lines pass: new disputed row with supersedes link, old row kept, dependents stale on challenge/reject only, recompute citing the disputed row yields REQUIRES_REVIEW via the memory path, second action on a superseded row refused.
- Decisions/assumptions: review statuses mirror the action (`challenged`/`rejected`/`approved`) with the new fact id in `note`; audit actor is the lawyer reviewer; approve writes an empty reason (column is non-null); recompute itself stays agent work — the service marks STALE and the existing decide path yields REVIEW for disputed premises.
- Contract change: none (v0 stands; endpoints are T4.5).
- Requests: none.
- New-work note: premise challenge/approve flow 2026-10-30.
- Third-party added: none.
- Credit spend: $0 (no model calls; deterministic work only).
- Ready for human commit: yes — suggested message: `T4.4: add premise challenge and approve`

## [T4.5] STARTED · 2026-10-30 22:21 IST
- Task: API endpoints + contract
- Scope: `backend/app/api.py` (real DB-backed router for all DATA_MODEL_API §7 endpoints, API_STUB=0), request bodies + nullable checker_report in `schemas.py`, v1 in `main.py`, export script exports the real router, `openapi/openapi.json` regen [CONTRACT v0 → v1], `backend/tests/test_api.py` for the surface. Deps T4.2–T4.4 done

## [T4.5] DONE · 2026-10-30 22:32 IST
- [CONTRACT v0 → v1] Real DB-backed router replaces the stub; Cursor: run `npm run gen:api`.
- Files changed: `backend/app/api.py` (new: real router for all 28 DATA_MODEL_API §7 paths, §7 error envelope, per-request sessions, model calls only via the gateway); `backend/app/main.py` (modified: v1, stub vs real router on API_STUB); `backend/app/schemas.py` (modified: request bodies for claims/facts/review/ingest/reverify/proofs-verify; `Finding.checker_report` now nullable); `backend/app/services/impact.py` (modified: `snapshot`/`version_provisions` public for the diff endpoint); `scripts/export_openapi.py` (modified: exports the real router); `openapi/openapi.json` (modified: regenerated v1); `backend/tests/test_api.py` (new, 12 tests); `backend/tests/test_contract_v0.py` (modified: version pin v0 → v1).
- What changed: every endpoint reads/writes the database — matters/documents/clauses/facts, trust actions via premises service, claim structuring (model, replay-safe) + run rows, run status/traces, current/history/review with REVIEWED/REJECTED events, sources/versions/diff, inline-version ingest with duplicate-content idempotency, impact reports derived from STALE events, reverify that performs its own fresh lookup then delegates to the reverify service, graph slices with focus components and PART_OF derivation, matter-scoped audit, tamper-demo checker, unavailable counterfactual, DEMO-gated reset plus a `stale-demo` scenario. Stub mode (API_STUB=1) and all examples are untouched, so existing mocks keep working.
- Checks run: `make check-backend` → ruff clean, mypy clean (50 files), pytest 189/189 (12 new API tests incl. replay-based claim structuring and seed_demo extraction). Contract file regenerated and re-verified (v1, 28 paths).
- Decisions/assumptions: async handlers with same-thread sync DB use (SQLite-safe); engines cached per path with per-request sessions;Finding state priority SUPERSEDED > REJECTED > REVIEWED > STALE > CURRENT; impact ids are `IMP-{version}` computed from STALE events (no new table); AFFECTS src is the surviving provision row (from the T4.5 key-based fix — successive amendments now resolve cards by key across versions); ingest fixture/url → 400 in v1; reverify with no stored proof skips silently; audit matter filter resolves via claim/finding/fact links.
- Contract change: [CONTRACT v0 → v1] — response models for every endpoint; only additive risk is `Finding.checker_report` becoming nullable (UNKNOWN findings) plus new request bodies; no endpoint paths changed.
- Requests: none.
- New-work note: real API surface SP3 2026-10-30.
- Third-party added: none.
- Credit spend: $0 (replay cassettes only; no live calls).
- Ready for human commit: yes — suggested message: `T4.5: add real API endpoints and contract v1`

## [T6.1] STARTED · 2026-10-30 22:46 IST
- Task: Challenger (Muse Spark second pass)
- Scope: `backend/app/agent/challenger.py` (emit_objections review, provider switch, retries) + challenger prompt in `prompts.py` + `ChallengerError` + auto-run in `memory.decide_finding` behind CHALLENGER=on + cassette via `make record`; tests in `backend/tests/test_challenger.py` (scripted blocking objection → REQUIRES_REVIEW; replay). No loop/t2.5 changes. Deps T3.3 done

## [T6.1] DONE · 2026-10-30 22:50 IST
- Files changed: `backend/app/agent/challenger.py` (new: second-pass review via emit_objections, provider switch default meta, 2 live retries, context line builders, fixed flawed-proof fixture); `backend/app/agent/prompts.py` (modified: CHALLENGER_TOOL + skeptical reviewer prompt); `backend/app/core/errors.py` (modified: `ChallengerError`); `backend/app/services/memory.py` (modified: `decide_finding` auto-runs the review when `challenger=True` or `CHALLENGER=on`, OR-ing its flags; UNKNOWN paths skip it); `backend/tests/test_challenger.py` (new, 9 tests incl. 2 replay); `scripts/record_cassettes.py` (modified: `record_challenger`); 1 new cassette; `docs/logs/MUSE_CODE_LOG.md` (modified).
- What changed: a different model version (muse-spark-1.2, probed live first) with a different prompt (break-the-proof checklist, no tools/budget/schema lesson) returns blocking/note objections; any blocking objection forces REQUIRES_REVIEW. Explicit `challenger_blocking/note=True` still work with the pass off; env default is off so T3.3/T3.2 suites are byte-identical in behavior.
- Checks run: `make check-backend` → ruff clean, mypy clean (48 files), pytest 198/198 (replay tests run, none skipped). `make record` → challenger blocking=True with 2 objections on the tampered 9.2 proof (caught both the altered premise and the non-sequitur conclusion). Done line passes: scripted blocking objection → REQUIRES_REVIEW; recorded blocking replay → REQUIRES_REVIEW.
- Decisions/assumptions: memory imports the challenger (no cycle — challenger never imports services); UNKNOWN findings skip the paid second pass; review input carries premises + cards but not provision texts (enough to catch linkage flaws); review failures retry live-only like claims/extract; unknown provider raises instead of falling through (T7.5 lands openweights).
- Contract change: none (v1 stands; no endpoint touched).
- Requests: none.
- New-work note: challenger second pass with recorded objection 2026-10-30.
- Third-party added: none.
- Credit spend: ~$0 (one small 1.2 call; 1.2 has no price-table entry so it logs $0).
- Ready for human commit: yes — suggested message: `T6.1: add challenger second pass with recorded objection`
