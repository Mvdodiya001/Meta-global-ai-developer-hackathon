# HUMAN_LOG.md — your commits and decisions (only you write here)

Commit with the guarded alias: `git hc -m "T2.1: ..."` (installed by `make hooks`). Push with `git hp`.
Commit one lane at a time:
- Muse Code lane: `git add backend corpus scripts openapi Makefile`
- Cursor lane: `git add frontend README.md`
- Docs: `git add docs AGENTS.md PLAN.md PROGRESS.md NEW_WORK.md NOTICE.md`
Before each agent session, commit a checkpoint so `git diff` shows only that session's work.

## Commits
| Date/time (IST) | Hash | Lane | Tasks covered | Notes (reviewed? check result?) |
|-----------------|------|------|---------------|---------------------------------|
| Day 1 | 91fc1f | docs | T0.1 | first commit, docs + licence only |
| Day 1 | f01554 | scripts | T0.2, T0.3 | Meta hello-world + cost; plain commit before hooks |
| Day 1 | b5d63ec | process | T0.8 | git guards; `git hc` / `git hp` |
| Day 1 | 391a51a | mixed | T0.4, T0.6 | scaffold + corpus NOTES; mixed-lane commit |
| Day 1 | 09477b6 | MC | T0.7 | contract v0 + stub |
| Day 2 | d1efba8 | MC | T1.1 | schema + append-only triggers |
| Day 2 | 72e78e8 | MC | T1.2 | source snapshots + provisions |
| Day 2 | 7ab269a | MC | T1.3 | 7 rule cards + span loader |
| Day 2 | 010a2c9 | MC | T1.4, T1.5 | seed demo + version diff / as-of |
| Day 2 | 7ab269a | CU | T5.0 | UI foundation on mocks |
| Day 3 | 99a4f74 | MC | T2.1 | LLM gateway replay/mock; 0 live credits |
| Day 3 | 99a4f74 | CU | T5.1 | Screen 1 clause review |
| Day 3 | 1ad7ede | CU | T5.1 | CI: move findingTraces off gitignored `lib/` |
| Day 3 | 5c45b05 | MC | T2.2 | clause extraction + cassette; pushed; mixed with T5.2 |
| Day 3 | 5c45b05 | CU | T5.2 | Screen 2 impact + re-verify split; same commit, pushed |
| Day 3 | not committed | MC | T2.3, T3.1, T3.2, T2.4, T2.5, T3.3, T4.1–T4.5, T6.1 | claims, checker, six tools, loop, memory, graph, impact, re-verify, premises, API v1, challenger. Fill hash after `git hc` |
| Day 3 | not committed | CU | T5.3, T6.2, T5.4 | Screen 3, challenger panel, live v1 wire. Same local batch |

## Decisions and incidents
| Date | What happened / decided | Action taken |
|------|-------------------------|--------------|
| Day 1 | Git guards on | use `git hc` / `git hp` |
| Day 1 | Mixed T0.4+T0.6 commit | prefer one lane per commit |
| Day 1 | `.env.example` missing | still open |
| Day 1 | Port 8000 used by memopops | stub tested on 8001 |
| Day 2 | T1.3 CT1–CT3 names differ from ARCHITECTURE | keep cards; remap later or accept mapping in this log |
| Day 2 | Dropped `PRAGMA foreign_keys=ON` (SQLAlchemy flush bug) | FKs enforced in services |
| Day 3 | `frontend/src/lib/` ignored by root `.gitignore` `lib/` | traces moved to `frontend/src/utils/` |
| Day 3 | T2.1 live never run under pytest | credits were ~$0.01 then; later live calls below |
| Day 3 | T2.2 + T5.2 pushed as 5c45b05 | mixed message left as pushed |
| Day 3 | Gateway default moved to muse-spark-1.3-contributor | old cassettes replaced; loop had already spent ~$0.80 |
| Day 3 | `make record` loads `.env` and fails fast with no key | key not printed |
| Day 3 | Contract v0 → v1 in the working tree | real router when `API_STUB=0`; stub stays the default |
| Day 3 | `POST /api/claims` does not start the agent loop | Screen 1 cannot finish a finding; core gate not green |
| Day 3 | Template is `env.example`, not `.env.example` | no secret in that file; `.env` stays gitignored |
| Day 3 | Logged model spend about $0.88 | billing page not re-checked |

## Sync points
| ID | Date reached | Verified by | Notes |
|----|--------------|-------------|-------|
| SP1 contract v1 | 2026-10-30 | T4.5 log | `openapi` info.version v1 in the working tree; not committed |
| SP2 vertical slice | 2026-10-30 | T2.5 log | clause 9.2 proof accepted in replay tests; `python -m app.cli` not checked |
| SP3 impact API | 2026-10-30 | T4.5 log | impact ids `IMP-{version}` from STALE events; not committed |
| SP4 core gate | | | not reached. Claims route does not run the loop. Browser not verified on this app |
| SP5 freeze | | | |