# PROMPT.md — the one prompt (works for Muse Code and Cursor)

Paste this at the start of every agent session. Change only the first line: set `TOOL` to `Muse Code` or `Cursor`, and set `TASK` to a task ID from `docs/TASKS.md` (or `next`).

```
TOOL: <Muse Code | Cursor>        TASK: <task ID, e.g. T2.1, or "next">

You are building ClauseTrace with another AI tool working at the same time. Read, in this order: AGENTS.md, PLAN.md, docs/TASKS.md, docs/DATA_MODEL_API.md (if you do backend work or touch the API contract), your own log in docs/logs/, and, read-only, the other tool's log.

1. LANE. If TOOL is Muse Code: you own backend/, corpus/, scripts/, openapi/, Makefile and docs/logs/MUSE_CODE_LOG.md; call models only through backend/app/agent/llm.py; check with `make check-backend`. If TOOL is Cursor: you own frontend/, README.md and docs/logs/CURSOR_LOG.md; never call models and never open the database; build against API_STUB=1 or openapi/examples/; if the latest [CONTRACT vN] in docs/logs/MUSE_CODE_LOG.md is newer than your types, run `npm run gen:api` first; check with `make check-frontend`. Edit nothing outside your lane.

2. TASK. Do only TASK. "next" means the first unfinished task in your lane whose dependencies are done. Write the tests first where the task says so. Stop when its "Done when" lines pass.

3. MODELS. Use only the Meta Model API (Muse Spark). Do not integrate Baseten, Modal, Fireworks, or any open-weights host.

4. GIT IS READ-ONLY. Allowed: git status, diff, log, show. Never run git add, commit, push, pull, fetch, merge, rebase, reset, checkout, switch, restore, branch, tag, stash, clean, worktree or config, and never click an editor button that stages or commits. Never write Co-authored-by, "Generated with", or any "written by AI / Cursor / Muse Code" text in any file, comment, doc or message.

5. LOG. In your own log (append-only, never rewrite old entries), add `## [<task>] STARTED · <time>` now, and `## [<task>] DONE|PARTIAL|BLOCKED · <time>` at the end. Get the time with: TZ=Asia/Kolkata date '+%Y-%m-%d %H:%M IST'. The final entry lists: files changed, what changed, checks run and their real result, decisions and assumptions, contract change, requests, new-work note, third-party additions, credit spend, and "ready for human commit: yes/no" with a plain suggested commit message. Never claim a check passed that you did not run.

6. STOP AND ASK. If you need a file outside your lane, a schema / API-contract / tool-list / dependency change, or a requirement is unclear, write [REQ → H] in your log and stop that part. If you find changes in your lane that you did not make, stop and write [CONFLICT].

7. FIXED RULES. The checker never imports app.agent or any LLM client. The model gets exactly six tools (lookup_source, list_dependent_claims, get_premise, verify_derivation, propose_finding, request_lawyer_review). Only services/memory.py sets a finding's status. Findings, source versions, provisions and the audit log are append-only. Demo data is fictional. No political, war or medical content. The disclaimer banner shows on every screen.

Finish by printing: files changed, checks run, and the suggested commit message. Do not commit.
```
