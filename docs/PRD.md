# ClauseTrace — Product Requirements (PRD)

Version 1.1 · Solo build, Indie Developer track · Meta Global AI Developer Hackathon

## 1. Overview
**Pitch (one sentence):** When a law changes, ClauseTrace finds which legal conclusions depended on it, makes the agent re-check only those, and shows exactly why each conclusion follows — or why it can't be established.

**Lead-with-the-wow text (for submission page):** "When a law changes, lawyers don't always hear which of their reviewed clauses just went stale. ClauseTrace watches the source, traces the dependency graph, and re-verifies only the conclusions that were affected — with a proof an independent checker can validate."

**What it is:** a temporal verification engine for contract clauses, with a thin lawyer workspace around it. It is **not** a legal chatbot and **not** upload-and-ask RAG. Retrieval is used only inside the bounded tool `lookup_source`.

**Core principle:** a proof shows what follows from accepted premises. It does not claim the premises or the law are true, and it is not legal advice.

## 2. Problem statement fit
Primary: **Build for Your World** — bring Meta's models into a professional domain (contract compliance) and make possible something that wasn't (automatic, evidence-backed staleness tracking when a law or commencement date changes). Secondary angle for the video: verifiable agent memory for software agents ("Push the Frontier"). Choose one on the submission form; recommended: Build for Your World.

## 3. Users and impact (rubric: Impact 30%)
- **Users:** solo lawyers, small firms, and in-house privacy/compliance teams reviewing vendor and data-processing agreements in India.
- **Pain:** India's DPDP Rules 2025 phase in over time (some provisions immediately, others after 12 and 18 months — verify exact dates from the notification). A contract reviewed today can become non-compliant on a future commencement date, and nobody gets told which reviews are affected.
- **Impact sentence:** ClauseTrace turns "re-read everything when a law changes" into "re-check these 3 findings, here is why", with an audit trail a firm can defend.
- **Honest scope:** prototype on one corpus and one fictional contract; no real client data.

## 4. Goals and demo-measurable success metrics
| ID | Metric | Target |
|----|--------|--------|
| G1 | Findings with checker status PASS among FOLLOWS/RULED_OUT | 100% |
| G2 | Citations whose quoted span matches the stored snapshot (sha256 + substring) | 100% |
| G3 | On the fixture amendment: findings flagged stale vs findings truly dependent | exact match (e.g. 3 of 8, no false flags) |
| G4 | Change to the unrelated decoy source flags | 0 findings |
| G5 | Graph traversal + stale marking time on fixture | < 2 s |
| G6 | Re-verification of stale findings end to end | < 45 s |
| G7 | Out-of-corpus claim returns UNKNOWN with no invented citation | yes |
| G8 | Tampered proof (edited premise) rejected by checker | yes, shown live |

## 5. Features
Priority: **MVP** = must work in the demo · **Lite** = minimal version · **Stretch** = only if core is green · **Cut** = out.

| ID | Feature | Priority |
|----|---------|----------|
| F1 | Source registry + immutable, hashed source snapshots with versions and effective dates | MVP |
| F2 | Provision parsing + hand-curated rule cards (6–8) citing verbatim spans | MVP |
| F3 | Contract ingest + clause extraction (Muse Spark, structured output) | MVP |
| F4 | Question → typed claim (4 claim types, see §7 of ARCHITECTURE) | MVP |
| F5 | Agent with exactly 6 bounded tools (Responses API function calling) | MVP |
| F6 | Deterministic proof checker (separate package, no model) | MVP |
| F7 | Findings: FOLLOWS / RULED_OUT / UNKNOWN / REQUIRES_REVIEW + confidence band (rule-computed) | MVP |
| F8 | Trust classes on facts; premise admission rules | MVP |
| F9 | Source trace, premise trace, readable syllogism, "what would change my answer" | MVP |
| F10 | Versioned dependency graph (DEPENDS_ON, DERIVED_FROM, SUPERSEDES) | MVP |
| F11 | Amendment ingest, side-by-side diff, impact traversal, stale marking | MVP |
| F12 | Re-query enforcement, re-verification, old finding preserved | MVP |
| F13 | "As-of date" applicability (commencement / effective dates) | MVP |
| F14 | Audit log view | MVP |
| F15 | Lawyer approve / challenge premise → dependent findings recompute | MVP |
| F16 | Disclaimer banner; "AI draft" vs "Lawyer-reviewed" badges | MVP |
| F17 | Second-pass challenger (finds missing premises / counterexamples; an objection forces REQUIRES_REVIEW). Runs on Muse Spark with a different version and prompt | Lite |
| F18 | Matter context panel: one hearing date + one task, static | Lite |
| F19 | Counterfactual mode (read-only graph query: "if provision repealed / clause removed") | Stretch |
| F20 | Voice dictation → proposed fact (Muse Voice Transcribe) | Stretch |
| F21 | Scanned page → text (Muse Spark vision/PDF input) | Stretch |
| F22 | CONFLICTING-authorities state | Stretch |
| F23 | Challenger on Muse Spark Open through a partner host (open-weights bonus). Config switch only; core is Meta-API-only | Stretch (only if you get access and time) |
| — | Full dashboard, calendar, client portal, analytics, multi-jurisdiction, court-judgment network, live scraping/scheduled polling | **Cut** |

"Law-change monitor" in the MVP = an ingest button that loads the next snapshot from an allowlisted official URL or a local fixture. Scheduled polling is listed as future work.

## 6. User flows
1. **Verify a clause:** open matter → pick clause 9.2 → ask "Does this breach-notice window meet the DPDP breach-reporting timeline?" → watch tool-call trace → see finding, confidence, syllogism, source trace, premise trace, "what would change this".
2. **Law changes:** click "Check sources" → new version detected → side-by-side diff → impact graph shows affected findings → agent re-queries → new findings, old ones frozen → audit entry.
3. **Lawyer control:** review AI-extracted fact → Approve (becomes lawyer-confirmed) or Challenge (becomes disputed) → dependent findings recompute → mark finding "Lawyer-reviewed".
4. **Honest unknown:** ask a claim outside the corpus → UNKNOWN, "no source on file covers this", zero citations invented.
5. **As-of date:** move the as-of date before/after a commencement date → a provision flips between "not in force" and "in force" and the finding changes.

## 7. Out of scope (and anti-project guardrails)
- Not RAG chat, not a general legal assistant, not medical/job/education/personality/sports/nutrition tooling.
- No political or war content; no election, party, or government-vs-citizen examples. Domain is commercial data-processing contracts.
- No real client data, no real hearing data, no legal advice, no claim of legal compliance.
- No agent web browsing; no other jurisdictions; no practice-management suite.

## 8. Non-functional requirements
- **Honesty:** disclaimer banner on every screen; UNKNOWN is a first-class result; simulated data always badged.
- **Reproducibility:** each finding stores source versions, premises, tool log, model ids, as-of date.
- **Security:** matter-scoped queries; secrets in `.env`; no PII.
- **Performance:** see G5/G6. Demo must run from `make reset-demo` in under 60 s.
- **Reliability:** replay mode for the demo path; pre-recorded fallback video.
- **Accessibility:** keyboard-navigable, contrast-safe status colors plus text/icon labels (never color alone).

## 9. Meta tooling plan (rubric: Meta AI Tooling 25%)
| Model | Used for | Why it is more than basic integration |
|-------|----------|---------------------------------------|
| Muse Spark (`muse-spark-1.3`) | Clause extraction (structured output); question → typed claim; agent loop with 6 tools; proof drafting | Multi-step tool loop with a hard bounded tool list and enforced re-query |
| Muse Spark, second pass (`muse-spark-1.2`, different prompt) | Challenger: finds missing premises and counterexamples; objection → REQUIRES_REVIEW | A real role in the verdict path; it is a reviewer, not independent verification (the checker is) |
| Muse Spark Open (optional, later) | Same challenger role on open weights via a partner host | Only if access and time allow (F23); enables the open-weights bonus |
| Muse Code | Builds the backend (disclosed in README) | Meta coding agent used in development |
| Muse Voice Transcribe (stretch) | Lawyer dictates a case fact → proposed premise | Multimodal input, human approval gate |
| Muse Spark vision/PDF input (stretch) | Scanned contract pages | Multimodal, India-relevant pain |
Not used: Muse Image (image generation), SAM 3.1, Muse Wonder (preview; optional A/B only).

## 10. Technical depth highlights (rubric: Technical 20%)
1. Independent deterministic proof checker with verbatim-span hash verification and premise admission rules.
2. Append-only versioned graph; targeted invalidation by reverse traversal; finding history preserved.
3. Re-query enforcement: a stale finding is replaced only if the tool log shows a fresh lookup of the current version.

## 11. Demo plan (rubric: Demo 25%)
See `docs/DEMO_AND_SUBMISSION.md` for the 3-minute second-by-second script.

## 12. Compliance table (hackathon rules)
| Rule | How ClauseTrace satisfies it |
|------|------------------------------|
| Uses Meta models | Muse Spark (Meta Model API) in the verdict path; Muse Spark Open optional |
| New work only | Public repo started on Day 1 before any code; `NEW_WORK.md`; commit history |
| Public repo, 3-min video, live product | Tasks T9.x; checklist in DEMO_AND_SUBMISSION |
| Not an anti-project | Not RAG; no medical/political/job/etc.; see §7 |
| Rights to data/assets | Official government texts only, listed in `NOTICE.md`; fictional contract written for this project |
| Contributors listed | Solo (update if teammates join) |
| Claim credits by Nov 4 9 PM ET | Task T0.2 |

## 13. Assumptions, open questions, risks
- **Assumption:** rule cards are written by the developer from official text and treated as "lawyer-confirmed" in the demo role-play. No lawyer has reviewed them. Say so in the README; if possible get a law-literate person to sanity-check the cards.
- **Open:** exact section numbers and commencement dates — verify in T0.6 from official sources before use.
- **Open:** whether to run the amendment demo on a real change or a labelled simulation. Default: simulated fixture, badged.
- **Risk:** scope creep → follow the cut list in `TASKS.md`. **Risk:** credit burn → replay mode. **Risk:** "political/RAG" reading → framing in §1 and §7.
