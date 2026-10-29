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
