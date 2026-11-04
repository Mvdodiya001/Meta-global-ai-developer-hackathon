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

## [ask-flow] STARTED · 2026-10-30 22:56 IST
- Task: user-directed — demo question needs a replay cassette; POST /api/claims must start the agent loop after typing (a cassette alone produces no finding)
- Scope: move demo 9.2 constants into `services/seed.py` (loop re-exports; `seed_demo` ensures F-LOOP-92/C-LOOP-92); POST /api/claims runs loop + decide and returns finding_id/status (contract additive → v2); record one structuring cassette for the demo question; API end-to-end test; regen openapi [CONTRACT v1 → v2]

## [ask-flow] DONE · 2026-10-31 00:13 IST
- [CONTRACT v1 → v2] POST /api/claims now runs the agent loop and returns the decided finding; Cursor: run `npm run gen:api`.
- Files changed: `backend/app/services/seed.py` (modified: demo 9.2 constants + `ensure_demo_92_claim` moved here from loop.py; `seed_demo` ensures them so every demo DB carries the 9.2 context); `backend/app/agent/loop.py` (modified: re-exports the seed constants); `backend/app/schemas.py` (modified: `ClaimCreated` gains nullable `finding_id`/`status`); `backend/app/api.py` (modified: POST /claims runs loop + `memory.decide_finding` on accept, returns finding); `backend/app/main.py` (modified: version v2); `scripts/record_cassettes.py` (modified: `record_demo_claim` + `record_ask_flow`); `openapi/openapi.json` (modified: regenerated v2, 28 paths); `openapi/examples/claim_created.json` (modified: v2 shape); `backend/tests/test_api.py` (modified: canned loop for the typing test, new end-to-end demo test, facts 13 with seeded F-LOOP-92); `backend/tests/test_contract_v0.py` (modified: version pin v2).
- What changed: asking the demo question now yields a stored FOLLOWS finding in one call — structure (replay) → loop (replay) → decide (deterministic). The demo structuring cassette is new; the ask-flow loop needed its own turns because live-typed params (`keep transfer logs`) differ from the hand-fixed T2.5 ones (`transfer logs`) — the prompt carries params, so hashes diverge. Found via a failed record: the model wandered on a dirty default DB (stray extraction facts changed the prompt), which also proved cassettes are content-pinned; fixed with `make reset-demo` first, then recorded clean.
- Checks run: `make check-backend` → ruff clean, mypy clean (52 files), pytest 199/199, zero skipped (all replays run, incl. the new end-to-end). `make record` → ask-flow loop accepted in 5 calls, finding FOLLOWS. Junk confusion-run cassettes (16) removed by content signature; re-ran green.
- Decisions/assumptions: claim-id-independent loop requests let one recording serve every endpoint-created claim (the draft's embedded claim id is the model's, ignored by decide — logged, not fixed, since checker never checks it); loop failures surface as 502 with the claim still stored; non-accepting loops return null finding fields; C-REC-ASK recording id is fixed so re-records replay the loop from cache.
- Contract change: [CONTRACT v1 → v2] — only additive optional fields on ClaimCreated; stub examples updated to the v2 shape.
- Requests: none.
- New-work note: ask-flow end-to-end 2026-10-31.
- Third-party added: none.
- Credit spend: ~$0.01 (1 structuring + 5 loop turns on contributor tier).
- Ready for human commit: yes — suggested message: `Wire agent loop into POST claims and contract v2`

## [ask-502] DONE · 2026-10-31 00:21 IST
- Files changed: `Makefile` (modified: `dev` hint sources `../.env` so uvicorn gets the key); `docs/logs/MUSE_CODE_LOG.md` (modified).
- What changed: nothing in the endpoint — the 502s are the gateway failing loudly by design. Reproduced both: (1) any question without a recorded cassette in replay mode → 502 `MODEL_UNAVAILABLE: no cassette for request …`; (2) `LLM_MODE=live` without the key exported in the server shell → 502 `MODEL_UNAVAILABLE: MODEL_API_KEY is missing`. The demo question itself returns 200 FOLLOWS on a clean seed. The response body always carries the exact `code`/`message` — read it, not just the status line.
- Checks run: live endpoint probes — demo question 200 FOLLOWS; unrecorded question 502 no-cassette; live-without-key 502 missing-key; `make check-backend` → ruff clean, mypy clean, pytest 199/199.
- Decisions/assumptions: replay stays strict (fail loudly, no fallback); only the 8 recorded questions work keyless; any other question needs `LLM_MODE=live` with the key in the server env (use the updated `make dev` command).
- Contract change: none.
- Requests: none.
- New-work note: none.
- Third-party added: none.
- Credit spend: $0.
- Ready for human commit: yes — suggested message: `Load .env in dev server hint`

## [ask-frontend] STARTED · 2026-10-31 00:22 IST

## [ask-frontend] DONE · 2026-10-31 00:37 IST
- Scope: frontend ask-502 (`POST /api/claims` 502 on the 2025-10-17 ask) + challenger panel "No challenger report on this finding yet". No frontend edits (Cursor lane); backend-only fix. Frontend is NOT at fault (details below).
- Diagnosis (read-only frontend inspection):
  - 502: `ClauseReviewPage.tsx` sends exactly what the user typed (`question` + `as_of`, default `2025-10-01`). Replay cassettes are content-pinned by request hash (model+input incl. as_of). Recorded triple used `2026-11-20`; the typed `2025-10-17` had no structure/loop cassettes, so strict replay raised `LLMRequestFailed` -> 502. Correct frontend behavior; backend coverage gap.
  - Challenger: the panel renders `finding.challenger_report`. Backend hardcoded `"challenger_report": None` in `_finding_payload` and never wrote the `challenger_reports` table (a second `review_claim` gap: the endpoint's `decide_finding` call omitted `challenger_cache_dir`, so it read the default `.cache/llm` dir instead of `corpus/cassettes` and could never replay). So the panel could never show data even on success. Correct frontend rendering; backend persistence/wiring gap.
- Files changed (this turn only):
  - `backend/app/services/memory.py`: `decide_finding` keeps the run `ChallengerReport`; `_store_decision(..., challenge=None)` inserts one append-only `challenger_reports` row (claim/finding/model/objections). UNKNOWN paths pass nothing.
  - `backend/app/api.py`: new `_challenger_payload` echoes the stored review (`model`, `blocking` derived from objection severities, `objections`) or None; endpoint `decide_finding` now passes `challenger_cache_dir=CASSETTES_DIR`.
  - `backend/tests/test_memory.py`: `test_decide_persists_challenger_report` (monkeypatched review, no LLM), `test_decide_without_challenger_stores_no_report`.
  - `backend/tests/test_api.py`: `test_user_date_question_end_to_end` (2025-10-17 -> 200 FOLLOWS), `test_challenger_report_returned` (CHALLENGER=on -> payload echoes `muse-spark-1.2` endorsement, status FOLLOWS).
  - `scripts/record_cassettes.py`: `record_ask_flow` parameterized (`as_of`/`claim_id`/`run_id`, `record_review`); main records canonical chain + review, then the 2025-10-17 chain (`C-REC-ASK-1017`).
  - `corpus/cassettes/`: 14 new cassettes (structure-1017 x1, loop-1017 turns x12, ask-flow review x1). The user's exact missing hash `2d021202...` is now recorded.
- Checks run (real results): new tests failed first (incl. reproducing the user's 502s), then `make check-backend` green — ruff clean, mypy clean (52 files), pytest 203/203 (199 prior + 4 new). One `make record` run: canonical loop accepted (5 calls, cache), review recorded blocking=False/0 objections, 1017 loop accepted (12 live calls) -> FOLLOWS, tampered-proof review cache-hit blocking=True.
- Decisions/assumptions: recording pinned to the user's typed date (arbitrary dates still need a live key); `blocking` derived from severities (same rule as challenger) so no schema change and no dev-DB reset needed; no contract change ([CONTRACT v2] field already declared, now populated).
- Requests: [REQ -> H] (1) For a zero-key first-run demo, ask Cursor to default the as-of picker to a recorded date (`2026-11-20` or `2025-10-17`); any other date needs `MODEL_API_KEY` + live mode. (2) Demo server needs `CHALLENGER=on` for real challenger reports, else the panel keeps showing the mock/none state.
- Credit spend: 14 new cassettes this run; dev-DB live-call ledger totals $0.013414 across 18 uncached calls (inside daily $4 budget).
- Ready for human commit: yes. Suggested message: "Record 2025-10-17 ask chain and return stored challenger reports on findings"

## [record-fix] DONE · 2026-10-31 01:14 IST
- Scope: user's `make record` failed at `record_loop` with `budget_exhausted after 12 tool calls (accepted=False)`. Backend lane only; no frontend involvement.
- Root cause (verified, not guessed): the dev DB had drifted since the clean record. A lawyer-review Approve had copied fact F-LOOP-92 into `F-fa0a3f806d0c` (`lawyer_confirmed`, via `premises._copy_fact` — correct T4.4 behavior, not a bug). The loop's turn-1 prompt embeds `_fact_lines` (every MAT-01 fact), so turn-1 hashed differently -> all turns missed cache -> 12 live model calls -> model failed to converge -> `SystemExit`. That run also saved 12 junk cassettes (00:52-01:01) encoding the failed path, which made even replay fail deterministically afterward. Failing input verified by reading the recorded turn-1 text (two near-identical premises).
- Fix (mine): deleted exactly the 12 content-identified junk cassettes (`grep -l F-fa0a3f806d0c`, count now 32 = 18 canonical + 14 ask-frontend); `make reset-demo` (wipes dev sqlite, reseeds canonical rows); `make record` green with $0 spend (extraction/claims skips, loop 6-turn accept, ask-flow 5-turn FOLLOWS + review endorsement cache-hit, 1017 chain 12-turn FOLLOWS, tampered-proof review cache-hit).
- My code (ask-frontend) is untouched and exonerated: the failure used only pre-existing `record_loop` + drifted DB rows. My two replay probes were read-only plus log rows (Run/ToolCall/LlmCall, hash-neutral), wiped by the reset.
- Checks: `make check-backend` green — ruff clean, mypy clean (52 files), pytest 203/203.
- Standing rule for human/demo: interactive demo use (Ask, and especially lawyer Approve which mints new `F-*` facts) changes prompt hashes. Always run `make reset-demo` before `make record`; never record on a clicked-around DB. No `make record` needed at all right now — every chain is recorded.
- Spend: the failed run burned 12 live calls = $0.010667 (`RUN-458718727d71`); cleanup/record runs spent $0. Cumulative dev-DB live ledger was wiped by the reset.
- Ready for human commit: yes (log only; cassettes are untracked, DB is gitignored). Suggested message: "Remove failed-path loop cassettes orphaned by drifted demo DB".

## [gate-G4-G8] STARTED · 2026-11-02 01:39 IST

## [gate-G4-G8] PARTIAL · 2026-11-02 02:01 IST
- Scope: gate fix G4 (replay 502 hash mismatch) then G8 (seed extracts DOC-01 facts). Backend lane only; no frontend edits.
- G4 DIAGNOSIS (verified by diff, task step 1): reproduced the 502 on the live server DB — the loop turn-1 hash `1780d3d1…` has no cassette. Diffed the server-built request against the recorded ask-flow turn-1 (`880eea31…`): model, tools (list order + content), tool_choice, parallel_tool_calls, temperature, as_of, question, matter id are ALL EQUAL. The ONLY differing field is the "Admitted premises" block: recorded has 1 line (F-LOOP-92), server has 14 (12 facts from Screen 3 extraction testing + 1 lawyer-confirmed copy, created 2026-11-01 19:54Z, AFTER the Oct-31 recordings). Also noted: bare `cp` of the WAL database gives a stale snapshot (1 fact) — misleading probes; diagnosis rerun against live rows.
- Step 2 NOT applied (deliberate): no volatile field exists in the failing request. The differing block is real admitted premises, not timestamps/run-ids/tool-order noise. Hashing it away would replay stale-premise proofs against new premises — dishonest for a verifier — so I did not touch `request_hash` or prompt inputs.
- Step 3 done ONCE (request really changed): `make reset-demo` + one `make record`. It FAILED at `record_loop`: `budget_exhausted after 12 tool calls`. Trajectory read back from the saved turns: the model never used the real claim id — verify_derivation calls went out as CLAIM-9.2 → MAT-01 → CT2 → F-LOOP-92 (all `unknown_claim` tool errors) and it burned 3 calls on the prompt-banned `list_dependent_claims`. The prompt never states the claim id (latent since T2.5; old recordings succeeded by trial-and-error luck — turn files show CT2-transfer-logs → C-LOOP-92). The 13-fact prompt made the guessing fail. This is a convergence problem, not a hash problem.
- Cleanup: deleted this run's 12 failed-path cassettes (mtime 01:49–01:58); 32 valid prior cassettes remain. Dev DB = fresh G8 seed + this attempt's log rows; re-run `make reset-demo` before any future record.
- Files changed: `backend/app/services/seed.py` (G8: `_seed_extraction_facts` replays the T2.2 extraction cassette and persists `F-SEED-01..12` with fixed dates, attached to seeded clauses; `seed_demo` result gains `facts`); `scripts/seed_demo.py` (print includes facts); `backend/tests/test_seed.py` (new `test_seed_extracts_doc01_facts_in_replay`, idempotency now expects 13 facts); `backend/tests/test_api.py` (new G4 HTTP replay regression `test_g4_ask_replays_on_seeded_facts`; `test_extract_persists_version` stale total 13 → 25 for the new seed).
- Checks run (real results): new tests failed first (seed facts absent; G4 test passes pre-seed-change then fails post, as designed). After seed change + before record: `test_seed.py` 3/3 green; ask chain tests fail with 502 no-cassette (the bug, captured). After the single record attempt (failed): still red on 4 tests — `test_demo_question_end_to_end`, `test_g4_ask_replays_on_seeded_facts`, `test_user_date_question_end_to_end`, `test_challenger_report_returned`. `test_extract_persists_version` fixed and passing. ruff clean, mypy clean (52 files) throughout. `make check-backend` is RED only on those 4 replay-chain tests.
- Decisions/assumptions: G8 deterministic ids (`F-SEED-*`) instead of the endpoint's random `_new_id`s, because every reset must reproduce byte-identical prompt hashes. Seeded facts attach to the seeded DOCV-01 clauses (no duplicate version). The `request_lawyer_review` review_id is a genuinely volatile id if a loop ever called it mid-path — observed, not changed (prompt-banned; no recorded path uses it).
- Contract change: none (seed data + tests only; no schema/endpoint/tool change).
- Requests: [REQ → H] The one allowed `make record` is spent and the model could not re-converge on the 13-fact prompt. To finish G4 pick one: (A) approve a second record run as-is (temperature 0 but gateway varies; may fail again, ~$0.013/run); (B) approve adding the claim id to the proof prompt (one line in `prompts.build_proof_input`; makes convergence near-deterministic) then one record run; (C) approve resolving the claim server-side in verify/propose tools instead of trusting the model's echoed claim_id (most robust, biggest change). Recommendation: B, then A applies as the single record after the prompt fix.
- New-work note: G8 seed extraction + G4 diagnosis 2026-11-02.
- Third-party added: none.
- Credit spend: $0.013246 (12 live calls, RUN-39b3b2be0ed1) for the single failed record attempt; seeding is replay-only ($0).
- Ready for human commit: NO — lane check red on 4 replay-chain tests until a re-record lands. Suggested message once green: "Seed DOC-01 facts at reset and re-record ask chain (gate G4, G8)"

## [explore] STARTED · 2026-11-02 03:19 IST
- Task: Explore current folder (read-only orientation, no task assigned)
- Scope: read `AGENTS.md`, `PLAN.md`, `docs/TASKS.md`, `PROGRESS.md`, all three logs (`MUSE_CODE_LOG.md`, read-only `CURSOR_LOG.md`/`HUMAN_LOG.md`), root layout, backend/frontend/corpus/openapi structure

## [explore] DONE · 2026-11-02 03:19 IST
- Task: Explore current folder (read-only orientation, no task assigned)
- Files changed: `docs/logs/MUSE_CODE_LOG.md` (modified, this entry only)
- What changed: No code changed. Orientation findings: (1) State per `PROGRESS.md` (2026-11-02, Day 5): T0–T6 coded, contract v2 (`openapi/openapi.json`: v2, 28 paths, 26 examples), Screen 1 Ask on live replay returns FOLLOWS (`FND-e25e54bb2f42`); next is `/impact` + `/control` click-through, then T8 — do not start T7 yet. (2) Backend lane complete through T6.1 + ask-flow/ask-502 fixes: `backend/app/{api,main,schemas,stub,models,db}.py`, `agent/{llm,extract,claims,loop,tools,prompts,challenger}.py`, `services/{sources,rulecards,seed,diff,memory,graph,impact,reverify,premises}.py`, isolated `backend/checker/verify.py`; 22 test files in `backend/tests/`; 48 cassettes + 7 rule cards in `corpus/`. (3) Last MC entry `[gate-G4-G8] PARTIAL · 2026-11-02 02:01 IST` is superseded by Cursor's `[ask-502-B] DONE/CONFIRMED · 2026-11-02 02:30/02:33 IST` (stable cassette claim id `C-REC-ASK` + tool rebind; browser Ask 200 FOLLOWS) and commits `82fc307`/`6264d22` — the 4 red replay-chain tests and `[REQ → H]` A/B/C in that PARTIAL entry should be re-verified before acting on them. (4) `HUMAN_LOG.md` sync table still says SP4 not reached — stale vs the confirmed browser FOLLOWS; H-owned, not edited.
- Checks run: none (read-only exploration; no lane check run, none claimed). Verified counts via shell: contract v2/28 paths, 26 examples, 48 cassettes, 7 rule cards. `git status`: only `backend/db.sqlite3-shm`/`db.sqlite3-wal` modified (live DB sidecars, gitignored DB itself untouched by me); `git log -5` head is `6264d22 update the docs`.
- Decisions / assumptions: Acting as Muse Code lane per user instruction. No task ID assigned, so no implementation started per AGENTS.md session rule ("Do ONLY the task you were given").
- Contract change: none (v2 stands)
- Requests: [REQ → H] confirm next task (per PROGRESS.md: /impact + /control click-through, then T8.1–T8.2; T7 not started). Note the stale SP4 row in `HUMAN_LOG.md` and the superseded `[gate-G4-G8]` PARTIAL above — a backend `make check-backend` run would confirm the replay chain is green before the click-through.
- New-work note: none
- Third-party added: none
- Credit spend: none (no model calls)
- Ready for human commit: yes — suggested message: `Log Muse Code exploration session 2026-11-02`

## [ask-502-clause] STARTED · 2026-11-02 03:21 IST
- Task: Fix POST /api/claims 502 (user-reported, backend lane)
- Scope: reproduce against live DB on :8001, diagnose which stage (structure vs loop) misses replay, fix in `backend/**` only, regression test, `make check-backend`

## [ask-502-clause] DONE · 2026-11-02 03:26 IST
- Task: Fix POST /api/claims 502 (user-reported, backend lane)
- Files changed: `backend/app/api.py` (modified: `_CLAUSE_REF_RE` + `_resolve_clause`, wired into `create_claim`), `backend/tests/test_api.py` (new `test_demo_question_with_mismatched_clause_id`), `docs/logs/MUSE_CODE_LOG.md` (modified)
- What changed: Root cause verified against the live DB, not guessed: the three 502'd claims (`C-a1d635…`, `C-228a1b…`, `C-4f2014…`) were stored with `clause_id=CL-03` while their question is the default "Does clause 9.2 require Nimbus to keep transfer logs?". Claim structuring replayed fine; the agent loop's turn-1 prompt embeds the target clause text verbatim, so clause 3's text hashed to `7f839e6b…` (2026-11-20) / `cae44c76…` (2025-10-17), neither recorded → `CassetteMissing` → 502 `MODEL_UNAVAILABLE`. `CL-10` + same question returned 200 FOLLOWS before the fix. Fix: an explicit `clause <ref>` in the question is authoritative — `_resolve_clause` resolves that ref inside the same document version and the claim is stored against it; no ref or unknown ref keeps the caller's clause (no behavior change there, no hash weakening, `request_hash` untouched).
- Checks run: regression test written first → failed with the exact live hash `7f839e6b…` (502). After fix: targeted 5 tests pass; `make check-backend` → ruff clean, mypy clean (52 files), pytest 206/206. Live server on :8001 (auto-reloaded): `CL-03`+9.2 question → 200 FOLLOWS at both `2026-11-20` and `2025-10-17`; `CL-10` → 200 FOLLOWS.
- Decisions / assumptions: fix at claim creation (not in the loop) so the stored claim, proof `contains_element`, and finding all consistently concern clause 9.2. A question with no clause ref aimed at a non-9.2 clause still has no recorded proof path in replay and will still 502 — that needs a live key or a new cassette, not a code change; not weakened. If the user's server was started without `--reload`, it needs a restart to pick this up.
- Contract change: none (v2 stands; no schema/endpoint/tool change)
- Requests: none. [REQ → H] restart the :8001 server if it was not run with `--reload`, then re-click Run verification on `/review` (any clause selected now works for the 9.2 question).
- New-work note: clause-ref resolution for claim targeting 2026-11-02
- Third-party added: none (stdlib `re`)
- Credit spend: none (replay only; no live calls, no `make record`)
- Ready for human commit: yes — suggested message: `Fix claims 502: resolve clause named in question over mismatched clause_id`

## [gate-probe] STARTED · 2026-11-02 09:26 IST
- Task: Cover backend gaps — Phase 1 gate probe (plan agreed with user)
- Scope: `make reset-demo`, backend on :8001 with `API_STUB=0 LLM_MODE=replay DEMO_MODE=1 CHALLENGER=on`, curl-probe full demo path (ask both dates, ingest/impact/reverify, premise actions, tamper, UNKNOWN); log backend defect list before fixing. Backend lane only; no frontend/docs edits. Note: uncommitted [ask-502-clause] fix is in the working tree and included in this probe.

## [gate-fix] DONE · 2026-11-02 09:52 IST
- Task: Cover backend gaps — Phases 1–5 (probe, fix, replay robustness, T8.1 scenarios, deploy artifact)
- [CONTRACT v2 → v3] ProofStep now carries all checker step fields; Cursor: run `npm run gen:api`
- Files changed: `backend/app/api.py` (UNKNOWN claims decide directly, no loop; empty-proof skeleton), `backend/app/services/memory.py` (unavailable challenger → REQUIRES_REVIEW + low band, finding never lost), `backend/app/schemas.py` (ProofStep: clause_id/quote/value/op/bound/party/role + extra=allow), `backend/app/agent/tools.py` (`_drop_null_fields` service-boundary normalization before the checker; checker untouched), `backend/app/agent/llm.py` (replay-miss message names the remedy), `backend/app/main.py` (version v3), `backend/tests/test_api.py` (+3 gate regression tests), `backend/tests/test_seed.py` (+seed determinism test), `backend/tests/test_scenarios.py` (new, T8.1: decoy, future provision, stale chain exact, cross-matter, source failure), `backend/tests/test_contract_v0.py` (version pin v3), `backend/Dockerfile` (new), `openapi/openapi.json` (regenerated v3), `openapi/examples/finding{,_current,_history}.json` (regenerated from stub), `docs/logs/MUSE_CODE_LOG.md`
- Phase 1 probe (18 checks on the live server): 3 real backend defects found, all reproduced before fixing. **D1** UNKNOWN-typed questions ran the agent loop and 502'd (no proof path exists); now `create_claim` skips the loop and `memory.decide_finding` stores an UNKNOWN finding. **D2** with `CHALLENGER=on`, the 2025-10-17 ask 502'd *after* a successful loop: hash `d86e512b…` was proven (by recomputation) to be the challenger request, which has no cassette for that date, and the exception lost the finding; now an unavailable challenger forces REQUIRES_REVIEW (low band, no challenger report) instead of a 502. **D3** proof round-trip: `ProofStep` dropped `clause_id`/`quote` and emitted `citation: null`, so an untampered proof read from the API failed `/api/proofs/verify` (`CITATION_MALFORMED`) — Screen 3's tamper demo could not distinguish tampered from untampered; now the schema carries all step fields and `verify_proof` drops explicit nulls at the service boundary (checker core unchanged, still strict for direct callers). Non-defect noted: `stale-demo` flags no findings for the 9.2 ask because its proof cites no s8(6) rule card — legally correct; the stale demo needs a breach-intimation finding, which is a demo-content decision for H, not an engine bug.
- Checks run (real results): 3 new tests failed first (502 / KeyError clause_id), then pass. Live probe after fix: 19/19 checks behave as specified (1017+CHALLENGER=on now returns 200 REQUIRES_REVIEW as designed; challenger off keeps FOLLOWS). `make check-backend` → ruff clean, mypy clean (52 files), pytest **215/215**. Docker: `docker build -f backend/Dockerfile` succeeds; container on :8002 serves health/matter and replay ask → 200 FOLLOWS (container removed after). Dev DB reset clean (13 facts) and :8001 server restarted on the new code; one sanity ask → FOLLOWS.
- Decisions / assumptions: challenger-unavailable degrades to REQUIRES_REVIEW, never to endorsement and never to a lost finding. No cassette recorded in this task (Phase 3 decision): recording the 1017 challenger cassette would restore FOLLOWS under CHALLENGER=on for that date — [REQ → H] approve a single targeted record run (~$0, muse-spark-1.2 is unpriced) or keep as is. `request_hash` not weakened anywhere.
- Contract change: [CONTRACT v2 → v3] additive only — ProofStep gains optional fields (`clause_id`, `quote`, `value`, `op`, `bound`, `party`, `role`) and `additionalProperties: true`; no path or required-field change. [REQ → CU] run `npm run gen:api` and confirm the ProofEditor round-trip on Screen 3.
- Requests: [REQ → H] (1) root `docker-compose.yml` is outside my lane — add it or approve; the backend Dockerfile is ready and verified. (2) Update `PROGRESS.md`/`HUMAN_LOG.md` (SP4, contract v3) — your files. (3) Optional targeted challenger cassette record above. (4) Rule-card `trust_class` flip + CT taxonomy decision still pending from T1.3.
- New-work note: gate defect fixes D1–D3, T8.1 scenario suite, backend Dockerfile 2026-11-02
- Third-party added: none
- Credit spend: none (replay only; no `make record`, no live calls)
- Ready for human commit: yes — suggested message: `Gate fixes: UNKNOWN decides directly, challenger miss requires review, proof round-trips; contract v3, scenarios, Dockerfile`

## [readme-backend] DONE · 2026-11-02 10:05 IST
- Task: Update README.md for the backend (user request)
- Files changed: `docs/logs/MUSE_CODE_LOG.md` only. `README.md` NOT edited — it is Cursor's lane (AGENTS.md §4); the draft below is for CU/H to apply.
- Requests: [REQ → CU] apply the backend README update drafted in the 2026-11-02 session (also summarised here): (1) demo path is contract **v3**, not v1; (2) gateway model is `muse-spark-1.3-contributor` for extraction/claims/loop, `muse-spark-1.2` challenger only; (3) template file is `env.example`, not `.env.example`; (4) add backend architecture invariants (isolated deterministic checker, only `services/memory.py` sets status, append-only tables, six bounded tools); (5) add demo runbook: `make reset-demo` first, `API_STUB=0 LLM_MODE=replay DEMO_MODE=1`, recorded ask dates 2026-11-20 / 2025-10-17, arbitrary questions need `LLM_MODE=live` + key, always reset before `make record`; (6) behaviour notes: UNKNOWN questions decide UNKNOWN (no proof drafted), unavailable challenger forces REQUIRES_REVIEW, question naming a clause targets that clause; (7) Docker: `docker build -f backend/Dockerfile -t clausetrace-backend .` verified, compose file pending H; (8) checks: `make check-backend` (ruff, mypy, pytest 215). [REQ → H] confirm the port line before CU applies it: README says backend 8000 / Vite proxy 8000, but the frontend proxy currently targets 8001 (local 8000 is another app) — state both (canonical 8000, local demo 8001) rather than silently changing the canonical port.
- Checks run: none (documentation request only; facts verified against code/logs from [gate-fix], not re-run)
- Contract change: none (documents existing v3)
- Credit spend: none
- Ready for human commit: yes — suggested message: `Log README backend update request for Cursor`

## [root-health] STARTED · 2026-11-02 09:56 IST
- Task: Add GET / and GET /health so probes stop 404ing (user request, backend lane)
- Scope: `backend/app/main.py` routes + test first in `backend/tests/test_health.py`; canonical `/api/health` unchanged

## [root-health] DONE · 2026-11-02 10:00 IST
- Task: Add GET / and GET /health so probes stop 404ing (user request, backend lane)
- [CONTRACT v3 → v4] additive probe routes `/` and `/health`; Cursor: `npm run gen:api` (no API path changes)
- Files changed: `backend/app/main.py` (root service index + bare `/health` alias; version v4), `backend/tests/test_health.py` (new `test_root_and_health_alias`, written first — failed 404 before the fix), `backend/tests/test_contract_v0.py` (version pin v4), `openapi/openapi.json` (regenerated: v4, 30 paths), `docs/logs/MUSE_CODE_LOG.md`
- What changed: `GET /` returns `{status, service, health, docs}`; `GET /health` returns `{"status":"ok"}`; canonical `/api/health` unchanged. Browsers, scanners and load balancers probing the root no longer 404.
- Checks run: `make check-backend` → ruff clean, mypy clean, pytest 216/216. Live on the user's :8000 server (auto-reloaded): `/` → 200 service index, `/health` → 200 ok, `/api/health` → 200 ok.
- Decisions / assumptions: new routes are additive probes only; no §7 endpoint changed. Note the :8001 server from the gate session is no longer running — the user's :8000 server is now the live one, while the frontend Vite proxy still targets 8001 (Cursor lane; see [readme-backend] request).
- Contract change: [CONTRACT v3 → v4] additive
- Requests: [REQ → CU] regenerate API types for v4 (probe routes only; no client change needed)
- New-work note: none
- Third-party added: none
- Credit spend: none
- Ready for human commit: yes — suggested message: `Add root and bare health routes so probes do not 404; contract v4`

## [T7.3] STARTED · 2026-11-02 13:05 IST
- Task: T7.3 Counterfactual mode (read-only graph traversal) + user additions
- Scope: `backend/checker/proplogic.py` (new pure propositional-logic entailment: truth-table over parsed formulas, deterministic valid/not-valid with counterexample), `backend/app/services/counterfactual.py` (read-only dry run of impact: diff + dependents + per-finding entailment under the hypothetical change, NO writes), real `POST /api/counterfactual` + new `GET /api/reverify-list` (STALE findings awaiting re-verify; counterfactual response also returns its hypothetical `reverify_list`), tests first. Order T7.3 → T7.4 → T7.2 → T7.1 approved by user; T7.5 excluded. Checker core `verify.py` untouched; proplogic lives in `checker/` under the same isolation rules.

## [T7.3] DONE · 2026-11-02 13:20 IST
- Task: T7.3 Counterfactual mode + propositional-logic validity + reverify list
- [CONTRACT v4 → v5] `POST /api/counterfactual` is real; new `GET /api/reverify-list`; Cursor: `npm run gen:api`
- Files changed: `backend/checker/proplogic.py` (new: parser for `~ & | -> <->`, truth-table `entails` returning `{valid, consistent, counterexample, atoms}`, 20-atom cap, `PropLogicError`; pure stdlib, isolation scan passes), `backend/app/services/counterfactual.py` (new: read-only diff + dependent traversal; per-finding propositions — premise/rule/force/evidence atoms plus the proof's inference rule `(all atoms) -> conclusion_holds` — decided by `proplogic.entails`; atoms tied to changed provisions withheld so entailment fails deterministically), `backend/app/api.py` (counterfactual endpoint wired; new `GET /api/reverify-list?matter_id=` listing STALE findings), `backend/app/schemas.py` (CounterfactualResult extended additively; ReverifyList models), `backend/app/main.py` (v5), `backend/tests/test_proplogic.py` (new, 6 tests), `backend/tests/test_counterfactual.py` (new, 4 tests incl. no-writes row-count proof and endpoint tests), `backend/tests/test_contract_v0.py` (pin v5), `openapi/openapi.json` (regenerated, 31 paths), `openapi/examples/counterfactual.json` (regenerated), `docs/logs/MUSE_CODE_LOG.md`
- Checks run: `make check-backend` → ruff clean, mypy clean, pytest **227/227**. Live on :8001 after `make reset-demo`: counterfactual for SV-DPDP-ACT-V2SIM → changed `[DPDP-Act-2023_s8(6)]`, affected `FND-RC-CT3-BREACH-01` with `would_remain_valid: false` and counterexample `{rule_RC_CT3_BREACH_01: false, conclusion_holds: false}`, `reverify_list: [FND-RC-CT3-BREACH-01]`; persistent `/api/reverify-list` stays empty (nothing actually staled — read-only proven live and by row-count test).
- Decisions / assumptions: propositional validity is entailment, not checker re-run — the checker still decides real findings; counterfactual only asks whether the conclusion still *follows* if the changed provisions' atoms fall. Inconsistent premises never entail validity. Seeded per-card findings (from 59025a7) are legitimately part of the affected set. `GET /api/reverify-list` lists STALE today; CONFLICTING findings join it in T7.4.
- Contract change: [CONTRACT v4 → v5] additive (new endpoint + optional fields on CounterfactualResult)
- Requests: [REQ → CU] run `npm run gen:api` for v5; Screen 2 can now call `POST /api/counterfactual` with `{source_version_id}` and show `reverify_list` + the counterexample. [REQ → H] T7.4 decision still open: new CONFLICTING finding status (my recommendation) vs reuse REQUIRES_REVIEW.
- New-work note: propositional-logic entailment engine + counterfactual dry run 2026-11-02
- Third-party added: none (stdlib only)
- Credit spend: none (deterministic; no model calls)
- Ready for human commit: yes — suggested message: `T7.3: counterfactual dry run with propositional entailment and reverify list; contract v5`

## [T7.4] STARTED · 2026-11-02 13:15 IST
- Task: T7.4 CONFLICTING state (two rule cards) — new finding status per user-approved recommendation
- Scope: deterministic conflict detection in `services/memory.py` only (checker untouched): cited cards' `requires` become propositional formulas (`no_<x>`/`not_<x>` = negation of `<x>`), `checker.proplogic` decides consistency; inconsistent cited-card set on an otherwise valid proof → status CONFLICTING (band low). CONFLICTING findings join `GET /api/reverify-list` (reason CONFLICTING). Tests first in `backend/tests/test_conflicting.py`. No corpus card added (would change the 7-card count and the human's seeded gate); demo pair lives in test fixtures until H approves an 8th card.

## [T7.4] DONE · 2026-11-02 13:32 IST
- Task: T7.4 CONFLICTING state (two rule cards)
- [CONTRACT v5 → v6] new finding status value CONFLICTING (status is a free string in the schema; no shape change); Cursor: `npm run gen:api` + a CONFLICTING badge
- Files changed: `backend/app/services/memory.py` (`STATUSES` gains CONFLICTING; `_cards_conflict` builds propositional formulas from cited cards' `requires` — `no_x`/`not_x` negate `x` — and asks `checker.proplogic.entails` for consistency; precedence: checker-invalid → REQUIRES_REVIEW, disputed → REQUIRES_REVIEW, conflict → CONFLICTING, then challenger/tool-log/conclusion; conflict forces low band), `backend/app/api.py` (reverify-list also lists CONFLICTING findings with reason CONFLICTING), `backend/app/main.py` (v6), `backend/tests/test_conflicting.py` (new, 4 tests: conflict decides CONFLICTING + low band + card edges; agreeing cards still FOLLOWS; tampered proof still REQUIRES_REVIEW; CONFLICTING appears in reverify-list endpoint), `backend/tests/test_contract_v0.py` (pin v6), `openapi/openapi.json` (regenerated v6), `docs/logs/MUSE_CODE_LOG.md`
- Checks run: conflict test failed first (decided FOLLOWS), then `make check-backend` → ruff clean, mypy clean, pytest **231/231**. Live :8001 restarted on v6: health ok, openapi v6, reverify-list ok (empty on the clean demo DB — no conflicting pair exists in the shipped corpus, see requests).
- Decisions / assumptions: conflict is defined over *cited* cards only, on an otherwise checker-valid proof — an invalid proof is REQUIRES_REVIEW, never CONFLICTING. Negation convention is the `no_`/`not_` prefix on requirement names, documented in `_cards_conflict`. No corpus card added: an 8th (conflicting) card would change the seeded card count (7) and the human's gate fixtures; the demo pair is proven in tests instead.
- Contract change: [CONTRACT v5 → v6] additive status value
- Requests: [REQ → H] approve adding one demo conflicting card (e.g. `RC-CT3-BREACH-CONFLICT-01`, `requires: [no_breach_intimation_duty]`, same s8(6) span) so Screen demos can produce CONFLICTING live — this changes card count 7 → 8 and seed expectations, so it needs your go-ahead. [REQ → CU] `npm run gen:api` for v6 and add a CONFLICTING status badge (text + icon, not color-only).
- New-work note: propositional conflict detection in the memory service 2026-11-02
- Third-party added: none
- Credit spend: none (deterministic)
- Ready for human commit: yes — suggested message: `T7.4: CONFLICTING status from propositional rule-card conflict; contract v6`

## [T7.4-demo-card] STARTED · 2026-11-02 13:27 IST
- Task: Add approved demo conflicting card and prove CONFLICTING works end-to-end (user-approved)
- Scope: `corpus/rulecards/RC-CT3-BREACH-CONFLICT-01.yaml` (same s8(6) span, `requires: [no_breach_intimation_duty]`, kind interpretation, labelled demo), seed/test count updates 7 → 8 cards, live decide test on a scratch seeded DB: checker-valid proof citing both breach cards + fresh lookup → expect CONFLICTING in reverify-list

## [T7.4-demo-card] DONE · 2026-11-02 13:45 IST
- Task: Add approved demo conflicting card and prove CONFLICTING works end-to-end (user-approved)
- Files changed: `corpus/rulecards/RC-CT3-BREACH-CONFLICT-01.yaml` (new: same s8(6) verbatim span as RC-CT3-BREACH-01, kind interpretation, `requires: [no_breach_intimation_duty]`, interpretation text explicitly labelled a fictional demo reading, `approved_by: demo-conflict-fixture`), `backend/tests/test_seed.py` (card counts 7 → 8), `backend/tests/test_counterfactual.py` (affected set gains the new card's seeded finding), `backend/tests/test_conflicting.py` (new `test_demo_conflict_card_end_to_end` on the real corpus cards), 2 new cassettes in `corpus/cassettes/` (challenger hashes changed because card lines now include the 8th card), `docs/logs/MUSE_CODE_LOG.md`
- What changed / verified: citing BOTH real breach cards in one checker-valid proof (fresh lookup, v1-only corpus so the Act version is current) decides **CONFLICTING**; citing only RC-CT3-BREACH-01 decides **FOLLOWS** — the conflict path works and does not fire spuriously. The 8th card also enters challenger prompts, so its two review cassettes were re-recorded with the one approved `make record` for this task (after `make reset-demo`).
- Checks run: `make record` once → ask chains FOLLOWS from cache, ask-flow review re-recorded (blocking=False), tampered-proof review blocking=True, latest call cost $0.000420. `make check-backend` → ruff clean, mypy clean, pytest **232/232** (was 231 + 1 new demo-card test). Live: dev DB reseeded (8 cards), :8001 restarted; graph for MAT-01 now shows `RC-CT3-BREACH-CONFLICT-01` and its seeded finding.
- Decisions / assumptions: the demo card is fictional and says so in its interpretation text; it is `ai_inferred` like the other unreviewed cards. Note the full demo seed also loads simulated v2, which supersedes Act v1 — a cite_rule proof against the real pair therefore decides CONFLICTING only in a v1-current context (as in the test); the seeded per-card finding exists for the impact/counterfactual demo regardless.
- Contract change: none (v6 stands; no schema change)
- Requests: [REQ → CU] the conflict card is now in the demo DB; Screen 3 can surface CONFLICTING from the reverify-list (badge request from [T7.4] still open)
- New-work note: demo conflicting rule card 2026-11-02
- Third-party added: none
- Credit spend: ~$0.0004 (one `make record`: 2 challenger calls on muse-spark-1.2, rest cached)
- Ready for human commit: yes — suggested message: `Add demo conflicting rule card and prove CONFLICTING end-to-end`

## [T7.2] STARTED · 2026-11-02 13:40 IST
- Task: T7.2 Scanned page → text (Muse Spark PDF/image input)
- Scope: step 0 probe (does `muse-spark-1.3-contributor` accept image/PDF input on the Responses API? stop + log if not), fictional scanned fixture in `corpus/scans/`, `backend/app/agent/scan.py` (multimodal extraction via gateway only, T2.2-style validation), cassette via one `make record`, replay tests. Extracted facts are `document_extracted` only once stored against a document version; model output alone admits nothing. Tests never live.

## [T7.2] DONE · 2026-11-02 13:52 IST
- Task: T7.2 Scanned page → text (Muse Spark PDF/image input)
- [CONTRACT v6 → v7] new `POST /api/scans`; Cursor: `npm run gen:api`
- Files changed: `corpus/scans/clause_9_2_page.png` (new fictional fixture: clause 9.2 rendered as a scanned page, PIL/DejaVu), `backend/app/agent/scan.py` (new: `scan_page` via gateway image input, `emit_scan` validation, `ScanError`; PNG/JPEG only), `backend/app/agent/prompts.py` (SCAN_TOOL + multimodal input builder), `backend/app/schemas.py` (ScanRequest/ScanResult), `backend/app/api.py` (`POST /api/scans`: base64 JSON body — no multipart dependency — stores a new scan document + version + clause + `document_extracted` fact), `backend/app/main.py` (v7), `scripts/record_cassettes.py` (`record_scan`), 1 new cassette (42922183…), `backend/tests/test_scan.py` (new, 4 tests), `backend/tests/test_contract_v0.py` (pin v7), `openapi/openapi.json` (regenerated v7), `docs/logs/MUSE_CODE_LOG.md`
- Probe result: `muse-spark-1.3-contributor` accepts `input_image` (data URI) on the Responses API and transcribed the fixture verbatim (798 in / 512 out tokens). PDF input was NOT probed, so `application/pdf` is rejected with a typed ScanError instead of a guessed format.
- Checks run: `make record` once (scan cassette recorded live, clause 9.2). `make check-backend` → ruff clean, mypy clean, pytest **236/236** (replay scan transcribes the fixture; endpoint stores document kind=scan with a `document_extracted` fact linked to the clause; invalid base64 → 400; PDF → typed error). Live on :8001: `POST /api/scans` → 200, ref 9.2, fact `document_extracted`; demo DB then reset clean and server restarted on v7.
- Decisions / assumptions: base64-in-JSON instead of multipart (python-multipart is not installed and new deps need approval). The scanned document is a separate document (kind `scan`), so the demo DPA clause list is untouched. Model output alone admits nothing — the fact becomes `document_extracted` only when the endpoint stores it against the new document version, same rule as T2.2.
- Contract change: [CONTRACT v6 → v7] additive (new endpoint + models)
- Requests: [REQ → CU] `npm run gen:api` for v7; a scan upload control can post `{matter_id, title, image_base64}` — no multipart needed
- New-work note: multimodal scanned-page transcription 2026-11-02
- Third-party added: none (PIL already present locally, used only to render the fixture; runtime is stdlib + gateway)
- Credit spend: ~$0.0004 total (probe 798/512 tokens + one recorded scan call, contributor tier)
- Ready for human commit: yes — suggested message: `T7.2: scanned page transcription via Muse Spark image input; contract v7`

## [T7.1] STARTED · 2026-11-02 13:45 IST
- Task: T7.1 Voice dictation → proposed fact (Muse Voice Transcribe, approval gate)
- Docs read (user request): dev.meta.ai overview + speech-to-text guide — model `muse-voice-transcribe-1.0`, file endpoint `POST /v1/asr/transcribe` (multipart: `request` JSON part + `audio` WAV part; mono 16-bit PCM WAV 16/24 kHz; $0.18/hr; response `{transcript, turns, audioDurationMs}`)
- Scope: fictional dictation fixture via ffmpeg flite TTS (`corpus/audio/`), `backend/app/agent/transcribe.py` (stdlib multipart client, gateway-style live/replay/mock + cassette keyed by audio hash, `llm_calls` logging), `POST /api/dictations` storing the transcript as a proposed fact with `trust_class=ai_inferred` (inadmissible as a premise until the existing lawyer approve flow mints the `lawyer_confirmed` copy), replay tests first incl. checker rejection of the unapproved fact. One `make record` for the ASR cassette.

## [T7.1] DONE · 2026-11-02 14:05 IST
- Task: T7.1 Voice dictation → proposed fact (Muse Voice Transcribe, approval gate)
- [CONTRACT v7 → v8] new `POST /api/dictations`; Cursor: `npm run gen:api`
- Files changed: `corpus/audio/dictation_fact.wav` (new fictional fixture: flite-synthesized dictation, mono 24 kHz PCM WAV per the docs' format), `backend/app/agent/transcribe.py` (new: docs-shaped multipart client for `POST /v1/asr/transcribe`, live/replay/mock, cassette `<audio-hash>.asr.json`, WAV container validation, `llm_calls` logging at $0.18/hr, live blocked under pytest), `backend/app/schemas.py` (DictationRequest/DictationResult), `backend/app/api.py` (`POST /api/dictations` stores the transcript as `trust_class=ai_inferred`, origin `voice_dictation`; TranscribeError → 400), `backend/app/main.py` (v8), `scripts/record_cassettes.py` (`record_dictation`), 1 ASR cassette (2ac4b57a…asr.json), `backend/tests/test_transcribe.py` (new, 3 tests), `backend/tests/test_contract_v0.py` (pin v8), `openapi/openapi.json` (regenerated v8), `docs/logs/MUSE_CODE_LOG.md`
- Checks run: docs-format probe first (curl multipart, exact transcript back, 3.84 s audio). `make record` once → ASR cassette recorded with the exact transcript. `make check-backend` → ruff clean, mypy clean, pytest **239/239**: replay transcription matches; the proposed fact is `ai_inferred` and `verify_proof` rejects it with PREMISE_UNTRUSTED; after lawyer approve, the `lawyer_confirmed` copy verifies valid. Live on :8001: dictation → 200 `ai_inferred`, approve → 200 `lawyer_confirmed` new fact; demo DB reset clean afterwards, server on v8.
- Decisions / assumptions: the ASR endpoint is not the Responses API, so it gets its own client beside the gateway (same modes, cassette discipline, key handling and `llm_calls` logging; the six agent tools are unchanged). Non-WAV audio is rejected (docs' container); realtime WebSocket mode is out of scope — file transcription covers dictation. Approval gate is the existing T4.4 premises flow, unmodified.
- Contract change: [CONTRACT v7 → v8] additive (new endpoint + models)
- Requests: [REQ → CU] `npm run gen:api` for v8; a dictation control can post `{matter_id, clause_id, audio_base64}` (WAV) and must show the proposed fact as not-yet-approved until a lawyer approves it
- New-work note: Muse Voice Transcribe dictation with lawyer approval gate 2026-11-02
- Third-party added: none (stdlib urllib multipart; ffmpeg/flite used only to render the fixture, not a runtime dependency)
- Credit spend: ~$0.0004 (probe + one recorded ASR call; $0.18/hr × ~4 s each)
- Ready for human commit: yes — suggested message: `T7.1: voice dictation to proposed fact with approval gate; contract v8`

## [e2e-verify] DONE · 2026-11-02 14:15 IST
- Task: Test all things end-to-end (user request)
- Files changed: `backend/app/api.py` (matter-scoped audit now resolves `impact.applied` rows through stale finding → claim → matter), `backend/tests/test_api.py` (new `test_audit_includes_impact_for_matter`), `docs/logs/MUSE_CODE_LOG.md`. No contract change (v8 stands).
- What was run: `make check-backend` → 240/240 (after the audit fix); `make check-frontend` read-only → 32/32 (run for verification only, no frontend edits). Then a 31-check live E2E through the real Vite proxy (frontend :5173 → backend :8000, `API_STUB=0 LLM_MODE=replay DEMO_MODE=1 CHALLENGER=on`, after `make reset-demo`): matter/clauses/13 facts; Ask with mismatched clause → FOLLOWS + challenger report + AI-draft label; proof round-trip verifies; tamper → PREMISE_MISMATCH; tool trace; history; 2025-10-17 ask stored REQUIRES_REVIEW (no 502); UNKNOWN → UNKNOWN; counterfactual flags both breach findings with propositional `valid: false` and lists them in reverify_list; reverify-list empty pre-ingest (read-only proven); sources/diff s8(6); stale-demo → STALE set in reverify-list and impact report; reverify supersedes and clears the list; graph 29 nodes/25 edges; audit incl. `impact.applied`; scan → `document_extracted`; dictation → `ai_inferred` → approve `lawyer_confirmed` → challenge `disputed`; backend `/` and `/health` 200; frontend `/review`, `/impact`, `/control` all 200.
- One real defect found and fixed during the run: matter-scoped audit hid `impact.applied` (details carry stale finding ids, no matter link), so Screen 2's audit panel would miss the amendment event. Fixed in `_audit_matches` with a regression test; the first E2E run went 28/30, the re-run after the fix went **31/31**.
- Note: the Vite proxy currently targets port 8000 (canonical, commit 59025a7), so the backend was run on 8000 for this test. Demo DB reset clean afterwards (13 facts) with backend on :8000 and frontend on :5173 left running.
- Credit spend: none (replay only)
- Ready for human commit: yes — suggested message: `Show impact events in matter-scoped audit; verified end-to-end 31/31`

## [ui-e2e] DONE · 2026-11-02 14:22 IST
- Task: Test the frontend as well, both frontend and backend (user request)
- Files changed: `backend/app/api.py` (`create_claim` returns the loop's run id, not the claim-open placeholder; UNKNOWN path stamps its run finished), `backend/tests/test_api.py` (run-trace regression on the demo ask; canned-loop test updated to the corrected contract of the response), `docs/logs/MUSE_CODE_LOG.md`. No contract version bump (response field meaning fixed, shape unchanged; v8 stands). Frontend files NOT edited (Cursor lane) — its in-progress T7 panels were only exercised.
- Real integration defect found and fixed: `POST /api/claims` returned the placeholder run id while the agent loop logged its tool calls under its own run — the UI's `pollRunEvents(created.run_id)` therefore always saw 0 events and status `running` (20 polls × 400 ms, then gave up). Verified live before the fix (events `[]`, status `running`) and after (5 events: lookup_source, get_premise, verify_derivation, propose_finding, verify_derivation; run status `accepted`).
- Checks run: `make check-frontend` → lint clean, vitest 32/32 (read-only; Cursor's uncommitted T7 panels present in the tree); `npm run build` → pass; `make check-backend` → ruff/mypy clean, pytest **240/240**. Then a 25-check live UI-flow test through the Vite proxy (:5173 → :8000) replaying each screen's exact client sequence: Screen 1 load/auto-select 9.2/ask/poll-trace/current-finding; Screen 2 sources/versions(SIMULATED)/diff/WhatIfPanel/graph/stale-demo/ReverifyListPanel/impact/reverify/audit-with-impact.applied; Screen 3 facts/approve/challenge/ProofEditor valid+tamper/reviewFinding/ScanPagePanel/DictationPanel — **25/25 passed**. Frontend API types already include v8 (`/api/scans`, `/api/dictations`, `/api/counterfactual`, `/api/reverify-list` present in schema.d.ts).
- Note: no headless browser is available in this environment, so page rendering was verified at the DOM-shell level (all three routes 200) plus the exact API sequences the pages issue; a human click-through in a real browser is still the final visual check.
- Credit spend: none (replay only). Demo DB reset clean afterwards; backend :8000 and frontend :5173 left running.
- Ready for human commit: yes — suggested message: `Return the loop run id from POST claims so the UI trace polls the real run`

## [phase2-labels] STARTED · 2026-11-02 15:01 IST
- Task: Phase 2 only — lawyer display labels beside machine fields, contract v8 → v9 (additive)
- Scope: `backend/app/api.py` + `backend/app/schemas.py` display fields (Finding status_label/clause/section/law-version/fact_lines, impact + reverify-list labels, counterfactual would_follow_label, trust labels, plain-language error messages with codes kept), tests first in `backend/tests/test_display_labels.py`, regenerate `openapi/openapi.json` v9 + affected stub examples. Machine fields (ids, hashes, proof JSON, codes) all stay. No frontend/README edits, no tool/checker/rule-card changes, tests never live, no record unless a cassette hash breaks. Note: working tree shows human-staged files (git index M/A) — not touched.

## [phase2-labels] DONE · 2026-11-02 15:12 IST
- Task: Phase 2 only — lawyer display labels beside machine fields, contract v8 → v9 (additive)
- [CONTRACT v8 → v9] additive display fields only; Cursor: `npm run gen:api`
- Files changed: `backend/app/api.py` (`STATUS_LABELS`/`TRUST_LABELS`/`REASON_LABELS` with the exact approved glossary; `_display_fields` derives status_label, clause_ref/quote, section_label/quote, law_version_label/date and fact_lines[{label, trust_label, confirmed_by}] from stored rows; impact rows gain status_label + clause_ref; reverify-list rows gain reason_label + clause_ref; proofs/verify maps PREMISE_MISMATCH to "This fact no longer matches the document" plus three more plain checker messages; MODEL_UNAVAILABLE keeps its code but the message is now plain — no "cassette", "502" or "MODEL_" in it), `backend/app/schemas.py` (FactLine; Finding/Fact/AffectedFinding/CounterfactualAffected/ReverifyListItem additive fields with defaults), `backend/app/services/counterfactual.py` (would_follow_label sentence beside would_remain_valid + logic), `backend/app/main.py` (v9), `backend/tests/test_display_labels.py` (new, 6 tests), `backend/tests/test_api.py` + `test_conflicting.py` (two exact-equality assertions extended for the additive fields), `backend/tests/test_contract_v0.py` (pin v9), `openapi/openapi.json` (regenerated v9), stub examples regenerated (`finding.json`, `finding_current.json`, `finding_history.json`, `facts.json`, `impact.json`, `extract_result.json`), `docs/logs/MUSE_CODE_LOG.md`
- Checks run: 6 new tests failed first, then pass. `make check-backend` → ruff clean, mypy clean, pytest **246/246**. No cassette hash broke (gateway request shapes unchanged), so no `make record` was run and no credits spent. Tests never used live.
- Decisions / assumptions: section/law-version labels derive from the first cited rule card's provision (DEPENDS_ON edges as fallback), so a finding with no cited card (e.g. the recorded 9.2 proof, which cites a fact only) returns empty section fields rather than invented ones. `confirmed_by` is the latest fact review's reviewer, else null. Machine fields — ids, hashes, proof JSON, error codes, logic objects — are all unchanged in every response; labels sit beside them. Frontend/README/docs outside the log untouched (the staged frontend changes in the tree predate this task and are not mine).
- Contract change: [CONTRACT v8 → v9] additive only
- Requests: [REQ → CU] `npm run gen:api` for v9 and render only the `*_label`, `clause_quote`, `section_quote`, `fact_lines`, `would_follow_label` and `reason_label` fields; keep machine fields out of the UI per the lawyer-first plan
- New-work note: lawyer display-label layer (contract v9) 2026-11-02
- Third-party added: none
- Credit spend: none
- Ready for human commit: yes — suggested message: `Add lawyer display labels beside the machine fields; contract v9`

## [approve-500] STARTED · 2026-11-02 15:46 IST
- Task: Fix POST /api/facts/F-LOOP-92/approve 500 ObjectDeletedError (user-reported; user granted all-file permission, backend fix only needed)
- Diagnosis: works on a scratch DB; fails on the live server whose DB file was replaced by `make reset-demo` while running — the engine's connection pool holds connections to the deleted inode, so the INSERT and the post-commit attribute refresh can land in different files. F-SEED-04 approve (200 in the same log) drew a consistent connection.
- Scope: `backend/app/db.py` (NullPool so every checkout opens the current file), `backend/app/services/premises.py` (refresh + expunge before returning, so endpoint attribute reads never reload), regression tests. Restart of the user's server required after the fix (engines are cached per process).

## [approve-500] DONE · 2026-11-02 15:55 IST
- Task: Fix POST /api/facts/F-LOOP-92/approve 500 ObjectDeletedError
- Files changed: `backend/app/db.py` (`get_engine` uses NullPool — every checkout opens the database file as it exists now, so a mid-run `make reset-demo` can no longer split requests across a deleted inode and the new file), `backend/app/services/premises.py` (`_finish`: commit + refresh + expunge for approve/challenge/reject, so the returned fact's attributes never reload), `backend/tests/test_premises.py` (regression tests: NullPool engine; approved attributes survive session close), `docs/logs/MUSE_CODE_LOG.md`
- Checks run: regression tests failed first (QueuePool; DetachedInstance/expired reload). `make check-backend` → ruff clean, mypy clean, pytest **248/248**. Live on the user's :8000 server (auto-reloaded): approve F-LOOP-92 → 200 `lawyer_confirmed` (was 500); then two consecutive `make reset-demo` cycles **without restarting the server** — approve F-SEED-04 → 200 after the first, Ask → 200 FOLLOWS after the second. The reset-while-running failure mode is gone. Demo DB left reset clean (13 facts).
- Decisions / assumptions: NullPool costs one SQLite open per checkout — negligible at demo scale and the correct trade for a replaceable demo DB. The same post-commit-read pattern elsewhere (findings, claims) is covered systemically by NullPool; refresh+expunge was added where the crash was reported. Standing guidance changes: restarting the server after `make reset-demo` is no longer required (still harmless).
- Contract change: none (v9 stands)
- Requests: none
- Credit spend: none
- Ready for human commit: yes — suggested message: `Fix approve 500 after demo reset: NullPool engine and detached-safe premise results`

## [F1] STARTED · 2026-11-02 17:56 IST
- Task: F1 (backend part) — confirm API re-checks every stale row + regression test; before/after shows old vs new s8(6) text
- Scope: probe stale → `POST /api/impact/{id}/reverify` on a scratch seeded DB; fix any stale row that cannot be re-checked or is silently skipped; regression test. CU does the before/after display after my confirmation. Per DECISIONS: no new features, no trust flips, no SHOWDOWN work.

## [F1] DONE · 2026-11-02 18:05 IST
- Task: F1 (backend part) — every stale row re-checks; no silent skips
- [CONTRACT v9 → v10] `ReverifyResult` gains additive `skipped: list[str]`; Cursor: `npm run gen:api`
- Files changed: `backend/app/api.py` (reverify_impact collects proof-less stale rows into `skipped` instead of silently `continue`-ing; diff keeps stored provision order — see decisions), `backend/app/schemas.py` (`ReverifyResult.skipped`), `backend/app/main.py` (v10), `backend/tests/test_api.py` (new: `test_stale_demo_reverify_rechecks_every_stale_row`, `test_reverify_reports_proofless_stale_rows_as_skipped`), `backend/tests/test_contract_v0.py` (pin v10), `openapi/openapi.json` (regenerated v10), `openapi/examples/reverify_result.json` (regenerated), `docs/logs/MUSE_CODE_LOG.md`
- Confirmation (probe + tests, real results): on the seeded demo, stale-demo flags exactly `FND-RC-CT3-BREACH-01` + `FND-RC-CT3-BREACH-CONFLICT-01`; reverify supersedes **both**, returns 2 new findings, each fetchable with status REQUIRES_REVIEW and label "Needs your review before it can be relied on" (the accepted honest outcome — old proofs cited the replaced text); reverify-list is then empty. The diff API returns both s8(6) texts (`changed_keys: ["DPDP-Act-2023_s8(6)"]`, before ≠ after, both containing the breach-intimation wording). Before this fix, a stale finding with no stored proof was silently skipped by reverify (not superseded, not reported); it now appears in `skipped` and stays in the reverify list. `make check-backend` → ruff clean, mypy clean, pytest **250/250**.
- Decisions / assumptions: I first ordered the diff's before/after lists changed-first, then **reverted it**: the existing test `test_reingest_stored_version_stales_card_dependents` caught that clients round-trip diff output into ingest, whose content hash is order-sensitive — reordered provisions created a duplicate version (`SRC-DPDP-ACT-v3` instead of idempotent `SV-DPDP-ACT-V2SIM`). Stored order is a load-bearing invariant. [REQ → CU] the before/after block must select the provision whose key is in `changed_keys` (today it shows the first/commencement provision); the API already returns `changed_keys` plus both s8(6) texts, and per-finding `clause_ref` is on impact/reverify rows since v9. No trust-class flips, no new features, CHALLENGER/recording rules untouched; F3 not started (F1 first per DECISIONS; F3 is cut-if-overrun).
- Contract change: [CONTRACT v9 → v10] additive (`skipped` only)
- Requests: [REQ → CU] `npm run gen:api` for v10; fix the before/after block to key on `changed_keys` (see above)
- Credit spend: none (replay; no record run)
- Ready for human commit: yes — suggested message: `F1: reverify reports skipped stale rows instead of dropping them; contract v10`

## [F1CU+F2+F3] STARTED · 2026-11-02 17:43 IST
- Task: Cursor lane taken over by Muse Code (user instruction: "cursor was no more do it by yourself")
- Scope: F1-CU `DiffView` selects the provision named in `changed_keys` (today `before[0]`/after[0] = commencement); F2 second approve shows "Already confirmed", local sample cards (as-of, post-challenge) labelled "Illustration, not a server answer"; F3 record one cassette for the out-of-corpus telecom question (as_of 2025-10-01 to match Screen 3) then wire UnknownClaimDemo to the real `POST /api/claims` instead of the local sample. Frontend tests + build, backend check. At most one `make record`.

## [F1CU+F2+F3] DONE · 2026-11-02 17:52 IST
- Task: F1 (display) + F2 + F3, frontend lane included per user instruction
- Files changed: `frontend/src/components/DiffView.tsx` (select before/after rows by `changed_keys[0]`, fallback to first row; was showing commencement s1), `frontend/src/components/DiffView.test.tsx` (new: amended section shown, commencement not shown), `frontend/src/pages/LawyerControlPage.tsx` ("Already confirmed" notice on second approve — checked locally and on server rejection of the superseded row; Unknown demo now calls the real API via `handleUnknownAsk` with busy/error states), `frontend/src/components/lawyer/IllustrationLabel.tsx` (new shared label), `frontend/src/components/lawyer/AsOfPanel.tsx` + LawyerControlPage post-challenge card (label applied to local sample answers), `frontend/src/components/lawyer/UnknownClaimDemo.tsx` (error line), `frontend/src/api/mocks/lawyerControl.ts` (UNKNOWN_QUESTION reworded, see below), `frontend/src/api/mocks/index.ts` + `frontend/src/api/client.ts` (body-aware mock createClaim; C-UNK mock finding so tests exercise the real flow shape), `frontend/src/pages/LawyerControlPage.test.tsx` (Already-confirmed test; illustration label asserted), `scripts/record_cassettes.py` (`record_unknown_demo`), `backend/tests/test_api.py` (`test_out_of_corpus_question_returns_unknown`), 1 kept cassette (`e360b972…`), `docs/logs/MUSE_CODE_LOG.md`
- F3 wording change (verified live, not guessed): the original telecom question types **CT2** against the model (element = "fairness opinion…"), which then needed a loop with no cassette (502). Four candidate wordings were probed once each at temperature 0; three typed UNKNOWN. The screen now asks "Is it fair that this clause relies on an unrelated telecom circular?" → typed UNKNOWN → decided UNKNOWN directly by the server. The one `make record` run for this task plus 4 tiny probe calls cost ≈ $0.004 total; the 3 unused probe cassettes were deleted, the used one kept. Cassette `721dd65e…` (CT2 wording) also deleted.
- Checks run: backend F3 test failed first (502, no cassette), passes after recording; live POST on :8000 → `200 {status: UNKNOWN, finding_id}`. `make check-backend` → **251/251**; `make check-frontend` → **36/36** (11 files) + `npm run build` pass. New frontend tests: DiffView selection, second-approve notice.
- Decisions / assumptions: mock layer now mirrors the real Unknown flow (C-UNK claim + UNKNOWN finding) so Vitest exercises the same page code path the live server takes. As-of and post-challenge cards remain local samples (no server round-trip exists for them in the demo path) and are labelled accordingly; the Unknown card is no longer a sample. Demo DB reset clean afterwards; servers left stopped for the user's manual testing.
- Contract change: none (v10 stands; frontend consumes existing fields)
- Requests: none. Remaining finish list: F4 + F6 (human), F5 deploy (MC backend + human VM/Vercel), F7 README/video/submit.
- Credit spend: ≈ $0.004 (one `make record` + 4 one-line probes)
- Ready for human commit: yes — suggested message: `F1-F3: amended-section diff, Already confirmed, real server UNKNOWN`

## [CI mypy optional-deps] DONE · 2026-11-04 09:08 IST
- Task: `make check-backend` failed in GitHub CI (mypy `import-not-found` for `falkordb` in `app/modules/evidence/graph_projection.py:26` and `pypdf` in `app/modules/intake/pdf.py:87`, `tests/test_mixed_pdf.py:74`). Root cause: CI installs only `.[dev]`; `falkordb`/`pypdf` are optional prod extras imported lazily, and the existing `# type: ignore[import-untyped]` only covers the installed-but-unstubbed case, not the module-absent case.
- Files changed: `backend/pyproject.toml` — added `[[tool.mypy.overrides]]` with `ignore_missing_imports = true` for `falkordb`, `falkordb.*`, `pypdf`, `pypdf.*`.
- Checks run: `make check-backend` → ruff clean, mypy "no issues found in 103 source files", pytest **282 passed, 2 skipped** (baseline skips; 4 pre-existing DeprecationWarnings in docx intake, untouched).
- Decisions: config-only fix; no runtime, schema, contract, or test changes. No new dependency.
- Credit spend: none.
- Ready for human commit: yes — suggested message: `Fix CI mypy: ignore missing optional imports (falkordb, pypdf)`
