# CURSOR_LOG.md — written ONLY by Cursor (append-only)

Cursor: you never commit and never add co-author or "Generated with" text. Log every task here. The human reads this to track your work and decides what to commit.
Time: `TZ=Asia/Kolkata date '+%Y-%m-%d %H:%M IST'`. Heading format must stay greppable: `## [T5.1] DONE · <YYYY-MM-DD HH:MM IST>`.
Status words: STARTED · DONE · PARTIAL · BLOCKED. Special tags in entries: `[REQ → H]`, `[REQ → MC]`, `[CONFLICT]`.
At session start: read `docs/logs/MUSE_CODE_LOG.md` (read-only). If the latest `[CONTRACT vN]` is newer than the one you built against, run `npm run gen:api` first and log it.

## Entry template (copy for each STARTED and final entry)
```
## [Txx.x] STARTED|DONE|PARTIAL|BLOCKED · <time>
- Task: <title>
- Built against: API_STUB | mocks | real API · contract version vN
- Files changed: <path (new|modified|deleted)>, ...
- What changed: <2–4 lines>
- Checks run: `make check-frontend` → pass|fail (<counts or error>)
- Decisions / assumptions: <or none>
- Requests: [REQ → MC] <missing field or endpoint> | [REQ → H] ... | none
- UI rules checked: disclaimer banner present · AI-draft/Lawyer-reviewed badge · SIMULATED badge · status not color-only
- New-work note: <component built, date>
- Third-party added: <name version licence> | none
- Ready for human commit: yes|no — suggested message: `Txx.x: <plain message, no trailers>`
```

---
## Log (newest at the bottom)
_(no entries yet)_
