# 05 — Frontend (React, production rebuild)

## Stack
React 18 + Vite + TypeScript (strict, no `any`), Tailwind design tokens,
React Router, React Flow (law graph), Vitest + Testing Library, generated
API types from `openapi.json` (no hand-written response types).

## Information architecture (lawyer workflows, not system screens)
- **Matters** — list, create, open. Everything is matter-scoped in the UI.
- **Review a clause** — clause list → ask → verdict-first AnswerCard:
  conclusion in approved glossary wording, reasoning as numbered steps with
  clause + section quotes, facts relied on with trust labels, "what would
  change this answer", second-review notes when present.
- **Law changes** — amendment timeline; before/after of the *amended*
  section (selected by changed_keys); preview (what-if) vs applied change;
  affected answers; one Re-check action; before/after answers.
- **Your control room** — three queues: *Facts awaiting your approval*
  (dictated/scanned/proposed first, clearly "not relied on"), *Answers
  needing review* (incl. conflicting readings), *Re-check queue*.
- **Evidence** — per-finding page: full reasoning, citations viewer (exact
  section text), history of versions, export evidence pack.
- **Admin** (staff): members, budgets, eval status — never shown to lawyers
  as product surface.

## Design system
- Tokens: colour, type scale, spacing, status = icon + text (never colour
  alone), light/dark safe, AA contrast, keyboard navigation, focus visible,
  aria labels on every interactive element.
- Copy: the approved glossary only; a banned-strings list (ids, JSON, hashes,
  tool/model internals) enforced by lint test + screenshot sweep.
- Components (< 150 lines each): AnswerCard, ReasoningSteps, CitationBlock,
  FactRow, TrustLabel, QueueList, SectionDiff, LawTimeline, GraphCanvas,
  ApprovalQueue, DictationControl, ScanControl, WordingEditor (structured —
  no raw JSON anywhere in the UI).

## State and data
- Server state via generated client only; no direct fetch in components.
- Optimistic UI forbidden for trust actions (approve/challenge/re-verify
  always round-trip and re-read).
- Errors surface as lawyer-safe messages; machine codes go to console only.

## Tests
- Every component: render + interaction test (Vitest).
- Page flows against mocks generated from openapi examples; contract tests
  fail if a mock drifts from an example payload.
- E2E (staging): the golden demo path in a real browser before each release.
