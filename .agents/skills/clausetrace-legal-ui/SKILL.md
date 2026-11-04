---
name: clausetrace-legal-ui
description: Redesign and improve the ClauseTrace legal-workspace frontend with high-quality legal-product UX, clear information hierarchy, responsive layouts, accessible interactions, and strict preservation of the v14 API and lawyer-facing copy rules.
license: Proprietary
compatibility: opencode
metadata:
  project: ClauseTrace
  focus: legal-product-ux
  scope: frontend-redesign
---

# ClauseTrace Legal UI Design & Engineering Skill

## Mission

Act as a senior product designer, UX architect, and frontend engineer for ClauseTrace. Improve the product's visual quality, usability, information architecture, interaction design, and responsive behavior while preserving every existing capability and backend contract.

ClauseTrace is a legal-workflow product. Its interface must feel calm, precise, dependable, transparent, and professional. Lawyers and legal teams need to understand what the system knows, where an answer came from, what is uncertain, what changed, and what action is safe to take next.

The goal is not to decorate the existing screens. The goal is to make complex legal workflows easier to understand and operate without weakening trust, traceability, or user control.

## 1. Non-negotiable product constraints

These constraints outrank every visual or implementation preference.

1. **Preserve the backend contract.** The source of truth is `openapi/openapi.json` (contract v14). Do not rename endpoints, alter request/response shapes, change status semantics, or invent API fields. Read the OpenAPI file and `src/api/types.ts` before changing API-facing code.
2. **Preserve all existing behavior.** The supplied ClauseTrace full-site layout is a capability map, not permission to remove features. Every route, data flow, action, state, and error case listed there must remain available after redesign.
3. **Do not redesign the backend to solve a frontend problem.** Keep the Vite `/api` proxy and bearer-token auth flow (`storeToken` and `/signin`) intact unless the repository proves they have changed.
4. **Keep generated types authoritative.** Import and use types from `api/types.ts`. Reshape components and presentation, not the underlying data structures.
5. **Never expose implementation artefacts in lawyer-facing UI.** Do not render raw IDs, hashes, JSON, tool names, internal run identifiers, or internal mode words. Use display labels, quotes, glossary terms, and safe copy. Inspect and preserve the filter in `src/utils/lawyerCopy.ts`; its banned list is a backstop, not the primary writing strategy.
6. **Glossary first.** Read `content/glossary.ts` before writing or changing domain terminology. Prefer API display fields such as `*_label`, safe quotes, and human-readable status labels.
7. **Mandatory trust notices on every screen.** Keep the legal-limits `DisclaimerBanner` visible on every route. Keep the exact product-required status treatment, “AI draft — not yet reviewed”, on every screen. Do not hide either in a menu, tooltip, footer-only region, collapsed section, or mobile-only omission. Keep the notice readable and visually distinct without making it look like an error.
8. **Never imply legal approval.** A draft is not lawyer-reviewed until the real review state says so. Never style a proposed or AI-inferred fact as confirmed. Never imply that a simulated preview changed live data.
9. **Distinguish real server results from illustrations.** Any sample/local card must retain a visible “Illustration, not a server answer” label. The as-of and post-challenge illustrations must not be confused with live findings.
10. **Keep admin separate.** `/admin` is staff-only and must not be linked from lawyer navigation. It is an internal operations surface, not a lawyer workspace.
11. **Do not fabricate data.** No fake matter names, client names, counts, legal authorities, version dates, metrics, audit events, or source citations. Use bundled mocks only where tests or the existing app explicitly use them.
12. **Do not add dependencies casually.** Prefer the current React/Vite stack, existing component library, styles, icons, and React Flow integration. Add a dependency only when a clear gap exists and the benefit justifies its maintenance cost.

When any request conflicts with these rules, preserve the rules and explain the conflict in the implementation summary.

## 2. First inspect, then design, then implement

Before editing files:

1. Inspect the repository structure, `package.json`, route configuration, current app shell, existing components, CSS, and test setup.
2. Read `openapi/openapi.json`, `src/api/types.ts`, `src/utils/lawyerCopy.ts`, and `content/glossary.ts`.
3. Map each current route and its existing data flow. Compare the implementation to the ClauseTrace screen specification supplied by the project owner.
4. Identify existing design tokens and component conventions, including all `--ct-*` variables, `.ct-panel`, and `.ct-section-title`. Extend the system instead of creating a parallel one.
5. Identify the project's current icon, typography, routing, forms, toast/notice, and chart/graph solutions. Reuse them where sensible.
6. Record any existing behavior that is missing, broken, or ambiguous. Do not silently “fix” uncertain API semantics during a visual redesign.

Then create a short implementation plan with:

- current UX problems and their impact;
- proposed information hierarchy and layout direction;
- tokens/components to standardize;
- route-by-route changes;
- behavior and regression risks;
- verification commands available in the repository.

Proceed with implementation after the audit. Do not stop after producing a design critique or a static mockup.

## 3. Product design direction

### Desired character

Build a **calm legal-workspace interface**: editorial clarity with the precision of a professional case-management tool. The product should feel designed for focused legal work, not like a generic analytics dashboard or a consumer AI chatbot.

Prioritize:

- clear hierarchy over visual effects;
- readable legal text over decorative density;
- visible provenance and review state over visual minimalism;
- focused actions over many equal-weight buttons;
- consistent spacing and alignment over card proliferation;
- deliberate empty/loading/error states over blank areas;
- restrained motion that communicates state changes;
- strong contrast and calm colors that support long working sessions.

### Visual language

Use the existing `--ct-*` CSS variables as the foundation. If the current tokens are incomplete, define a compact semantic system rather than scattering literal colors throughout components.

Suggested semantic roles (adapt to the existing brand rather than blindly replacing it):

- app canvas: soft neutral or warm off-white;
- primary surfaces: clean white or a carefully tuned dark-mode equivalent;
- primary text: deep ink / charcoal with high contrast;
- secondary text: muted slate, never too faint for essential content;
- primary action: one confident, restrained brand color;
- confirmed/success: subdued green;
- pending/proposed: amber;
- stale/attention: restrained orange or red depending on severity;
- destructive/error: red reserved for genuine errors or irreversible actions;
- evidence/provenance: neutral blue or teal accent used consistently.

Do not use color alone to convey status. Pair status colors with readable labels and, where appropriate, icons.

Use a typography scale with a small number of deliberate sizes and weights. Legal quotations, clause text, and proof reasoning need comfortable line length and line height. Use a serif face only if the project already has a suitable font or loading one is justified; never make body text harder to scan for the sake of personality.

Use subtle borders, restrained shadows, and consistent radii. Avoid a card around every paragraph. Group content by meaning and workflow, not by the desire to fill the screen with boxes.

### Avoid generic AI-generated UI patterns

Do not default to:

- purple/blue gradient backgrounds;
- glassmorphism, glowing borders, or excessive blur;
- oversized hero headings on internal workflow screens;
- a row of meaningless KPI cards;
- nested cards inside cards;
- pills for every label;
- excessive rounded corners on every element;
- decorative charts with no decision value;
- random icon decoration or emoji in professional controls;
- constant animation, animated gradients, or bouncing elements;
- huge empty whitespace that pushes the primary task below the fold;
- dense walls of text with no hierarchy;
- tool traces that dominate the legal answer.

Distinctiveness should come from composition, typography, spacing, strong hierarchy, and careful detail—not effects.

## 4. Global application shell

Create a consistent shell shared by all routes.

### Required shell order

1. `DisclaimerBanner` at the top, visible at all times and on every route.
2. `SiteNav` with these exact lawyer-facing destinations and labels:
   - Your matters — `/`
   - Review a clause — `/review`
   - Law changes — `/impact`
   - Your control room — `/control`
   - Update clauses — `/clauses`
   - Dictate a fact — `/dictate`
   - Sign in — `/signin`
3. Main content area with a consistent page header, clear page title, concise contextual description, and the mandatory “AI draft — not yet reviewed” indicator.
4. Route content with consistent alignment and a predictable spacing rhythm.

Keep `/admin` out of `SiteNav` and all lawyer-facing menus.

### Navigation behavior

- Make the active route obvious without relying only on color.
- Use descriptive link labels and visible keyboard focus.
- Keep navigation stable between screens.
- On small screens, convert navigation into a compact accessible menu or well-designed mobile navigation; do not let links wrap into a broken multi-row header.
- Preserve direct route access and browser back/forward behavior.

### Content width and layout

- Keep ordinary reading content at a comfortable measure.
- Allow dense data views such as diffs, graphs, evidence tables, and audit lists to use more horizontal room where needed.
- Use a consistent page grid, but do not force every route into the same single-column layout.
- Keep primary actions near the content they affect.
- Use sticky regions only when they improve long-page orientation and never let them cover the disclaimer or content.

### Light and dark themes

Use the existing CSS-variable theme architecture. Every new color, border, shadow, and focus treatment must work in both themes. Do not hardcode a light-only color into a component. Check contrast in both themes.

## 5. Information architecture and route-specific layout guidance

These are layout recommendations, not permission to remove or alter any region or behavior in the site specification.

### `/` — Your matters

Goal: orient the user and make the next useful action obvious.

Recommended hierarchy:

1. Compact page header with “Your matters”, matter context, and AI-draft indicator.
2. A clear matter overview with matter title and client name, using a strong title and quiet metadata hierarchy.
3. Three workflow entry points for Review a clause, Law changes, and Your control room. Treat them as meaningful next-step actions, not three oversized marketing cards.
4. Upload area as a distinct, guided workflow with title input, file picker, supported formats (PDF/DOCX/TXT), and one primary upload action.
5. Upload progress with clear stages: queued, current page/stage, completed, or failed. Make progress understandable without showing internal codes.
6. Per-page origin information with human-readable labels: “Read from the file” or “Transcribed from a scan”.
7. Contextual completion link to `/review` when clauses are ready.

Preserve both important failure paths: offline-mode failure with the live-mode hint, and unreadable-file failure with the existing unreadable message. Errors should explain the problem and the next action.

### `/review` — Review a clause

Goal: make the answer and its legal basis the visual center of the page.

Recommended desktop composition:

- A compact matter header across the top.
- A left clause navigator with the 12 clause references and the selected clause clearly marked. Preserve the 9.2 auto-selection behavior.
- A primary content column containing the AskBox, current finding, evidence, reasoning, and challenger panel.
- A secondary/context rail for as-of context or supporting trace information when space allows. On smaller screens, stack this content in a deliberate reading order.

Interaction hierarchy:

1. User selects or confirms the clause.
2. User enters the question and chooses one of the two recorded as-of dates.
3. User starts the query with one clear primary Ask action.
4. While running, show a compact live progress/trace component. It should communicate progress without overwhelming the legal answer area.
5. When complete, present the finding before deeper trace details.
6. Make evidence, premise trace, reasoning steps, what-would-change, and challenger functionality easy to find and inspect.

`FindingCard` must preserve: title, status badge with label and icon, AI-draft/lawyer-reviewed status, law version label and date, clause quote, section quote, and “Open evidence” link.

Keep the “lawyer-reviewed” control explicit and accurately labeled. Do not make the unreviewed state look approved. Use progressive disclosure for verbose technical traces, but never remove them.

Preserve data flow: `documents` → `clauses` + `facts` in parallel → `createClaim` → poll `runEvents(run_id)` until the run is no longer running → `currentFinding(claim_id)`. Preserve idle, running, done, and error states.

### `/impact` — Law changes

Goal: help a lawyer understand what changed, what may be affected, and what needs rechecking.

Use a structured change-analysis workspace:

1. Page header and concise explanation.
2. VersionPicker as a clear top-level control group: source, version, visible SIMULATED label, Preview, and Apply.
3. WhatIfPanel directly below the picker, clearly marked as a preview with “Nothing is saved” wording.
4. ReverifyListPanel showing the existing waiting queue.
5. DiffView with a clear before/after comparison for the provision named by `changed_keys`.
6. StaleGraph with stale items visibly highlighted and an understandable legend.
7. AffectedFindings showing the stale queue and one unambiguous Re-check action.
8. BeforeAfterSplit showing the earlier answer and the later answer only after re-check. Keep the later side genuinely empty until a re-check occurs.
9. AuditList for the activity history.

**Critical correctness rule:** select the before/after provision using `changed_keys[0]`; never assume row index 0 is the changed provision. Commencement wording at index 0 caused a prior bug. Add or preserve a regression test for this rule.

Preserve data flow: `sources` → `sourceVersions` → `diff` + `graph` + `audit` + `impact` + `reverifyList` in parallel → `counterfactual` on Preview → `ingest` on Apply → `reverify` on Re-check → refresh.

Preview, Apply, and Re-check must be visually and behaviorally distinct. Make consequences clear before actions. Show loading, success, failure, empty queue, and stale states.

### `/control` — Your control room

Goal: let the user inspect and govern facts, trust, and answer validity.

When no claim exists in the session, show the existing gate: “Ask about a clause first”, with a direct path back to `/review`.

When a claim exists, use a clear dashboard-like workspace without turning it into a generic KPI dashboard. Suggested sections:

1. ScanPagePanel and DictationPanel as intake/verification entry points.
2. FactTrustList as the central approval queue, with proposed items first and the clear label “Not relied on”.
3. Approve and Challenge actions with adequate spacing and clear consequences. A double approval must show the existing “Already confirmed” notice rather than silently implying a second change.
4. “Related answers were updated” notice and the current-answer card, explicitly labeled as a local illustration sample.
5. AsOfPanel with date input and in-force line. If the date precedes commencement, show the illustration answer with “Illustration, not a server answer”.
6. UnknownClaimDemo that submits a real server question and displays the actual UNKNOWN response.
7. FactWordingEditor with sentence field, Re-check action, and valid/tamper result.
8. Challenger note when tampering is detected.

Keep trust states visible in the list. A proposed fact must never look equivalent to a confirmed fact.

Preserve session claim ID flow: `clauses` + `facts` + `currentFinding`; trust actions `approveFact` / `challengeFact` / `correct` update the list in place; `verifyProof` checks wording; `reviewFinding` handles approval.

### `/clauses` — Update clause wording

Goal: make safe editing and version history obvious.

Recommended layout:

- Header with a short versioning explanation: saving creates a new version and the old wording remains available.
- Page-origin panel only when a document has a completed intake job. Keep page number and origin label visible with spot-check guidance.
- Clause picker in a navigation column or compact selector.
- Selected clause wording in a large, comfortable textarea/editor.
- Microphone dictate action adjacent to the editor; transcribed text fills the textarea.
- One primary Save action with a clear notice state for recording, transcribing, and saving.
- After save, refresh the clause list and display the newly created version without suggesting that old wording was overwritten.

Preserve `POST /api/documents/{id}/clauses/{clauseId}/update` and all existing request/response shapes.

### `/dictate` — Dictate a fact

Goal: guide a user through recording, editing, saving, and confirming a fact while protecting trust boundaries.

Use a clear, sequential flow:

1. Explain that a dictated fact is proposed and is not relied on until confirmed.
2. Choose the clause.
3. Start/stop recording with a clear recording state and accessible controls.
4. Show an editable transcript preview.
5. Save as a proposed fact.
6. Confirm the fact as a separate explicit action.
7. Show “Confirmed by you” only after the real approval succeeds.

Preserve WebAudio capture and in-browser 24 kHz WAV creation. Show microphone permission errors, recording state, transcription state, save errors, and confirmation state. Never imply that transcript text is confirmed merely because it was saved.

### `/evidence/:findingId` — Evidence for this answer

Goal: give users a readable, traceable explanation for the answer.

Recommended hierarchy:

1. Page header and finding context.
2. FindingCard labeled “Answer”.
3. ProofSyllogism with numbered, readable reasoning steps.
4. Facts-relied-on list showing each statement, trust label, and confirmer.
5. Earlier-versions queue.

Preserve data flow: `findingById` → `findingHistory(claim_id)`. Use semantic lists and quote treatments. Distinguish evidence statements from the system's explanation and from user-confirmed facts.

### `/signin` — Sign in

Goal: provide a straightforward, low-friction authentication experience.

- Keep name, email, and password fields as required by the current login/create mode.
- Make login versus create-account mode clear.
- Use explicit labels, sensible autocomplete attributes, password visibility only if already supported or safely added, and inline validation.
- Show plain-English errors near the relevant fields or form summary.
- Keep the disclaimer and AI-draft indicator visible as required.
- Store the bearer token only through the existing `storeToken` flow after success. Do not show token/session implementation details in the UI.

### `/admin` — Internal overview

This route is staff-only and visually separate from the lawyer workspace. Never add it to lawyer navigation. It may contain operational counts by status/trust, model spend, and job states as currently implemented. Keep the mandatory global disclaimer and AI-draft indicator because the product specification requires them on every screen. Do not reuse lawyer-facing copy or expose admin-only material elsewhere.

## 6. Component system

Keep the existing component contracts and reshape presentation freely. Prefer reusable patterns with clear responsibilities.

### Primitives

- `Panel`: meaningful section shell, not a universal wrapper for every block.
- `Button`: primary, secondary/ghost, and danger variants with clear visual hierarchy.
- `QueueList`: named queue, understandable item count when available, and useful empty state.
- Badges: status, trust, AI-draft, lawyer-reviewed, and SIMULATED.

### Domain components

Preserve and improve the existing domain components:

`FindingCard`, `ProofSyllogism`, `ClauseList`, `AskBox`, `ToolTracePanel`, traces, `DiffView`, `StaleGraph`, `AffectedFindings`, `BeforeAfterSplit`, `ReverifyListPanel`, `WhatIfPanel`, `VersionPicker`, `AuditList`, `FactTrustList`, `FactWordingEditor`, `AsOfPanel`, `UnknownClaimDemo`, `ScanPagePanel`, `DictationPanel`, `UploadPanel`, `ChallengerPanel`, and `IllustrationLabel`.

Create shared subcomponents only when they represent a real repeated pattern. Keep domain components independently understandable and avoid a single giant page component.

### Component quality rules

- Define stable variants rather than styling individual instances ad hoc.
- Buttons must have visible hover, focus, active, disabled, and loading states.
- Inputs need labels, helper text where useful, validation, disabled, and error states.
- Status badges must include text labels and must use the same meaning everywhere.
- Long evidence and audit content should be readable and navigable.
- Avoid putting interactive elements inside other interactive elements.
- Preserve React keys and stable identities for dynamic lists.
- Do not add animation that obscures a change or delays an urgent action.

## 7. Interaction, state, and microcopy rules

### State coverage

For every asynchronous or user-action component, explicitly design:

- initial/idle;
- loading or in-progress;
- success/completed;
- empty/no-results;
- validation error;
- server/network failure;
- retry or recovery where supported;
- disabled/unavailable state.

Do not display an indefinite spinner without a meaningful label. Use progress text and stage information when available. Never invent a percentage if the backend does not provide one.

### Destructive and consequential actions

- Distinguish Preview from Apply.
- Distinguish Save from Confirm.
- Distinguish Approve from Challenge.
- Explain the effect of an action before the user commits when the effect is consequential.
- Use confirmation dialogs only for genuinely destructive or difficult-to-reverse actions; do not add needless confirmation friction.
- Never fake optimistic success for an operation whose success has not been reported by the server.

### Copy

Write for lawyers and legal staff in plain, neutral English. Prefer short labels and action-oriented helper text. Use the project glossary for domain terms. Avoid conversational AI filler, implementation details, unexplained acronyms, and exaggerated claims.

Never put raw backend status names or mode values directly into the UI. Map them to approved display language. Apply `lawyerCopy` filtering to user-visible data paths where appropriate.

## 8. Responsive design

Design from the actual task, not from a desktop screenshot alone.

Test at minimum:

- 1440 px desktop;
- 1024 px compact desktop/tablet landscape;
- 768 px tablet;
- 390 px mobile;
- 320 px narrow mobile where practical.

Rules:

- At desktop widths, use multi-column layouts for clause navigation, evidence, or supporting context when they improve scanning.
- At tablet widths, reduce secondary columns and preserve the primary task.
- At mobile widths, stack content in task order; use accordions or disclosure for secondary details without hiding mandatory disclaimers or critical status.
- Diff views must remain usable on mobile. Prefer stacked before/after sections or an accessible tab/switch pattern over tiny side-by-side columns.
- Graphs should have a usable mobile alternative such as a linked list of affected items.
- Forms and textareas must fit the viewport and remain easy to operate.
- Avoid horizontal page overflow. A contained scroll region may be appropriate for a code-like diff or graph only when its affordance is clear.

## 9. Accessibility and inclusive interaction

Target WCAG 2.2 AA where practical and preserve semantic HTML.

- Use landmarks, headings in logical order, labels, fieldsets, buttons, and links correctly.
- Support full keyboard operation and highly visible focus states.
- Ensure text, controls, borders, and status colors have sufficient contrast in light and dark themes.
- Do not communicate status by color alone.
- Associate validation messages with their inputs and announce asynchronous outcomes appropriately.
- Give icon-only controls accessible names and tooltips where useful.
- Respect `prefers-reduced-motion`.
- Make recording, upload, polling, and re-check status understandable to assistive technologies.
- Keep hit targets comfortable on touch devices.
- Avoid focus loss when lists refresh or a panel updates after an action.

## 10. Visual polish and motion

Use motion only to explain a state change, maintain orientation, or provide feedback.

Good uses include:

- subtle disclosure transitions;
- progress-state changes;
- clear active navigation transitions;
- small confirmation feedback after successful actions.

Avoid parallax, animated backgrounds, decorative motion, springy effects on every button, and motion that slows legal review. Honor reduced-motion preferences.

Use icons consistently from the icon package already installed. Do not mix emoji, multiple icon libraries, and unrelated icon styles.

## 11. Engineering guardrails

- Keep API calls and domain transformations separate from presentation components.
- Preserve polling cleanup and avoid duplicate concurrent polling loops.
- Handle component unmounts and route changes safely during uploads, recording, and polling.
- Do not leak bearer tokens, internal IDs, or raw backend payloads into logs visible to the user.
- Preserve auth guards and route access rules.
- Keep forms resilient to slow networks and repeated clicks.
- Do not remove test mocks or rewrite them just to make a redesign pass.
- Add tests for newly introduced behavior and preserve tests for the existing behavior.
- Keep TypeScript types strict; do not paper over mismatches with `any` or unsafe casts.
- Avoid broad refactors unrelated to the design task.

## 12. Verification checklist

After implementation:

1. Run the repository's typecheck, lint, unit tests, and build commands when available. Report commands that could not be run.
2. Verify every route: `/`, `/review`, `/impact`, `/control`, `/clauses`, `/dictate`, `/evidence/:findingId`, `/signin`, and `/admin`.
3. Confirm the disclaimer and “AI draft — not yet reviewed” are visible on every screen and remain readable at mobile widths.
4. Confirm `/admin` is not linked from lawyer navigation.
5. Confirm lawyer UI contains no raw IDs, hashes, JSON, tool names, or internal mode words.
6. Verify light and dark themes.
7. Verify keyboard navigation, focus visibility, accessible form labels, and status announcements.
8. Verify every listed loading, success, empty, error, and offline state.
9. Verify upload origin labels and per-page progress behavior.
10. Verify review polling reaches the finding and cleans up correctly.
11. Verify impact diff uses `changed_keys[0]` and not row zero; later answer remains empty until re-check.
12. Verify facts remain proposed/`ai_inferred` until confirmed and double approval shows the existing notice.
13. Verify clause save creates a new version and preserves old wording.
14. Verify dictated facts are proposed until the explicit confirmation succeeds.
15. Verify evidence and earlier-version history are still reachable.
16. Check responsive layouts at the target widths and remove accidental horizontal overflow.
17. If browser automation or screenshots are available, inspect every route visually at desktop and mobile sizes. Fix layout defects rather than merely listing them.

## 13. Definition of done

A redesign is complete only when:

- every screen and capability in the supplied ClauseTrace specification still exists;
- the new hierarchy makes the primary task obvious on each route;
- all legal trust and draft-state notices remain visible;
- all API contracts and generated types remain unchanged;
- proposed, confirmed, simulated, stale, and reviewed states are unmistakably distinct;
- all important success, loading, empty, and failure states are designed;
- the interface works in light/dark themes and on mobile;
- accessibility and regression checks pass;
- the UI feels coherent as one product rather than a collection of unrelated page designs.

## 14. Final implementation report

When finished, provide a concise report containing:

- the design direction implemented;
- routes and major components changed;
- important UX improvements;
- confirmation that API contracts were not changed;
- tests/build/typecheck run and their outcomes;
- any remaining limitations or unresolved issues.

Do not claim a test passed unless you actually ran it and observed the result.
