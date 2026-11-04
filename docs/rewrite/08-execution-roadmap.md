# 08 — Execution roadmap (Option B, both sides)

Owner granting this rewrite waived lane restrictions for this work; the
only standing rule is **no commits** (the human commits). Order below is
dependency-driven; each phase ends green (lane checks + its gate) before
the next starts. The v10 demo path stays runnable throughout.

## P0 — Safety and scaffolding ✅ DONE (2026-11-02)
- Monorepo layout kept; domain boundaries added as facade packages in
  `backend/app/modules/` (identity, matters, verification, law, impact,
  intake, evidence) re-exporting today's implementations — structural
  split only, zero behaviour moved. Dependency rules (no domain imports
  the HTTP layer; only verification decides status) enforced by
  `backend/tests/test_module_boundaries.py`.
- Contract v10 frozen (`openapi/FREEZE.md`); additive v11 draft opened
  at `openapi/openapi.v11-draft.json` (33 paths, `v11-draft`).
- Gate evidence: `make check-backend` 253/253 (ruff, mypy, pytest,
  incl. 2 new boundary tests), `make check-frontend` 36/36 + lint clean.
  Demo behaviour unchanged (facades are import-only).

## P1 — Data layer (Postgres + graph projection) ✅ DONE (2026-11-02)
- `tenants` table + `tenant_id` (default `demo`) on matters, documents,
  facts, claims, findings, audit_log; law tables stay global.
  `app.modules.identity` holds `DEMO_TENANT_ID`, `ensure_tenant`,
  `tenant_query`. Seed creates the demo tenant.
- Engine is dialect-portable: `CLAUSETRACE_DB_URL` picks any SQLAlchemy
  URL (NullPool kept for SQLite files); `init_engine` shared by both.
- SQLite → Postgres migration (`scripts/migrate_sqlite_to_postgres.py`,
  idempotent) verified against a real Postgres 16 container: full table
  parity on the seeded demo, spot-checked evidence integrity.
- Graph projection to **FalkorDB** (dev environment's graph DB;
  `app.modules.evidence.graph_projection`): rebuild-from-record project
  + traversal with parity test against the record-side traversal.
- Drivers are an optional `prod` extra (`psycopg[binary]`, `falkordb`);
  the demo path needs neither. Infra tests are env-gated
  (`CLAUSETRACE_PG_URL`, `CT_GRAPH_TEST`) and skip cleanly without them.
- Gate evidence: default suite 255 passed + 2 skipped (infra gates);
  with infra env set, **257/257 passed** incl. PG parity and graph
  parity. Demo behaviour unchanged (SQLite default).

## P2 — Service split ✅ DONE (2026-11-02)
- Real code moved behind the P0 facades: evidence (graph, premises),
  law (sources, rulecards, diff), verification (memory — behaviour
  untouched), impact (impact, reverify, counterfactual), intake
  (extract, scan, transcribe), matters (seed). Old `app.services.*` /
  `app.agent.{extract,scan,transcribe}` paths are typed compatibility
  re-exports, so no caller or test changed its import.
- Two move hazards found and fixed by tests: package-`__init__` import
  cycles (shims now import submodules directly; an alias-shim variant
  also broke mypy and was replaced), and `Path(__file__).parents[N]`
  corpus paths shifting one level with the deeper packages.
- Domain events between modules (`app/core/events.py`):
  `finding.decided`, `fact.approved/challenged/rejected`,
  `impact.applied` — synchronous, handlers fail loudly, bus carries
  notifications only (status decisions stay in verification.memory).
- Gate evidence: `make check-backend` 257 passed + 2 infra skips
  (ruff/mypy clean), `make check-frontend` 36/36. Contract files
  untouched for ported endpoints (v10 surface identical).

## P3 — Intake pipelines (async) ✅ DONE (2026-11-02)
- Job framework: `intake_jobs` table + `app.modules.intake.jobs`
  (queued → running → done/failed with the failure recorded on the row);
  `POST /api/matters/{id}/documents/upload` stores the document and
  queues extraction (background worker), `GET /api/jobs/{id}` reports
  progress. The sync extract endpoint and the worker share one write
  path (`extract_and_store`).
- PDF pipeline (`app.modules.intake.pdf`): per-page text layer via
  pypdf; image-only pages detected (< 40 chars) and routed to vision
  (pdftoppm render → scan path). Typed `PdfError` for bad files.
- Lawyer correction: `POST /api/facts/{id}/correct` — new row, edited
  wording, same trust class, old row kept, `fact.corrected` event.
- Gate (tests, replay): a **non-seeded variant DPA** (Beacon/Stratus,
  corpus/contracts/variant_dpa.md, extraction cassette recorded once)
  uploads → job done with 12 clauses + document_extracted facts →
  correction → approval → checker-valid proof citing the approved
  corrected fact. Job failure is recorded, never silent.
- `[CONTRACT v10 → v11]` additive (upload, jobs, correct); FREEZE.md
  updated. Gate evidence: `make check-backend` 260 passed + 2 skips.

## P4 — Frontend rebuild ✅ DONE (2026-11-02, admin deferred to P5)
- Types regenerated from contract v11 (`npm run gen:api`); client gained
  `findingHistory`; mocks mirror the new history flow.
- Design system consolidated: existing CSS-var tokens kept, new shared
  primitives in `components/ui/` (Panel, Button, QueueList) with the
  lawyer-workflow pages built on them.
- New routes: `/` **Your matters** (matter home with the three workflow
  entries; replaces the redirect) and `/evidence/:findingId`
  (**Evidence for this answer**: verdict, reasoning, facts relied on
  with trust labels, earlier versions). FindingCard links to evidence.
  The three workflow screens (Review a clause / Law changes / Your
  control room) were retained — they already implement the lawyer-first
  design on v9+ display fields — rather than rewritten for its own sake.
- Tests: App coverage for both new routes, FindingCard renders wrapped
  in a router (evidence link), an async-race flake in the evidence test
  found and made deterministic. `make check-frontend` 38/38 + build
  pass; live routes all 200 through the Vite proxy.
- Zero-technical-strings sweep over the new UI source: clean.
- **Deferred:** Admin console (members/budgets/eval) — no admin API
  exists yet; it lands in P5 with the eval harness it displays.

## P5 — Hardening and release ✅ DONE (2026-11-02)
- **Eval harness (release gate):** `corpus/evals/golden.json` +
  `app.agent.evals` + `scripts/run_evals.py` — 5 golden cases (ask
  FOLLOWS, two UNKNOWN shapes, counterfactual invalid, decoy) with
  verdict agreement, premise-admission violations (must be 0) and
  spend; exit code gates the release. Green: 5/5, 0 violations.
- **Budgets:** `app.agent.budgets` — per-tenant spend from `llm_calls`,
  `CT_TENANT_BUDGET_USD` limit enforced at the live loop entry (loud
  typed error, replay never trips it).
- **Performance:** checker budget test (< 10 ms/proof, measured over
  50 runs); a same-second version-timestamp flake in latest-version
  ordering was found by the P3 gate test and fixed (monotonic version
  stamps in the intake write path).
- **Admin surface (deferred from P4):** `GET /api/admin/overview`
  (counts by status/trust, spend, jobs) + internal `/admin` page,
  clearly labelled not part of the lawyer workflow.
  `[CONTRACT v11 → v12]` additive.
- **Drills + runbooks:** graph rebuild parity re-run green against
  FalkorDB; eval gate re-run green; `docs/rewrite/09-runbooks.md`
  (model outage, budget, amendment failure, graph rebuild, key
  rotation, restore, demo reset).
- Gate evidence: backend 264 passed + 2 infra skips; frontend 39/39;
  production build passes.

## P-A — Vision sending efficiency ✅ DONE (2026-11-02)

Sending order for scanned pages: pypdf text layer first (free, exact);
image-only pages are rendered at **150 DPI**, grayscaled, contrast-normalised
and JPEG-encoded (q70) by `app/modules/intake/vision_prep.py` (`prepare_page`
returns bytes + content hash), then sent as one structured `emit_scan` call
per page (`media_type="image/jpeg"`, supported by the scan gateway).

Measurement on fictional clause fixtures (normal 26pt + dense 14pt pages),
Muse Spark vision, temperature 0: clause-body accuracy was **identical and
verbatim at every setting** (100/150/200 DPI × PNG/JPEG), so payload decides —
JPEG is ~3x smaller than PNG (150 DPI: 24–38 KB vs 66 KB; 200 DPI PNG: 114 KB).
150 DPI keeps headroom for dense real-world print over 100 DPI at ~2x the bytes.
Identical prepared pages share gateway cassettes by content hash, so re-running
a job never re-pays a transcribed page. Cost: 8 small live calls (~$0.002).
Side finding: uniform-14pt fixture headings caused a measured "8.4"→"B.4"
vision misread of the ref field; fixtures now render headings larger/bolder,
as in real documents (body transcription was always exact).
Follow-up (efficiency hardened): the worker and `extract_pages` now render
all vision pages in **one** pdftoppm call (`prepare_pages` /
`transcribe_vision_pages`) instead of one fork per page — byte-identical
JPEGs (proven per-page equal), so no cassette churn. Measured on a 4-page
scan: 0.13s vs 0.15s. Honest note: fork overhead was never the bottleneck
(pdftoppm renders fast); the win is modest, and model calls still dominate
job cost. Fixed along the way: pdftoppm numbers outputs by document page
(not sequentially from `-f`), and autocontrast was confirmed as the earlier
misread's cause and stays out (grayscale JPEG only).
Gate evidence: `test_vision_prep.py` (5 tests: size, hash, replay accuracy,
PDF vision route, batch==per-page) + `make check-backend` **282 passed +
2 skips**.

## P-B — DOCX support ✅ DONE (2026-11-02)

- `app.modules.intake.docx` (stdlib zip + XML only): paragraphs in order
  with styles, tables inline, clause split on `Heading*` styles or
  `9.2 Title` lines — the same ref rule as `parse_contract`, so a DOCX
  and its text twin yield identical clauses. Legacy `.doc` is rejected
  with a plain typed message (no conversion dependency added).
- Upload endpoint accepts
  `application/vnd.openxmlformats-officedocument.wordprocessingml.document`
  (base64, unchanged transport); `.doc` maps to the typed refusal.
- Gate evidence: `test_docx.py` (5 tests: twin parity, style-less
  headings, bad-file/empty rejection, legacy refusal, upload round-trip)
  + `make check-backend` **278 passed + 2 skips**.

## P-C — Mixed-PDF hardening ✅ DONE (2026-11-02)

- `classify_pages` separates text vs scan pages without model calls; the
  worker transcribes vision pages with per-page `stage: "page i of n"`
  progress and records `{page, source}` in the job result; the joined
  document text carries `--- page N ---` markers (never quoted) so
  extraction segments per page; vision pages keep their `ref heading`
  prefix so the joined text stays self-describing.
- Measured corrections along the way: autocontrast damages small print
  (removed — grayscale + JPEG only); the generic extraction prompt needed
  an explicit per-page coverage line; identical adjacent pages invite
  model merging (fixtures now use distinct topics, as real documents do).
- `GET /api/documents/{id}/pages` exposes the page map for spot-checking.
- Gate evidence: `test_mixed_pdf.py` (text+scan in one file → 2 clauses,
  per-page origins, job progress) + `make check-backend` green.

## P-D — Contract + UI for uploads ✅ DONE (2026-11-02)

- `[CONTRACT v13 → v14]` additive: `DocumentPages`, `UploadResult` /
  `JobStatus` already declared; the pages endpoint is the new path.
- UI: `UploadPanel` (PDF/DOCX/TXT file pick → upload → job polling with
  per-page stage → per-page origin list → link to clauses) on the matters
  page; `ClausesPage` shows per-page origins ("read from the file" /
  "transcribed from a scan") above the wording editor; sign-in page +
  token auth on every request; dictation page (mic → transcribe → save
  as proposed → confirm); clause update with typed or dictated wording.
- Gate evidence: `make check-frontend` 44/44 + production build;
  `make check-backend` 280 passed + 2 skips.

**Rewrite P0–P5 complete.** Remaining is owner work: commit the lanes,
then the pilot decisions in SHOWDOWN §12 (design partners, data terms,
legal review) before any external user touches the new stack.

## Risks and mitigations (retained)
- Eval harness + golden matters as a release gate; budgets/alerts;
  performance pass against doc 06 budgets; security checklist (doc 07);
  runbooks; staging soak.
- Gate: eval thresholds met; load test within budgets; restore +
  graph-rebuild drills done.

## Risks and mitigations
- **Deadline/judging:** the submitted demo is a tagged, frozen commit; the
  rewrite never lands on top of it until the owner says so.
- **Scope creep:** docs 01–08 are the contract for this rewrite; anything
  not in them needs a doc change first.
- **Graph drift:** parity tests + rebuild drill; Postgres fallback path
  retained until Neo4j proves itself for two consecutive phases.
- **Model cost during development:** replay-first; live only behind the
  eval smoke set; every task logs spend.

## Definition of done (whole rewrite)
Staging demonstrates the §13 cold-start flow from the SHOWDOWN plan on the
new stack, E2E + evals green, and the demo tenant still replays the
original hackathon path byte-for-byte.
