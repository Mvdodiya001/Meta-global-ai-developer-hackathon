# CURSOR_LOG.md — written ONLY by Cursor (append-only)

Cursor: you never commit and never add co-author or "Generated with" text. Log every task here. The human reads this to track your work and decides what to commit.
Time: `TZ=Asia/Kolkata date '+%Y-%m-%d %H:%M IST'`. Heading format must stay greppable: `## [T5.1] DONE · <YYYY-MM-DD HH:MM IST>`.
Status words: STARTED · DONE · PARTIAL · BLOCKED. Special tags in entries: `[REQ → H]`, `[REQ → MC]`, `[CONFLICT]`.
At session start: read `docs/logs/MUSE_CODE_LOG.md` (read-only). If the latest `[CONTRACT vN]` is newer than the one you built against, run `npm run gen:api` first and log it.

## Entry template (copy for each STARTED and final entry)
```
## [Txx.x] STARTED|DONE|PARTIAL|BLOCKED · <time>
- Task: <title>
- Built against: API_STUB | mocks | real API · contract version vN
- Files changed: <path (new|modified|deleted)>, ...
- What changed: <2–4 lines>
- Checks run: `make check-frontend` → pass|fail (<counts or error>)
- Decisions / assumptions: <or none>
- Requests: [REQ → MC] <missing field or endpoint> | [REQ → H] ... | none
- UI rules checked: disclaimer banner present · AI-draft/Lawyer-reviewed badge · SIMULATED badge · status not color-only
- New-work note: <component built, date>
- Third-party added: <name version licence> | none
- Ready for human commit: yes|no — suggested message: `Txx.x: <plain message, no trailers>`
```

---
## Log (newest at the bottom)

## [T0.4] STARTED · 2026-10-29 08:45 IST
- Task: Scaffold and CI (frontend lane)
- Built against: no API contract yet (pre v0)

## [T0.4] DONE · 2026-10-29 08:46 IST
- Task: Scaffold and CI (frontend lane)
- Built against: API_STUB not wired yet · contract pre-v0 (T0.7)
- Files changed: `frontend/` (new scaffold), `frontend/package.json`, `frontend/package-lock.json`, `frontend/vite.config.ts`, `frontend/tsconfig*.json`, `frontend/tailwind.config.js`, `frontend/postcss.config.js`, `frontend/index.html`, `frontend/src/**`, `README.md` (modified), `docs/logs/CURSOR_LOG.md` (modified)
- What changed: Added Vite + React 18 + TypeScript app with Tailwind, oxlint, Vitest, and `src/{pages,components,api}` layout. Minimal HomePage and App smoke test. Root README documents setup and lane checks. `gen:api` script ready for openapi when MC lands contract v0.
- Checks run: `make check-frontend` → pass (oxlint 0 issues; vitest 1/1); `npm run build` → pass
- Decisions / assumptions: React 18 per AGENTS (not Vite template’s React 19). React Flow deferred to T5.x. GitHub Actions CI is MC/human scope (`.github/` outside CU lane).
- Requests: [REQ → H] add `node_modules/` and `frontend/dist/` to root `.gitignore` if not already present
- UI rules checked: disclaimer banner N/A (T5.0); scaffold only
- New-work note: frontend scaffold 2026-10-29
- Third-party added: react 18.3.1 MIT · react-dom 18.3.1 MIT · vite 6.x MIT · vitest 3.x MIT · tailwindcss 3.4 MIT · @testing-library/react 16.x MIT · openapi-typescript 7.x MIT (dev, for gen:api)
## [T5.0] STARTED · 2026-10-29 18:21 IST
- Task: UI foundation on mocks
- Built against: contract v0 · openapi/examples mocks

## [T5.0] DONE · 2026-10-29 18:23 IST
- Task: UI foundation on mocks
- Built against: openapi/examples mocks · contract v0 (`npm run gen:api` refreshed)
- Files changed: `frontend/package.json`, `frontend/package-lock.json`, `frontend/tailwind.config.js`, `frontend/src/index.css`, `frontend/src/main.tsx`, `frontend/src/App.tsx`, `frontend/src/App.test.tsx`, `frontend/src/content/disclaimer.ts`, `frontend/src/api/types.ts`, `frontend/src/api/client.ts`, `frontend/src/api/mocks/index.ts`, `frontend/src/api/schema.d.ts` (regenerated), `frontend/src/components/**`, `frontend/src/pages/ClauseReviewPage.tsx`, `frontend/src/pages/SourceImpactPage.tsx`, `frontend/src/pages/LawyerControlPage.tsx`, `frontend/src/test/setup.ts`, `docs/logs/CURSOR_LOG.md`; removed `frontend/src/pages/HomePage.tsx`
- What changed: App shell with design tokens, disclaimer banner on every route, and react-router paths for Screens 1–3. Mock API layer imports contract v0 examples; shared components (FindingCard, TrustChip, ProofSyllogism, DiffView, StaleGraph, AuditList, status/AI/lawyer/simulated badges) wired on each screen with demo interactions.
- Checks run: `make check-frontend` → pass (oxlint 0 issues; vitest 4/4); `npm run build` → pass; `npm run gen:api` → pass
- Decisions / assumptions: Default data path is bundled examples (set `VITE_USE_LIVE_API=1` for API_STUB backend). React Flow uses `@xyflow/react`; graph is read-only in T5.0. Screen-specific polish (SSE trace, full re-verify) stays in T5.1–T5.3.
- Requests: none
- UI rules checked: disclaimer banner present on all three screens · AI-draft and Lawyer-reviewed badges shown · SIMULATED badge on impact screen · status badges use text + icon (not color-only)
- New-work note: UI foundation + mock screens 2026-10-29
- Third-party added: react-router-dom 7.x MIT · @xyflow/react 12.x MIT
- Ready for human commit: yes — suggested message: `T5.0: add layout, routes, and shared UI components on mocks`

## [T5.1] STARTED · 2026-10-29 19:48 IST
- Task: Screen 1 clause review
- Built against: contract v0 · openapi/examples mocks

## [T5.1] DONE · 2026-10-29 19:50 IST
- Task: Screen 1 clause review
- Built against: contract v0 · openapi/examples + frontend mock run trace
- Files changed: `frontend/src/pages/ClauseReviewPage.tsx`, `frontend/src/pages/ClauseReviewPage.test.tsx`, `frontend/src/components/clause-review/*`, `frontend/src/components/FindingCard.tsx`, `frontend/src/components/FindingCard.test.tsx`, `frontend/src/lib/findingTraces.ts`, `frontend/src/lib/findingTraces.test.ts`, `frontend/src/api/client.ts`, `frontend/src/api/mocks/index.ts`, `frontend/src/api/mocks/runTrace.ts`, `frontend/src/api/types.ts`, `docs/logs/CURSOR_LOG.md`
- What changed: Screen 1 now has selectable clause list, ask box (question + as-of), mock verify flow with progressive tool-trace polling, then finding card, syllogism, source trace, premise trace, and “what would change my answer” panels. API client gained createClaim/runEvents/pollRunEvents; traces derived from finding + facts mocks. Lawyer-reviewed badge demo toggle on finding card.
- Checks run: `make check-frontend` → pass (oxlint 0 issues; vitest 10/10); `npm run build` → pass
- Decisions / assumptions: Full demo tool sequence lives in `runTrace.ts` (v0 `run_events.json` only has 2 steps). Sensitivity hints computed client-side until API exposes them. Live API path uses POST `/api/claims` and GET `/api/runs/{id}/events` when `VITE_USE_LIVE_API=1`.
- Requests: none
- UI rules checked: disclaimer via layout on `/review` · AI-draft default + Lawyer-reviewed demo · status text+icon · SIMULATED N/A on this screen
- New-work note: Screen 1 clause review mock flow 2026-10-29
- Third-party added: none
- Ready for human commit: yes — suggested message: `T5.1: build clause review screen with ask box and tool trace`

## [T5.1] STARTED · 2026-10-29 20:01 IST
- Task: CI fix — findingTraces missing on runner
- Built against: contract v0 · openapi/examples mocks

## [T5.1] DONE · 2026-10-29 20:02 IST
- Task: CI fix — findingTraces missing on runner
- Built against: contract v0 · openapi/examples mocks
- Files changed: `frontend/src/utils/findingTraces.ts` (new), `frontend/src/utils/findingTraces.test.ts` (new), `frontend/src/pages/ClauseReviewPage.tsx` (modified), `frontend/src/components/clause-review/SourceTrace.tsx` (modified), `frontend/src/components/clause-review/PremiseTrace.tsx` (modified), `frontend/src/components/clause-review/WhatWouldChangePanel.tsx` (modified), `docs/logs/CURSOR_LOG.md` (modified). Removed local `frontend/src/lib/` (was never tracked).
- What changed: CI failed because Vite could not resolve `../lib/findingTraces`. Root `.gitignore` line `lib/` (Python packaging template) matches any directory named `lib/`, so `frontend/src/lib/` never entered git even though local `make check-frontend` passed. Moved the module to `frontend/src/utils/` which is not ignored. Did not edit `.gitignore` (outside Cursor lane).
- Checks run: `make check-frontend` → pass (oxlint 0 issues; vitest 10/10); `npm run build` → pass; `git check-ignore frontend/src/utils/findingTraces.ts` → not ignored
- Decisions / assumptions: Relocate rather than change gitignore. Human commit must include `frontend/src/utils/`.
- Requests: [REQ → H] consider narrowing root `.gitignore` `lib/` to `/lib/` so a future `frontend/src/lib` is not silently dropped
- UI rules checked: disclaimer still on `/review` · badges unchanged
- New-work note: none
- Third-party added: none
- Ready for human commit: yes — suggested message: `T5.1: move finding traces off gitignored lib path`

## [T5.2] STARTED · 2026-10-30 18:29 IST
- Task: Screen 2 source change and impact
- Built against: contract v0 · openapi/examples mocks

## [T5.2] DONE · 2026-10-30 18:32 IST
- Task: Screen 2 source change and impact
- Built against: contract v0 · openapi/examples + frontend impact demo overlay
- Files changed: `frontend/src/pages/SourceImpactPage.tsx`, `frontend/src/pages/SourceImpactPage.test.tsx` (new), `frontend/src/components/impact/VersionPicker.tsx` (new), `frontend/src/components/impact/AffectedFindings.tsx` (new), `frontend/src/components/impact/BeforeAfterSplit.tsx` (new), `frontend/src/components/StaleGraph.tsx`, `frontend/src/components/badges/StatusBadge.tsx`, `frontend/src/api/client.ts`, `frontend/src/api/types.ts`, `frontend/src/api/mocks/index.ts`, `frontend/src/api/mocks/impactDemo.ts` (new), `docs/logs/CURSOR_LOG.md`
- What changed: Screen 2 now has source + version pickers, SIMULATED badge when the selected version is simulated, ingest, side-by-side diff, React Flow graph with a 3-of-8 stale summary, affected-findings list, Re-verify, before/after finding split, and audit trail. Decoy source ingest flags no findings. Re-verify keeps FND-001 (FOLLOWS) and adds FND-002 (UNKNOWN).
- Checks run: `make check-frontend` → pass (oxlint 0 issues; vitest 13/13); `npm run build` → pass; `git check-ignore` on new files → not ignored
- Decisions / assumptions: Contract v0 examples only flag one finding; demo overlay in `impactDemo.ts` supplies 8 findings / 3 stale for the demo script. Did not change `openapi/examples/`. Live API still uses `VITE_USE_LIVE_API=1`.
- Requests: none
- UI rules checked: disclaimer via layout on `/impact` · SIMULATED badge on v2 · status text+icon · stale count plus STALE label (not colour-only)
- New-work note: Screen 2 source change and impact mock flow 2026-10-30
- Third-party added: none
- Ready for human commit: yes — suggested message: `T5.2: build source-change impact screen with re-verify split`

## [T5.3] STARTED · 2026-10-30 22:36 IST
- Task: Screen 3 lawyer control
- Built against: contract v1 (will run npm run gen:api) · openapi/examples mocks

## [T5.3] DONE · 2026-10-30 22:39 IST
- Task: Screen 3 lawyer control
- Built against: contract v1 (`npm run gen:api` run) · openapi/examples + frontend lawyer-control mocks
- Files changed: `frontend/src/api/schema.d.ts` (regenerated v1), `frontend/src/api/types.ts`, `frontend/src/api/client.ts`, `frontend/src/api/mocks/index.ts`, `frontend/src/api/mocks/lawyerControl.ts` (new), `frontend/src/pages/LawyerControlPage.tsx`, `frontend/src/pages/LawyerControlPage.test.tsx` (new), `frontend/src/components/lawyer/*` (new), `frontend/src/components/FindingCard.tsx`, `docs/logs/CURSOR_LOG.md`
- What changed: Regenerated types for [CONTRACT v0 → v1] (nullable `checker_report`). Screen 3 now has fact trust chips with Approve/Challenge, dependent recompute to UNKNOWN, as-of date vs commencement in-force flip, out-of-corpus UNKNOWN demo (no invented citations), and a proof JSON editor that POSTs `/proofs/verify` and shows PREMISE_MISMATCH on tamper.
- Checks run: `make check-frontend` → pass (oxlint 0 issues; vitest 18/18); `npm run build` → pass; `npm run gen:api` → pass
- Decisions / assumptions: Commencement date taken from stub SV-01 `effective_from` 2025-10-01. Tamper mock compares premise statements to the stored finding proof. Live path uses `VITE_USE_LIVE_API=1` for approve/challenge/verify.
- Requests: none
- UI rules checked: disclaimer via layout on `/control` · AI-draft + Lawyer-reviewed badges · status text+icon · UNKNOWN is first-class
- New-work note: Screen 3 lawyer control mock flow 2026-10-30
- Third-party added: none
- Ready for human commit: yes — suggested message: `T5.3: build lawyer control screen with proof tamper demo`

## [T6.2] STARTED · 2026-10-30 22:53 IST
- Task: Challenger in UI + README note
- Built against: contract v1 · openapi/examples mocks

## [T6.2] DONE · 2026-10-30 22:54 IST
- Task: Challenger in UI + README note
- Built against: contract v1 · openapi/examples mocks (no new contract; T6.1 did not bump version)
- Files changed: `frontend/src/components/ChallengerPanel.tsx` (new), `frontend/src/components/ChallengerPanel.test.tsx` (new), `frontend/src/api/mocks/challenger.ts` (new), `frontend/src/api/mocks/challenger.test.ts` (new), `frontend/src/pages/ClauseReviewPage.tsx`, `frontend/src/pages/ClauseReviewPage.test.tsx`, `frontend/src/pages/LawyerControlPage.tsx`, `frontend/src/pages/LawyerControlPage.test.tsx`, `README.md`, `docs/logs/CURSOR_LOG.md`
- What changed: Challenger panel on clause review (toggle + demo run) and lawyer control (after a rejected proof). Blocking objections show Requires review with severity as text, not colour-only. README states muse-spark-1.2 is only the challenger, `CHALLENGER=on|off`, and `CHALLENGER_PROVIDER=meta`.
- Checks run: `make check-frontend` → pass (oxlint 0 issues; vitest 23/23); `npm run build` → pass
- Decisions / assumptions: Contract still v1 so `gen:api` was not re-run. Demo objections follow the T6.1 recorded second-pass shape (blocking + quote + reason). Default panel is on in the UI; backend default remains `CHALLENGER=off`.
- Requests: [REQ → H] consider adding `CHALLENGER=off` and `CHALLENGER_PROVIDER=meta` to `env.example`
- UI rules checked: disclaimer via layout · status text+icon for REQUIRES_REVIEW · no claim that the challenger proves the law
- New-work note: Challenger panel + README model note 2026-10-30
- Third-party added: none
- Ready for human commit: yes — suggested message: `T6.2: add challenger panel and README model note`

## [T5.4] STARTED · 2026-10-30 23:00 IST
- Task: Wire to real API, remove mocks from demo path
- Built against: contract v1 (T4.5; T6.1 did not bump)

## [T5.4] DONE · 2026-10-30 23:03 IST
- Task: Wire to real API, remove mocks from demo path
- Built against: contract v1 (no gen:api; T6.1 did not bump)
- Files changed: `frontend/src/api/client.ts`, `frontend/src/api/config.ts`, `frontend/src/api/types.ts`, `frontend/src/api/client.test.ts` (new), `frontend/src/api/mocks/index.ts`, `frontend/src/pages/ClauseReviewPage.tsx`, `frontend/src/pages/SourceImpactPage.tsx`, `frontend/src/pages/LawyerControlPage.tsx`, `frontend/src/components/lawyer/FactTrustList.tsx`, `frontend/src/components/clause-review/ToolTracePanel.tsx`, `frontend/vite.config.ts`, `README.md`, `docs/logs/CURSOR_LOG.md`
- What changed: Demo/dev now call the live v1 API by default. Bundled `openapi/examples` mocks stay for Vitest (`MODE=test`) or `VITE_USE_MOCKS=1`. Live paths match T4.5: clauses via document `DOC-01`, `GET /api/source-versions/{id}/diff?against=`, `GET /api/graph?matter_id=`, `GET /api/audit?matter_id=`, inline ingest (no `fixture:true`), poll `GET /runs/{id}/events` + run status, 404 current-finding handled. Vite proxies `/api` to port 8000. README demo path is `API_STUB=0` + `LLM_MODE=replay`.
- Checks run: `make check-frontend` → pass (oxlint 0; vitest 24/24); `npm run build` → pass. Browser: `/review`, `/impact`, `/control` render with disclaimer; matter/sources did not load because the process on :8000 is not the v1 app (`/api/health` 404). Did not start or restart the backend (would open the database).
- Decisions / assumptions: Default client is live; tests keep mocks. Impact ids are `IMP-{versionId}`. Ingest posts the selected version's `diff.after` provisions (duplicate content is idempotent on the API). Screen 3 as-of / out-of-corpus panels stay client overlays (no as-of query endpoint). Challenger "Run challenger (demo)" still injects the T6.2 overlay so existing tests hold; live `challenger_report` on a finding is shown when present.
- Contract change: none (v1)
- Requests: [REQ → MC] `POST /api/claims` structures a claim and opens a run but does not start the T2.5 agent loop, so `GET /claims/{id}/current` 404s and the run stays `running`. Screen 1 cannot finish a finding until that loop is invoked from the API. [REQ → MC] no CORS middleware; Vite proxy covers `npm run dev`, a raw `VITE_API_BASE=http://localhost:8000` browser origin will fail. [REQ → H] `seed_demo` does not extract facts, so Screen 3 is empty until `POST /api/documents/DOC-01/extract`. Restart whatever is on :8000 with `API_STUB=0 LLM_MODE=replay DEMO_MODE=1`.
- UI rules checked: disclaimer on `/review`, `/impact`, `/control` · AI-draft / status text+icon unchanged · SIMULATED still from `is_simulated` · no legal-advice copy
- New-work note: Demo UI talks to the live v1 API 2026-10-30
- Third-party added: none
- Credit spend: $0 (no model calls)
- Ready for human commit: yes — suggested message: `T5.4: wire demo UI to the live v1 API`

## [G2,G3,G5,G9] STARTED · 2026-11-02 01:38 IST
- Task: Gate fixes — Screen 1 recorded question/as-of, Screen 3 uses Screen 1 claim_id, challenger toggle copy
- Built against: contract v2 (run npm run gen:api)

## [G2,G3,G5,G9] DONE · 2026-11-02 01:41 IST
- Task: Gate fixes G2, G3, G5, G9 (frontend only, as specified)
- Built against: contract v2 (`npm run gen:api` run)
- Files changed: `frontend/src/api/schema.d.ts` (regen v2), `frontend/src/api/demoSession.ts` (new), `frontend/src/api/mocks/runTrace.ts`, `frontend/src/components/clause-review/AskBox.tsx`, `frontend/src/pages/ClauseReviewPage.tsx`, `frontend/src/pages/ClauseReviewPage.test.tsx`, `frontend/src/pages/LawyerControlPage.tsx`, `frontend/src/pages/LawyerControlPage.test.tsx`, `frontend/src/components/ChallengerPanel.tsx`, `frontend/src/components/ChallengerPanel.test.tsx`, `frontend/src/components/lawyer/FactTrustList.tsx`, `frontend/src/components/lawyer/ProofEditor.tsx`, `frontend/src/components/lawyer/AsOfPanel.tsx`, `frontend/src/components/lawyer/UnknownClaimDemo.tsx`, `docs/logs/CURSOR_LOG.md`
- What changed: Screen 1 default question is the seed/cassette text and as-of defaults to 2026-11-20 with 2025-10-17 as the second option. Screen 1 stores the returned `claim_id` in sessionStorage; Screen 3 uses that id only — no hardcoded `C-001`. With no claim, Screen 3 shows "Run Screen 1 first" and disables approve/challenge/as-of/unknown/proof actions. Challenger checkbox label is the specified display-only copy; it does not imply it starts the backend pass.
- Checks run: `make check-frontend` → pass (oxlint 0; vitest 27/27); `npm run build` → pass. Browser: `/review` shows the recorded question, as-of 2026-11-20 / 2025-10-17, and the new challenger label; `/control` shows "Run Screen 1 first" with actions disabled. Backend was not started (lane rule).
- Decisions / assumptions: Claim id is passed via `sessionStorage` (`clausetrace.claim_id`) so Screen 3 works after a Screen 1 run in the same tab. Mock `C-001` remains only inside `openapi/examples` mock payloads, not page code. As-of on Screen 1 is a two-option select so replay dates cannot be mistyped.
- Contract change: none (consumed v2 types; no API edit)
- Requests: none
- UI rules checked: disclaimer still on every screen · challenger copy does not claim the law is true · no legal-advice text
- New-work note: none
- Third-party added: none
- Credit spend: $0
- Ready for human commit: yes — suggested message: `Fix Screen 1 defaults, Screen 3 claim_id, and challenger toggle copy`

## [proxy-8001] STARTED · 2026-11-02 02:09 IST
- Task: Screen 1 stuck on Loading matter (Vite proxy vs API port)
- Built against: contract v2 · live API

## [proxy-8001] PARTIAL · 2026-11-02 02:10 IST
- Task: Point Vite `/api` proxy at ClauseTrace on 8001
- Built against: contract v2 · live API on 8001
- Files changed: `frontend/vite.config.ts` (modified: proxy target 8000 → 8001), `frontend/src/api/client.ts` (debug logs), `frontend/src/pages/ClauseReviewPage.tsx` (load error notice + debug logs), `docs/logs/CURSOR_LOG.md`
- What changed: `/review` now loads MAT-01, 12 clauses, CL-10. Debug log GET 200 + "matter loaded". Run verification still 502 `MODEL_UNAVAILABLE` hash `72496f2e…` (POST logged status 502).
- Checks run: proxy `GET /api/matters/MAT-01` through 5173 → 200; browser `/review` shows Acme–Nimbus; Ask 502 on screen
- Decisions / assumptions: port 8000 is still another app; 8001 is ClauseTrace. Debug instrumentation left in until the 502 is gone.
- Requests: [REQ → MC] re-record the ask-flow cassettes after G8 seed facts (Muse Code log G4 PARTIAL). [REQ → H] `make reset-demo` then `make record` once (spends credits). Cursor will not call the model.
- UI rules checked: disclaimer still on `/review`
- New-work note: none
- Third-party added: none
- Credit spend: $0
- Ready for human commit: no — debug logs still in client; 502 not fixed

## [ask-502-B] STARTED · 2026-11-02 02:23 IST
- Task: Ask still 502 after G8; apply Muse option B then make replay work for random API claim ids
- Built against: contract v2 · live API on 8001 · LLM_MODE=replay

## [ask-502-B] DONE · 2026-11-02 02:30 IST
- Files changed: `backend/app/agent/prompts.py` (claim id line in proof prompt), `backend/app/agent/loop.py` (`_prompt_claim_id` uses recorded cassette ids, not live C-*), `backend/app/agent/tools.py` (`_bind_run_claim` for verify/propose), `backend/app/agent/llm.py` (debug logs), `corpus/cassettes/` (re-recorded ask chain), `docs/logs/CURSOR_LOG.md`
- What changed: Option B put a claim id in the proof prompt so the model stops inventing CLAIM-9.2. Live `make record` then accepted in 5 calls and stored FOLLOWS. POST Ask still 502 because API mints `C-{uuid}` and that id was hashed into the prompt (missing cassette `c65a07968606`). Fix: prompt embeds the recorded id (`C-REC-ASK` / `C-REC-ASK-1017` / `C-LOOP-92`); tools rebind verify/propose onto the run claim without mutating conversation history. Direct POST both as-of dates → 200 FOLLOWS.
- Checks run: POST `/api/claims` 2026-11-20 → 200 `FOLLOWS` (`C-c50516b91871`); 2025-10-17 → 200 `FOLLOWS`. pytest `test_demo_question_end_to_end`, `test_g4_ask_replays_on_seeded_facts`, `test_user_date_question_end_to_end`, `test_challenger_report_returned`, `test_cross_matter_access_rejected`, `test_replay_clause_92_loop` → 6 passed. Full `make check-backend` not run. Frontend debug logs still in.
- Decisions / assumptions: human proceed treated as override to edit backend (Muse lane) to finish the gate. Did not weaken `request_hash`. Cross-matter claim ids are not rebound. Latest record line `cost_est=$0.000448`.
- Contract change: none
- Requests: [REQ → H] commit mixed lanes (frontend proxy + backend G8/B/C + cassettes). Browser confirm Run verification on `/review` shows FOLLOWS. Do not start T7 until that click is green.
- UI rules checked: no copy change claiming the system proves the law
- New-work note: prompt claim-id is the cassette id; tools bind the live claim (option B+C)
- Third-party added: none
- Credit spend: ~$0.000448 this record (on top of G4 failed record ~$0.013)
- Ready for human commit: no until browser Ask is confirmed and debug logs are removed
- Suggested message: `Fix ask replay: stable cassette claim id plus tool rebind`

## [ask-502-B] CONFIRMED · 2026-11-02 02:33 IST
- What changed: Browser `/review` Run verification (default 2026-11-20 question) returned finding `FND-e25e54bb2f42` status FOLLOWS for live claim `C-dc6c0a3de675`. POST `/api/claims` 200. Replay used prompt id `C-REC-ASK` with cassette `624b9d9783d6` present; tools rebound `C-REC-ASK` → `C-dc6c0a3de675`. The on-screen `72496f2e` cassette error was the previous failed Ask, not a new 502.
- Files changed: removed debug ingest logs from `frontend/src/api/client.ts`, `frontend/src/pages/ClauseReviewPage.tsx`, `backend/app/agent/llm.py`, `loop.py`, `tools.py`. Kept load-failure `setNotice`. Kept `_prompt_claim_id` + `_bind_run_claim`.
- Checks run: browser Ask 200 FOLLOWS; uvicorn POST 200; GET `/api/claims/C-dc6c0a3de675/current` 200.
- Ready for human commit: yes — suggested message: `Fix ask replay: stable cassette claim id plus tool rebind`

## [T9.1] STARTED · 2026-11-02 09:49 IST
- Task: README as sales document (DEMO_AND_SUBMISSION §1) plus Muse Code [REQ → CU] backend facts
- Built against: contract v3

## [T9.1] DONE · 2026-11-02 09:49 IST
- Task: README as sales document
- Built against: contract v3 (`npm run gen:api` run)
- Files changed: `README.md`, `frontend/src/api/schema.d.ts` (v3 regen), `docs/logs/CURSOR_LOG.md`
- What changed: README is now the judge-facing sales page: pitch, why-different, architecture mermaid, Meta model table, six tools, NEW_WORK link, honest limitations, replay runbook (env.example, API_STUB=0, recorded question/dates, 8000 vs local 8001), checks, NOTICE link. Applied Muse Code [REQ → CU] from [readme-backend]: contract v3, muse-spark-1.3-contributor, isolated checker / memory-only status, UNKNOWN and challenger-miss behaviour, Docker note. No demo GIF or video URL (T9.2 not done).
- Checks run: `make check-frontend` → pass (oxlint 0; vitest 27/27). Backend pytest 215/215 cited from Muse Code [gate-fix], not re-run (would open the DB).
- Decisions / assumptions: Tool disclosure names Muse Spark in the verdict path and Muse Code as the backend lane, per DEMO_AND_SUBMISSION §1; no "written by" attribution. Canonical API port remains 8000; README states this machine's 8001 workaround instead of changing Makefile.
- Contract change: none (consumed v3 types only)
- Requests: [REQ → H] add the 3-minute video link when T9.2 is uploaded. Compose file still pending H (Muse Code).
- UI rules checked: disclaimer in README · no claim the system proves the law · SIMULATED labelled · not legal advice
- New-work note: none (README rewrite 2026-11-02)
- Third-party added: none
- Credit spend: $0
- Ready for human commit: yes — suggested message: `Rewrite README as the hackathon sales document`

## [proxy-8000] STARTED · 2026-11-02 10:02 IST
- Task: Point Vite `/api` proxy at backend port 8000
- Built against: contract v3

## [proxy-8000] DONE · 2026-11-02 10:03 IST
- Task: Point Vite `/api` proxy at backend port 8000
- Built against: contract v3
- Files changed: `frontend/vite.config.ts`, `README.md`, `docs/logs/CURSOR_LOG.md`
- What changed: Vite `/api` proxy target is `http://127.0.0.1:8000`. README no longer describes the 8001 workaround.
- Checks run: `make check-frontend` → pass (oxlint 0; vitest 27/27)
- Decisions / assumptions: Canonical ports are backend 8000, frontend 5173.
- Contract change: none
- Requests: none
- New-work note: none
- Third-party added: none
- Credit spend: $0
- Ready for human commit: yes — suggested message: `Point Vite API proxy at port 8000`

## [S1-review] STARTED · 2026-11-02 10:09 IST
- Task: Screen 1 Mark lawyer-reviewed was a local-only toggle; wire it to POST /findings/{id}/review
- Built against: contract v3

## [S1-review] DONE · 2026-11-02 10:11 IST
- Task: Screen 1 Mark lawyer-reviewed posts to the review API
- Built against: contract v3
- Files changed: `frontend/src/api/client.ts`, `frontend/src/api/types.ts`, `frontend/src/api/mocks/index.ts`, `frontend/src/pages/ClauseReviewPage.tsx`, `frontend/src/pages/ClauseReviewPage.test.tsx`, `frontend/src/components/FindingCard.tsx`, `frontend/src/components/FindingCard.test.tsx`, `docs/logs/CURSOR_LOG.md`
- What changed: the Screen 1 button was a local `setState` labelled "(demo)", so live review never hit the API and the badge did not persist. It now `POST /api/findings/{id}/review` with `action=approve`, refetches the finding, and shows Lawyer-reviewed from `REVIEWED` state / "Reviewed by lawyer" label. Button disables after success.
- Checks run: `make check-frontend` → pass (oxlint 0; vitest 28/28). Browser: `/review` loaded; Run verification 502'd (`CHALLENGER=on` cassette miss `7187dcc1…`) so the review click could not be exercised live. Tests cover the click.
- Decisions / assumptions: approve is the lawyer-reviewed action (reject would be REJECTED). Overlay `ai_draft_label` after a successful POST so mocks still flip the badge.
- Contract change: none
- Requests: none
- UI rules checked: AI-draft vs Lawyer-reviewed still text+icon · disclaimer unchanged
- New-work note: none
- Third-party added: none
- Credit spend: $0
- Ready for human commit: yes — suggested message: `Wire Screen 1 lawyer-reviewed to the review API`

## [impact-reingest] STARTED · 2026-11-02 11:14 IST
- Task: Screen 2 ingest of the stored simulated amendment showed no STALE findings
- Built against: contract v3

## [impact-reingest] DONE · 2026-11-02 11:32 IST
- Task: Screen 2 ingest of a stored amendment marks dependent findings STALE
- Built against: contract v3
- Files changed: `backend/app/api.py`, `backend/app/services/seed.py`, `backend/tests/test_api.py`, `backend/tests/test_scenarios.py`, `docs/logs/CURSOR_LOG.md`
- What changed: identical-content ingest still runs impact for that stored version. Seed ensures one current finding per loaded rule card, with ids, clause choice, and the citation taken from the card and the contract text. No source, card, or machine path is special-cased. Debug logs stay until the click-through is confirmed.
- Checks run: `pytest tests/test_api.py::test_reingest_stored_version_stales_card_dependents tests/test_scenarios.py::test_scenario_stale_chain_flags_exactly_dependents tests/test_seed.py` → 6 passed. `ruff check` on the four files → pass. `mypy app/api.py app/services/seed.py` → pass. Live ingest of the stored simulated version → 200, impact affected 1, state STALE. `make check-backend` not run.
- Decisions / assumptions: [REQ → H] backend files edited from the Cursor lane because the human said to proceed on this gate. A finding goes stale only when it depends on a card whose provision key changed. Re-verify on `LLM_MODE=live` with `CHALLENGER=on` would call the model; the regression test uses replay and challenger off and gets REQUIRES_REVIEW.
- Contract change: none
- Requests: [REQ → H] lane note above
- New-work note: none
- Third-party added: none
- Credit spend: $0
- Ready for human commit: yes — suggested message: `Mark dependents stale when a stored amendment is ingested`

## [impact-reingest] VERIFIED · 2026-11-02 11:36 IST
- Ingest on the Source change page returned 200 for the stored simulated version. Impact listed `FND-RC-CT3-BREACH-01` as STALE; the other findings stayed current. Debug logging removed after that run.
- Credit spend: $0

## [docs-gate] DONE · 2026-11-02 12:02 IST
- Task: Bring status docs in line with the green core gate and commit 59025a7
- Built against: contract v4
- Files changed: `PROGRESS.md`, `docs/logs/HUMAN_LOG.md`, `NEW_WORK.md`, `docs/TASKS.md`, `docs/logs/CURSOR_LOG.md`
- What changed: PROGRESS now says the replay gate is green and contract is v4. HUMAN_LOG records 59025a7 and SP4. NEW_WORK lists the impact/UNKNOWN/review work, the scenario tests, and the Dockerfile-only deploy gap. T8.1 is ticked. T7 and T8.2–T9 stay open.
- Checks run: none (docs only)
- Decisions / assumptions: human asked for the docs update. Did not rewrite old agent-log entries.
- Contract change: none
- Requests: none
- New-work note: none
- Third-party added: none
- Credit spend: $0
- Ready for human commit: yes — suggested message: `Record the green core gate and contract v4`

## [T7.4-ui] STARTED · 2026-11-02 13:24 IST
- Task: CONFLICTING status badge + regenerate API types for contract v6
- Built against: contract v6

## [T7.4-ui] DONE · 2026-11-02 13:25 IST
- Task: CONFLICTING status badge + regenerate API types for contract v6
- Built against: contract v6
- Files changed: `frontend/src/api/schema.d.ts`, `frontend/src/api/types.ts`, `frontend/src/components/badges/StatusBadge.tsx`, `docs/logs/CURSOR_LOG.md`
- What changed: regenerated types from openapi v6. FindingStatus now includes CONFLICTING. StatusBadge shows "≠ Conflicting" with light/dark violet border classes. CONFLICTING is a status, not a state, so STALE/SUPERSEDED still win only on those states. No demo finding added; no exhaustive mock list needed updating.
- Checks run: `make check-frontend` → pass (oxlint 0; vitest 28/28). Extra: `npx tsc -b` → pass.
- Decisions / assumptions: memory service sets CONFLICTING; the UI only displays it. Copy is "Conflicting", not legal advice.
- Contract change: none (consumed v6; did not edit openapi)
- Requests: none
- UI rules checked: status is text + icon, not color alone; light and dark classes present; disclaimer unchanged
- New-work note: none
- Third-party added: none
- Credit spend: $0
- Ready for human commit: yes — suggested message: `Show CONFLICTING findings with a text badge; regenerate API types for v6`
