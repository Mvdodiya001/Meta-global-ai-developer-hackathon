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
| Day 3 | T2.1 live never run under pytest | credits still ~$0.01 |

## Sync points
| ID | Date reached | Verified by | Notes |
|----|--------------|-------------|-------|
| SP1 contract v1 | | | still **v0**; T1.5 did not bump OpenAPI |
| SP2 vertical slice | | | |
| SP3 impact API | | | |
| SP4 core gate | | | |
| SP5 freeze | | | |