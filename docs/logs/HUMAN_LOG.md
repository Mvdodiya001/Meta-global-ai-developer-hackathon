## Commits
| Date/time (IST) | Hash | Lane | Tasks covered | Notes (reviewed? check result?) |
|-----------------|------|------|---------------|---------------------------------|
| Day 1 | 91fc1f | docs | T0.1 | first commit, docs + licence only |
| Day 1 | f01554 | scripts | T0.2, T0.3 | Meta API hello-world + cost calibration; committed with plain `git commit` before hooks were on |
| Day 1 | b5d63ec | process | T0.8 | `make hooks`; plain `git commit` blocked; `git hc` / `git hp` work; pushed |
| Day 1 | 391a51a | mixed | T0.4, T0.6 | backend + frontend scaffold, CI, `corpus/NOTES.md`; `make check-backend` and `make check-frontend` passed locally; CI on GitHub not confirmed; mixed-lane commit (should have been split); pushed |

## Decisions and incidents
| Date | What happened / decided | Action taken |
|------|-------------------------|--------------|
| Day 1 | Git guards installed (`make hooks`) | Plain commit/push blocked; use `git hc` / `git hp` |
| Day 1 | T0.4 + T0.6 landed in one mixed commit (`391a51a`) | Note for later: commit by lane (backend / frontend / docs) |
| Day 1 | Muse Code added `.github/workflows/ci.yml` (outside AGENTS.md lane list, but required by T0.4) | Accepted; keep CI in `.github/` |
| Day 1 | `.env.example` still missing from repo root | Add before live backend work |
| Day 1 | T0.7 started (MC, 09:13 IST) | Waiting on OpenAPI v0 + `API_STUB=1`; not committed yet |

## Sync points
| ID | Date reached | Verified by | Notes |
|----|--------------|-------------|-------|
| SP1 contract v1 | | | waiting on T0.7 (contract v0) then Day 2 |
| SP2 vertical slice | | | |
| SP3 impact API | | | |
| SP4 core gate | | | |
| SP5 freeze | | | |