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
