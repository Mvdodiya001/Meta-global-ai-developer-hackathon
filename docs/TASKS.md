# ClauseTrace — Task Plan (8 build days + 1 buffer day)

Rules: one task = one agent session (≈30–90 min). Write the listed tests first. A task is done only when its "Done when" lines pass, the lane check is green (`make check-backend` for MC, `make check-frontend` for CU), and the agent has logged it in `docs/logs/`. Owners: **MC** = Muse Code, **CU** = Cursor, **H** = you (human).
**Agents never commit** (no co-author lines either); H commits per lane. Who does what each day, sync points, and logging: see `PLAN.md`.
Rubric tags: I = Impact, M = Meta tooling, T = Technical depth, D = Demo.

## Calendar (relative days; Day 1 = the day you start)
| Day | Focus |
|-----|-------|
| 1 | Setup, Meta credits, hello-world, corpus; MC: contract v0 + stub; CU: UI foundation |
| 2 | Schema, sources, rule cards, contract → **SP1 (contract v1)** |
| 3 | MC: gateway, extraction, claims, checker core · CU: Screen 1 on mocks |
| 4 | MC: checker steps, tools, agent loop, memory service → **SP2 (vertical slice)** · CU: finish Screen 1, start Screen 2 on mocks |
| 5 | MC: graph, impact, re-verify, premise challenge, API (SP3) · CU: finish Screen 2, Screen 3 on mocks |
| 6 | MC: challenger, API gap fixes · CU: wire UI to real API. **Core gate at end of day** |
| 7 | Reliability, deploy, rough video, judge simulation, **feature freeze** |
| 8 | README, final video, X post, **submit** |
| 9 (buffer) | Fixes and link re-checks only |
Use the Discord office hours for blockers. Join or watch the hackathon's agent sessions when you can.

---
## M0 — Setup (Day 1)
- [x] **T0.1 Repo and new-work evidence** (H) · I/T
  - Create public GitHub repo, LICENSE (MIT or Apache-2.0), README stub, `AGENTS.md`, `docs/*`, `NEW_WORK.md`, `NOTICE.md`, `.gitignore`, `.env.example`.
  - Done when: first commit exists **before any code**; repo opens in a logged-out browser.
- [x] **T0.2 Credits and accounts** (H) · M
  - Claim $150 Meta credits (add card, set the spend-limit notification); join Discord, post in #intros.
  - Partner credits (Baseten, Modal, Fireworks) are **not needed** for the core. Optional: submit the request forms if they are still open, only for T7.5.
  - Done when: Billing page shows the Meta credits.
- [x] **T0.3 Meta API hello-world + cost calibration** (MC) · M
  - Files: `scripts/hello_meta.py`. Call `https://api.meta.ai/v1/responses` with `muse-spark-1.3`; do one function-call round trip.
  - Done when: tool call works; tokens and cost per call recorded in `PROGRESS.md` (this sets the daily budget).
- [x] **T0.4 Scaffold and CI** (MC backend, CU frontend) · T
  - Tests first: `tests/test_health.py`. FastAPI `/api/health`, pytest, ruff, mypy, Vite app, `Makefile`, GitHub Actions.
  - Extend the starter `Makefile` (MC) so `check-backend` and `check-frontend` work.
  - Done when: both lane checks green locally and in CI; logged in each agent's log.
- [x] **T0.6 Verify the corpus** (H) · I/T
  - Download official DPDP Act 2023, DPDP Rules 2025 and the commencement notification(s) from India Code / MeitY. Record URL + retrieval date in `NOTICE.md`.
  - Pick 5–8 provisions and a decoy source S4. Write `corpus/NOTES.md`: provision key, exact text, commencement/effective dates. Check every section number and date yourself.
  - Done when: the table is complete and every item is traceable to an official page.
- [ ] **T0.7 Contract v0 + stub mode** (MC) · T/D — Deps: T0.4
  - Files: `openapi/openapi.json`, `openapi/examples/*.json`. Pydantic response models for every endpoint in `DATA_MODEL_API.md` §7; stub mode `API_STUB=1` returns the examples (clause list, finding with proof, impact report, graph slice, audit rows, facts with trust classes).
  - Done when: `curl localhost:8000/api/health` and one stubbed endpoint work; `info.version` is `v0`; logged as `[CONTRACT v0]`. Contract v1 (SP1) follows at the end of Day 2.
- [x] **T0.8 Install git guards** (H) · process — Deps: T0.1
  - Run `make hooks`. Test: a plain `git commit` is blocked; `git hc -m "..."` works; a message with a co-author line is blocked.
  - Done when: all three behave as described. Check Cursor and Muse Code settings for any auto-commit or attribution option and turn it off.

## M1 — Sources and corpus (Day 2)
- [ ] **T1.1 Schema + append-only triggers** (MC) · T — Deps: T0.4
  - Tests first: UPDATE/DELETE on `findings`, `source_versions`, `provisions`, `audit_log` raise.
  - Done when: all tables from `DATA_MODEL_API.md` §2 exist; trigger tests pass.
- [ ] **T1.2 Source snapshots + provisions** (MC) · T — Deps: T0.6, T1.1
  - Files: `app/services/sources.py`, `corpus/raw/`. Store hashed versions; load cleaned text for the chosen provisions; add simulated v2 (`is_simulated=true`) and decoy.
  - Done when: v1, v2, decoy loaded; sha256 stable; ingest of identical content is idempotent.
- [ ] **T1.3 Rule cards** (MC, H reviews) · T/I — Deps: T1.2
  - Files: `corpus/rulecards/*.yaml`, loader. 6–8 cards covering CT1–CT3, each citing a verbatim span.
  - Tests first: a card whose span is not in the snapshot is rejected.
  - Done when: all cards load; every span verifies; H has read each card against the official text.
- [ ] **T1.4 Fictional contract + matter seed** (MC) · D — Deps: T1.1
  - Write the ~12-clause Master DPA (Acme Retail Pvt Ltd / Nimbus Analytics Pvt Ltd), matter, one hearing date, one task (labelled demo data). `make seed`, `make reset-demo`.
  - Done when: reset-and-seed completes in under 60 s.
- [ ] **T1.5 Diff + as-of applicability** (MC) · T — Deps: T1.2
  - Tests first: diff by provision key and hash; `in_force(as_of)` before/after commencement.
  - Done when: both tests pass for v1→v2.

## M2/M3 — Extraction, checker, agent (Days 3–4)
- [ ] **T2.1 LLM gateway** (MC) · M/T — Deps: T0.3
  - `live|replay|mock` modes, request-hash cache, `llm_calls` logging, caps.
  - Tests first: replay returns identical output; live blocked under pytest.
- [ ] **T2.2 Clause extraction** (MC) · M — Deps: T2.1, T1.4
  - Muse Spark structured output → clauses + candidate facts (`document_extracted`) with spans.
  - Done when: all 12 clauses extracted; spans match the contract text; cassette recorded.
- [ ] **T2.3 Question → typed claim** (MC) · M — Deps: T2.1
  - CT1–CT4; anything else returns UNKNOWN with explanation.
  - Done when: 3 supported and 2 unsupported sample questions behave correctly.
- [ ] **T3.1 Checker core** (MC) · T — Deps: T1.3
  - Tests first: schema/order, admission rules (rejects `ai_inferred`, `disputed`), span substring + hash, `tests/test_checker_isolation.py` (AST scan).
  - Done when: all pass.
- [ ] **T3.2 Checker step kinds** (MC) · T — Deps: T3.1, T1.5
  - `cite_fact`, `cite_rule`, `in_force`, `compare`, `contains_element`, `role_applies`, `conclude`; CLI `python -m checker verify proof.json`.
  - Tests first: valid proof passes; tampered premise, wrong value, out-of-force provision, superseded version each fail with a specific code.
- [ ] **T2.4 Six tools** (MC) · T/M — Deps: T1.2, T3.2
  - Schemas exactly as `DATA_MODEL_API.md` §4; matter scoping; limits; logging to `tool_calls`.
  - Tests first: cross-matter access rejected; 13th call rejected; unknown tool rejected.
- [ ] **T2.5 Agent loop** (MC) · M — Deps: T2.2–T2.4
  - Responses-API function calling, proof-drafting prompt, tool trace stored.
  - Done when: agent produces a proof for clause 9.2 that `verify_derivation` accepts (live once, then cassette).
- [ ] **T3.3 Memory service** (MC) · T — Deps: T2.5
  - Status decision + confidence band, finding write, edges, audit, re-query check.
  - Tests first: model cannot set status; stale-version proof rejected; each status path (FOLLOWS, RULED_OUT, UNKNOWN, REQUIRES_REVIEW).
- [ ] **T5.0 UI foundation on mocks** (CU) · D — Deps: T0.4 (parallel, Days 1–2)
  - Layout, design tokens, disclaimer banner, routes for Screens 1–3, mock handlers fed from `openapi/examples/` (or `API_STUB=1` once T0.7 exists). Shared components on mock data: FindingCard, TrustChip, ProofSyllogism, DiffView, StaleGraph, AuditList, badges (AI draft / Lawyer-reviewed / SIMULATED).
  - Done when: all three screens render with mock data; banner on every screen; `make check-frontend` green.
- ✅ **Milestone: vertical slice (end of Day 4):** CLI `python -m app.cli verify --clause 9.2 --question "..."` stores a checked finding with traces.

## M4 — Graph and impact (Day 5)
- [ ] **T4.1 Edges + reverse traversal** (MC) · T — Deps: T3.3
  - Tests first: changed provision → only dependent findings; decoy → none; unrelated provision → none.
- [ ] **T4.2 Impact engine** (MC) · T/D — Deps: T4.1, T1.5
  - Ingest → diff → `AFFECTS` → `STALE` events → impact report. Done when: fixture flags exactly the expected findings (G3), in under 2 s (G5).
- [ ] **T4.3 Re-verify + re-query enforcement** (MC) · T — Deps: T4.2
  - New finding supersedes old; old kept; unchanged outcome audited; rejection if no fresh lookup.
- [ ] **T4.4 Premise challenge/approve** (MC) · D — Deps: T4.1
  - Flow C; trust-class change creates a new fact row; recompute dependents.
- [ ] **T4.5 API endpoints + contract** (MC) · T — Deps: T4.2–T4.4
  - All endpoints from `DATA_MODEL_API.md` §7; regenerate `openapi/openapi.json`; log `[CONTRACT vN → vN+1]` in `MUSE_CODE_LOG.md` so CU regenerates types.

## M5/M6 — UI (built on mocks from Day 3, wired on Day 6) and challenger
- [ ] **T5.1 Screen 1: clause review** (CU, Days 3–4, on mocks) · D — Deps: T5.0
  - Clause list, ask box, live tool trace (SSE or polling), finding card, syllogism, source trace, premise trace, "what would change my answer", AI-draft/Lawyer-reviewed badge.
- [ ] **T5.2 Screen 2: source change and impact** (CU, Days 4–5, on mocks) · D — Deps: T5.0
  - Version picker, side-by-side diff, React Flow graph with stale highlight, before/after split, Re-verify button, audit panel, SIMULATED badge.
- [ ] **T5.3 Screen 3: lawyer control** (CU, Day 5, on mocks) · D/I — Deps: T5.0
  - Facts with trust chips, approve/challenge, recompute, unknown demo, as-of date control, proof editor for the tamper demo (`POST /proofs/verify`).
- [ ] **T6.1 Challenger (Muse Spark second pass)** (MC) · M — Deps: T3.3
  - `muse-spark-1.2` with a different prompt returns structured objections; flag `CHALLENGER=on`; provider switch `CHALLENGER_PROVIDER=meta` (default); cassette. Done when: an objection forces REQUIRES_REVIEW in a test.
- [ ] **T6.2 Challenger in UI + README note** (CU) · M — Deps: T6.1, T5.1
- [ ] **T5.4 Wire to real API, remove mocks from demo path** (CU, Day 6) · D — Deps: T5.1–T5.3, T4.5
- ✅ **Core gate (end of Day 6):** the full demo path runs end to end on real API in replay mode. If not green: stop all stretch work, fix core on Day 7.

## M7 — Stretch (only if the core gate is green; pick ONE on Day 7 morning)
- [ ] **T7.1 Voice dictation → proposed fact** (Muse Voice Transcribe, approval gate) · M
- [ ] **T7.2 Scanned page → text** (Muse Spark PDF/image input) · M
- [ ] **T7.3 Counterfactual mode** (read-only graph traversal) · T/D
- [ ] **T7.4 CONFLICTING state** (two rule cards) · T
- [ ] **T7.5 Open-weights challenger (optional)** (MC + H) · M — Needs partner access (Baseten or Modal; H requests it if the form is still open)
  - Add a provider behind `CHALLENGER_PROVIDER=openweights` using model `meta-models/muse-spark-open-1026` (OpenAI-compatible chat completions); no other code changes. Cassette for replay.
  - Done when: one challenger run succeeds on open weights and the README states exactly where it is used. If access is not granted, skip it; nothing else depends on it.

## M8 — Reliability and deploy (Day 7) — **feature freeze at end of day**
- [ ] **T8.1 Scenario tests** (MC) · T — decoy, future provision, UNKNOWN, tamper, stale chain, matter isolation, source failure, challenger objection.
- [ ] **T8.2 Cassettes + deploy** (MC) · D — Full demo path in replay; Docker Compose on your VM; test from a different network; `make reset-demo` under 60 s.
- [ ] **T8.3 Rough demo video** (H) · D — Record the full 3-minute script once; list what feels slow or unclear.
- [ ] **T8.4 Judge simulation** (H) — Run the judge prompt in `DEMO_AND_SUBMISSION.md` §8 on README + script; apply the top 3 fixes.

## M9 — Submit (Day 8)
- [ ] **T9.1 README as sales document** (CU) · I/M — Structure in `DEMO_AND_SUBMISSION.md` §1. `NEW_WORK.md` complete.
- [ ] **T9.2 Final video** (H) · D — Record, edit, upload; open the link logged-out.
- [ ] **T9.3 X post + thread** (H) · bonus — Draft in `DEMO_AND_SUBMISSION.md` §5; post after submission.
- [ ] **T9.4 Submit (target: end of Day 8, a day before the deadline)** (H) — Checklist in `DEMO_AND_SUBMISSION.md` §4; keep a screenshot of the confirmation.
- Day 9 (buffer): fixes and link re-checks only. No new features.

## Cut order if behind
1. Stretch items (M7). 2. Confidence band → show "not computed". 3. SSE trace → polling. 4. Static matter panel → hide. 5. Challenger → keep (it is cheap and shows well); if it blocks, switch it off with `CHALLENGER=off`. 6. Never cut: checker, impact traversal, re-verify, before/after, UNKNOWN demo, disclaimer, audit trail.

## Daily end-of-day checklist
Both agent logs have final entries · lane checks green (`make check` green for you) · you reviewed diffs and committed by lane (`git hc`) · pushed (`git hp`) · `HUMAN_LOG.md`, `PROGRESS.md`, `NEW_WORK.md`, `NOTICE.md` updated from the logs · credit spend logged · tomorrow's first task named.
