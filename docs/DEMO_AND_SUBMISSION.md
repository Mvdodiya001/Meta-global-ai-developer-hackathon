# ClauseTrace — Demo, README and Submission Pack

## 1. README structure (a sales document; judges skim)
1. **One-line pitch:** "When a law changes, ClauseTrace finds which legal conclusions depended on it, re-checks only those, and shows exactly why each follows — or why it can't be established."
2. **Demo GIF** (5 s loop: amendment → stale findings light up → re-verified) + link to the 3-minute video.
3. **Why it's different** (3 bullets): dependency graph tells you *what* to re-check; an independent deterministic checker validates proofs; history is never overwritten.
4. **Architecture diagram** (Mermaid from `ARCHITECTURE.md` §2).
5. **How Meta models are used** (table from `PRD.md` §9) + "Built with Muse Code" note.
6. **The six bounded tools** (list from `DATA_MODEL_API.md` §4) and what the model can never do.
7. **What we built during the hackathon** (link to `NEW_WORK.md`).
8. **Honest limitations:** one fictional contract; rule cards written by the developer, not reviewed by a lawyer; simulated amendment is labelled; not legal advice; no compliance claims.
9. **Run instructions:** `make setup && make reset-demo && make dev`; replay mode needs no key.
10. **Test results** (pytest summary) and **source provenance** (link to `NOTICE.md`).
Avoid unverifiable claims about competitors; describe the capability you built.

## 2. Three-minute demo script (target 2:55)
Keep a visible "Built during the hackathon" tag and the SIMULATED badge on screen where relevant.

| Time | On screen | Narration (short) |
|------|-----------|-------------------|
| 0:00–0:10 | Screen 2 showing 3 stale findings, then cut to the title | "When a law changes, lawyers don't always hear which reviewed clauses just went stale. ClauseTrace does." |
| 0:10–0:40 | Screen 1: clause 9.2, ask the question; live tool-call trace (`lookup_source`, `get_premise`, `verify_derivation`, `propose_finding`) → finding card | "Muse Spark can only call six bounded tools. It drafts a proof; it can't set the answer." |
| 0:40–1:05 | Finding: FOLLOWS, confidence band, syllogism, source trace (exact span, version, hash), premise trace, "What would change my answer?" | "Every step cites a source version and a premise. Here's what would flip it." |
| 1:05–1:25 | Checker panel: PASS. Edit a premise in the proof editor → checker REJECTS with a specific code. Show the challenger panel | "The checker has no model in it. A second Muse Spark pass challenges the proof." |
| 1:25–2:05 | Screen 2: ingest the simulated amendment → side-by-side diff → graph: 3 of 8 findings turn stale, decoy source change flags none → Re-verify | "Only dependent findings go stale. The agent must re-query the new version." |
| 2:05–2:25 | Split screen: same question before ("Follows") and after ("Unknown/Requires review"); audit entry with versions and times; old finding still available | "The old answer stays as history. The new one cites the new version." |
| 2:25–2:42 | Screen 3: challenge a premise → dependents recompute; approve → "Lawyer-reviewed" badge; move the as-of date across a commencement date | "Lawyers stay in control; dates matter." |
| 2:42–2:52 | Ask an out-of-corpus claim → UNKNOWN, "no source on file covers this" | "When it can't prove it, it says so." |
| 2:52–3:00 | `git log` with dates, Meta model table, repo URL, disclaimer line | "Built during the hackathon with Muse Spark and Muse Code. A proof is conditional on accepted premises, not a claim the law is true." |

Zero-risk requirements: demo runs in replay mode from `make reset-demo`; every step above has been rehearsed twice; ingest uses the local fixture, not the network.

## 3. "What I built during the hackathon" evidence
- Public repo created on Day 1 before any code; first commit contains only docs and licence.
- `NEW_WORK.md` lists every component with the date and commit range.
- Git history shows daily commits; show it in the last 8 seconds of the video.
- Pre-existing items (state them): the idea text, and open-source libraries listed in `NOTICE.md`. No pre-written application code.

## 4. Submission checklist (aim to submit a day before the deadline; hard deadline: Nov 4, 9 PM ET, about 7:30 AM IST the next morning)
- [ ] Repo is public (open it logged out); README complete; licence present.
- [ ] 3-minute video uploaded; link works logged out; video is ≤ 3:00.
- [ ] Live product URL works from another network; `DEMO_MODE` reset tested.
- [ ] Contributors listed on the submission page (solo, or everyone who worked on it).
- [ ] Track: Indie Developer. Problem statement chosen (recommended: Build for Your World).
- [ ] Meta credits claimed before the deadline; spend within $150.
- [ ] Only if T7.5 was done: open-weights usage documented in the README (for the open-weights flag).
- [ ] X post URL added in the platform (for Most Viral).
- [ ] `NOTICE.md` lists all sources and third-party code; no real personal data anywhere.
- [ ] Screenshot of the submission confirmation saved.

## 5. X post and thread (post after submitting)
**Post (check length ≤ 280 before posting):**
"When a law changes, which of your reviewed contract clauses just went stale? ClauseTrace traces the dependency graph, re-checks only the affected findings, and validates every proof with a deterministic checker. Built with Muse Spark. Demo ↓"

**Thread outline:** 1) the problem (law changes, reviews silently go stale) · 2) the demo video · 3) the six-tool bounded agent · 4) the checker tamper moment · 5) architecture diagram · 6) models and tools used (Muse Spark, Muse Code; Muse Spark Open only if used) · 7) repo link and honest limitations. Tag the official hackathon and Meta accounts as announced in the Discord. Most Viral counts likes, reposts and comments until the cutoff in the event rules, so post a clean video natively.

## 6. Bonus-prize checklist
- **Best Build on Meta Open Weight Models ($10K): optional.** Not targeted at the start. Only if T7.5 is done: Muse Spark Open runs through a partner host in the real verdict path; mention model id and provider in the README; make sure the partner can verify it.
- **Best Agentic Use-Case ($5K):** show autonomy (multi-step tool loop, re-query on stale) and bounds (six tools, status set by service).
- **Most Viral Project ($20K):** post video on X; submit the post link on the platform.
- **Community Vote ($10K):** public gallery, one vote per verified account — share the gallery link after the submission.
- Not targeted: Best Creative Build (Muse Image / Muse Wonder).

## 7. Fallbacks
- Live model slow or down → `LLM_MODE=replay` (identical output from cassettes).
- Deployed site down → run locally with `make dev`; keep the pre-recorded full-path video.
- Challenger call fails during the demo → the panel shows the recorded report labelled "recorded".
- Rehearse the replay path twice, once on a different network.

## 8. Judge-simulation prompt (run on Day 6 and Day 8)
```
Act as three strict judges for the Meta Global AI Developer Hackathon.
Rubric: Impact 30%, Use of Meta AI tooling 25%, Technical depth 20%, Demo 25%.
Anti-projects: basic RAG, anything political or about war, medical advice, simple analyzers, etc.
Below are my README and 3-minute demo script: [paste].
1. Stage 1: do I pass (fits a problem statement, genuinely uses Meta models)? Any risk of "basic RAG" or "political"?
2. Score 0-10 for each category with one-line reasons.
3. Any disqualification risk (new-work clarity, rights to data/assets, public repo, video)?
4. The 3 highest-value changes I can make in the time left.
Be critical, not agreeable.
```

## 9. Disclaimer (banner text, every screen)
"ClauseTrace shows whether a claim follows from accepted premises and the stated source versions. It does not assert that the law or the premises are true, and it is not legal advice. A qualified lawyer must review all findings. Demo data is fictional; simulated amendments are labelled."
