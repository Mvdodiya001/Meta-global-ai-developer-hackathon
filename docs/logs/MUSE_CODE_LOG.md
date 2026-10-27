# MUSE_CODE_LOG.md — written ONLY by Muse Code (append-only)

Muse Code: you never commit and never add co-author or "Generated with" text. Log every task here. The human reads this to track your work and decides what to commit.
Time: `TZ=Asia/Kolkata date '+%Y-%m-%d %H:%M IST'`. Heading format must stay greppable: `## [T2.1] DONE · <YYYY-MM-DD HH:MM IST>`.
Status words: STARTED · DONE · PARTIAL · BLOCKED. Special tags in entries: `[CONTRACT vN → vN+1]`, `[REQ → H]`, `[REQ → CU]`, `[CONFLICT]`.

## Entry template (copy for each STARTED and final entry)
```
## [Txx.x] STARTED|DONE|PARTIAL|BLOCKED · <time>
- Task: <title>
- Files changed: <path (new|modified|deleted)>, ...
- What changed: <2–4 lines>
- Checks run: `make check-backend` → pass|fail (<counts or error>)
- Decisions / assumptions: <or none>
- Contract change: none | [CONTRACT vN → vN+1] <what>
- Requests: [REQ → H] ... | [REQ → CU] ... | none
- New-work note: <component built, date>
- Third-party added: <name version licence> | none
- Credit spend: <tokens / $> | none
- Ready for human commit: yes|no — suggested message: `Txx.x: <plain message, no trailers>`
```

---
## Log (newest at the bottom)
_(no entries yet)_
