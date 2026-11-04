# ClauseTrace — full site layout (redesign reference)

One file describing every screen, region, and data need. Nothing here is
a redesign — it maps what exists so a new layout can replace it safely.
Backend contract: v14 (`openapi/openapi.json`). Never render ids, hashes,
JSON, tool names, or mode words in lawyer UI (see `src/utils/lawyerCopy.ts`
banned list). Disclaimer banner + "AI draft — not yet reviewed" on every
screen is mandatory.

## Global shell (all routes)

- Top: `DisclaimerBanner` (legal-limits sentence, always visible).
- Below: `SiteNav` — links: Your matters `/`, Review a clause `/review`,
  Law changes `/impact`, Your control room `/control`, Update clauses
  `/clauses`, Dictate a fact `/dictate`, Sign in `/signin`.
- Content column: `max-w-5xl`, stacked panels (`.ct-panel`), section titles
  (`.ct-section-title`). Light + dark via CSS vars (`--ct-*`).
- Auth: bearer token in localStorage (`storeToken`); `/signin` creates it.
  API base: Vite proxy `/api` → backend. Tests use bundled mocks.

## `/` — Your matters

Regions: header (title + AI-draft badge) → matter card (title, client name,
3 workflow cards linking to /review, /impact, /control) → UploadPanel.
UploadPanel: title input, file input (PDF/DOCX/TXT), upload button,
progress status (`queued` → per-page `stage` → `done`/`failed`), per-page
origin list ("read from the file" / "transcribed from a scan"), link to
/review (clauses). Error case: offline-mode failure shows the live-mode
hint; unreadable files show the unreadable message.

## `/review` — Review a clause

Regions: header (matter title/client) → clause list (12 refs, 9.2
auto-selected) → AskBox (question text, as-of select with 2 recorded dates,
Ask button) → tool-trace panel (live polling list, 5 steps typical) →
notice line → answer stack (FindingCard, lawyer-reviewed toggle, reasoning
steps, source trace, premise trace, what-would-change panel) →
challenger panel.
Data flow: `documents` → `clauses` + `facts` (parallel) → `createClaim` →
poll `runEvents(run_id)` until run not `running` → `currentFinding(claim_id)`.
States: idle → running (trace streams) → done (answer) | error notice.
FindingCard contents: title, status badge (label + icon), AI-draft or
lawyer-reviewed badge, law version label + date, clause quote block,
section quote block, "Open evidence" link.

## `/impact` — Law changes

Regions: header → VersionPicker (source select, version select with
SIMULATED badge, Preview + Apply buttons) → WhatIfPanel (changed-section
wording, affected-answers list with would-remain-valid flags, "nothing is
saved" note) → ReverifyListPanel (queue already waiting) → DiffView
(before/after of the provision named in `changed_keys`, NOT row 0) →
StaleGraph (React Flow, stale-highlighted) → AffectedFindings (stale
queue + single Re-check action) → BeforeAfterSplit (earlier vs later
answer; later empty until re-check) → AuditList.
Data flow: `sources` → `sourceVersions` → `diff` + `graph` + `audit` +
`impact` + `reverifyList` (parallel) → `counterfactual` (on Preview) →
`ingest` (on Apply) → `reverify` (on Re-check) → refresh.
Key rule: before/after selects by `changed_keys[0]`, never index 0
(commencement text lives at index 0 — this was a shipped bug once).

## `/control` — Your control room

Regions: header → (gate: "Ask about a clause first" when no claim in
session) → ScanPagePanel → DictationPanel → FactTrustList ("Facts
awaiting your approval"; proposed items first with "Not relied on";
Approve/Challenge buttons; "Already confirmed" notice on double approve)
→ "Related answers were updated" line + current-answer card (local
illustration sample, labelled) → AsOfPanel (date input, in-force line,
local illustration answer when before commencement, labelled) →
UnknownClaimDemo (question box → real server UNKNOWN answer) →
FactWordingEditor (sentence field → Re-check → valid/tamper result) →
challenger note on tamper.
Data flow: session claim id → `clauses` + `facts` + `currentFinding` →
trust actions (`approveFact`/`challengeFact`/`correct`) update the list
in place; `verifyProof` for wording checks; `reviewFinding` for approve.
"Illustration, not a server answer" marks the as-of and post-challenge
sample cards — everything else is a real server call.

## `/clauses` — Update clause wording

Regions: header + versioning explainer → per-page origin panel (only
when the document has a completed intake job: "Page N — read from the
file / transcribed from a scan", with spot-check guidance) → clause
picker → wording textarea → microphone dictate button (fills the
textarea via `/api/transcribe`) → Save (writes a NEW version, old text
kept; `POST /api/documents/{id}/clauses/{clauseId}/update`).
State: notice line for recording/transcribing/saving; clause list
refreshes to the new version ids after save.

## `/dictate` — Dictate a fact

Regions: explainer (proposed, not relied on, until confirmed) → clause
picker → Start/Stop recording (WebAudio → 24 kHz WAV in-browser) →
transcript preview (editable) → Save as proposed fact (`POST
/api/dictations`) → Confirm button (`approveFact`) → "Confirmed by
you" note. Facts stay `ai_inferred` until confirmed.

## `/evidence/:findingId` — Evidence for this answer

Regions: header → FindingCard ("Answer") → ProofSyllogism (numbered
reasoning) → Facts-relied-on list (statement + trust label + confirmer)
→ Earlier-versions queue. Data: `findingById` → `findingHistory(claim_id)`.

## `/admin` — Internal overview (staff only, NOT a lawyer surface)

Counts by status/trust, model spend, job states. Keep visually separate;
never link it from lawyer navigation.

## `/signin` — Sign in

Name/email/password, login vs create toggle, token stored on success,
plain-English errors. No session UI beyond this (token is silent).

## Component inventory (keep the contracts, reshape freely)

Primitives: `Panel` (section shell), `Button` (primary/ghost/danger),
`QueueList` (named queue + empty state), badges (status/trust/AI-draft/
lawyer-reviewed/SIMULATED). Domain: `FindingCard`, `ProofSyllogism`,
`ClauseList`, `AskBox`, `ToolTracePanel`, traces, `DiffView`,
`StaleGraph`, `AffectedFindings`, `BeforeAfterSplit`, `ReverifyListPanel`,
`WhatIfPanel`, `VersionPicker`, `AuditList`, `FactTrustList`,
`FactWordingEditor`, `AsOfPanel`, `UnknownClaimDemo`, `ScanPagePanel`,
`DictationPanel`, `UploadPanel`, `ChallengerPanel`, `IllustrationLabel`.
Types come from `api/types.ts` (generated) — reshape components, not
shapes. Copy rules: glossary first (`content/glossary.ts`), display
fields (`*_label`, quotes) preferred, `lawyerCopy` filter as backstop.
