# NEW_WORK.md — What was built during the hackathon

Judges: this file shows what is new. Fill the "Dates" and "Commit range" columns from `git log` and `docs/logs/HUMAN_LOG.md`.

## Before the hackathon
- An idea description (text only) submitted with the application.
- No application code existed. The repository was created on Day 1 of the build; the first commit contains only documentation and the licence.

## Components built during the hackathon
| Component | Dates | Commit range | Built with |
|-----------|-------|--------------|------------|
| Repo, CI, scaffold | 2026-10-29 | `91fc1f`–`391a51a` | Muse Code / Cursor |
| Schema + append-only triggers | 2026-10-29 | `d1efba8` | Muse Code |
| Source snapshots, provisions, rule cards | 2026-10-29 | `72e78e8`–`7ab269a` | Muse Code |
| Fictional contract + seed data (written for this project) | 2026-10-29 | `010a2c9` | Muse Code (fictional DPA; not Spark) |
| LLM gateway (live/replay/mock) | 2026-10-29 | `99a4f74` | Muse Code |
| Clause extraction | 2026-10-30 | `5c45b05` | Muse Code |
| Claim structuring, checker, six tools, agent loop, memory | 2026-10-30 | `9c65591` | Muse Code |
| Dependency graph, impact, re-verify, premise challenge, API v1 | 2026-10-30 | `9c65591` | Muse Code |
| UI screens 1–3 | 2026-10-29 to 2026-10-30 | `7ab269a`–`9c65591` | Cursor |
| Challenger (Muse Spark second pass + panel) | 2026-10-30 | `9c65591` | Muse Code / Cursor |
| Live API wire for the demo path | 2026-10-30 | `9c65591` | Cursor |
| Seed extraction + ask-flow replay after 13 premises | 2026-11-02 | 82fc307 | Muse Code / Cursor |
| Stored-version impact, UNKNOWN without the loop, lawyer-review API, contract v4 | 2026-11-02 | 59025a7 | Muse Code / Cursor |
| Scenario tests (decoy, future provision, stale chain, matter isolation, source failure; UNKNOWN, tamper, and challenger in the API tests) | 2026-11-02 | 59025a7 | Muse Code |
| Backend image | 2026-11-02 | 59025a7 | Dockerfile only; Compose and an off-machine check are not done |
| Gate fixes: clause-ref resolution, UNKNOWN decides directly, challenger-miss → REQUIRES_REVIEW, proof round-trip, root/health routes | 2026-11-02 | uncommitted at writing (owner to commit) | Muse Code |
| T7.3 counterfactual (propositional-logic entailment) + reverify list | 2026-11-02 | uncommitted at writing | Muse Code |
| T7.4 CONFLICTING status (propositional rule-card conflict) + demo conflicting card | 2026-11-02 | uncommitted at writing | Muse Code |
| T7.2 scanned page → text (Muse Spark image input) | 2026-11-02 | uncommitted at writing | Muse Code |
| T7.1 voice dictation → proposed fact (Muse Voice Transcribe) with approval gate | 2026-11-02 | uncommitted at writing | Muse Code |
| Lawyer display labels (contract v9) | 2026-11-02 | uncommitted at writing | Muse Code |
| F1–F3 finish items: every-stale-row re-check + skipped reporting, amended-section diff display, "Already confirmed", real server UNKNOWN | 2026-11-02 | uncommitted at writing | Muse Code |
| Production rewrite P0–P5: modular service boundaries, tenant schema, Postgres migration + FalkorDB graph projection (parity-tested), service split with domain events, async intake jobs + PDF pipeline + fact correction, matters/evidence/admin pages, eval gate, per-tenant budgets | 2026-11-02 | uncommitted at writing | Muse Code |
## Third-party material (not new work)
Open-source libraries and official legal texts are listed with licences and URLs in `NOTICE.md`.
