# PLAN.md — Parallel build plan for Muse Code + Cursor

Read with `AGENTS.md` (rules), `docs/TASKS.md` (task details) and `PROMPT.md` (the one prompt to paste). This file says **who does what, in what order, and how you track it**.

**Three rules that shape everything:**
1. **Agents never commit.** Not `git commit`, not `git push`, and no `Co-authored-by` or "Generated with" lines anywhere. Only you (the human) commit.
2. **Agents log everything** in their own file under `docs/logs/`, so you can see what each one did, what changed, and what is ready for you to commit.
3. **Two lanes, disjoint folders.** Muse Code works on the backend; Cursor works on the frontend. They run at the same time and never edit the same file.

**Models: Meta Model API only (Muse Spark).** Open weights (Muse Spark Open on a partner host) is an optional extra, task T7.5, only if the core is done and you have access. Nothing else depends on it.

## 1. Roles and ownership
| | Muse Code (MC) | Cursor (CU) | You (H) |
|---|---|---|---|
| Owns (may edit) | `backend/**`, `corpus/**`, `scripts/**`, `openapi/**`, `Makefile`, `docs/logs/MUSE_CODE_LOG.md` | `frontend/**`, `README.md`, `docs/logs/CURSOR_LOG.md` | everything else: `docs/**` (except the two agent logs), `AGENTS.md`, `PLAN.md`, `PROMPT.md`, `PROGRESS.md`, `NEW_WORK.md`, `NOTICE.md`, `docs/logs/HUMAN_LOG.md` |
| May read | everything | everything | everything |
| Git | read-only (`status`, `diff`, `log`, `show`) | read-only | **all commits and pushes** |
| Calls models | yes (credits) | no (UI uses the API only) | — |
| Touches the DB | yes | never (API only) | — |

If an agent needs a change in a file it does not own, it writes a request in its log (`[REQ → H]`, `[REQ → CU]` or `[REQ → MC]`) and stops that sub-task. It never edits the file.

## 2. Build order by day
Day numbers are relative: **Day 1 is the day you start.** If you start late or fall behind, do not move the end: use the cut order in `docs/TASKS.md`.

| Day | Muse Code lane | Cursor lane | You |
|-----|----------------|-------------|-----|
| **1** | T0.3 Meta API hello-world · T0.4 backend scaffold + CI · T0.7 contract v0 + stub mode | T0.4 frontend scaffold · T5.0 layout, design tokens, disclaimer banner, routes | T0.1 repo + first commit · T0.2 Meta credits · T0.6 corpus · T0.8 install git guards |
| **2** | T1.1 schema · T1.2 sources · T1.3 rule cards · T1.4 contract + seed · T1.5 diff/as-of → **SP1: contract v1** | T5.0 shared components on mock data (FindingCard, TrustChip, ProofSyllogism, DiffView, StaleGraph) | finish T0.6 · review rule cards · commit by lane |
| **3** | T2.1 gateway · T2.2 extraction · T2.3 claims · T3.1 checker core | T5.1 Screen 1 (clause review) on mocks | review + commit |
| **4** | T3.2 checker steps · T2.4 tools · T2.5 agent loop · T3.3 memory service → **SP2: vertical slice** | finish T5.1 · start T5.2 Screen 2 (diff + impact graph) on mocks | run the slice yourself · review + commit |
| **5** | T4.1–T4.5 graph, impact, re-verify, challenge, endpoints → **SP3** | finish T5.2 · T5.3 Screen 3 (lawyer control) on mocks | review + commit |
| **6** | T6.1 challenger (Muse Spark second pass) · fix API gaps found while wiring | T5.4 wire to real API · T6.2 challenger panel | **core gate at end of day** |
| **7** | T8.1 scenario tests · T8.2 cassettes + deploy · one stretch (T7.x) only if the gate is green | polish, accessibility, empty/error states · T9.1 README draft | T8.3 rough video · T8.4 judge simulation · **feature freeze at end of day** |
| **8** | fixes only, if you ask | T9.1 final README | T9.2 video · T9.3 X post · T9.4 **submit** |
| 9 | nothing unless you ask for a bug fix | nothing | buffer: re-check links only |

Cursor's free time (when its next screen is blocked): loading/error/empty states, keyboard navigation, dark-mode contrast, responsive layout, copy review against the disclaimer rules. Never wait idle for the backend.

## 3. Sync points (where the lanes meet)
| ID | When | Muse Code delivers | Cursor then | Proof you can check |
|----|------|--------------------|-------------|---------------------|
| SP1 | End of Day 2 | Contract v1: every endpoint in `DATA_MODEL_API.md` §7, example payloads in `openapi/examples/`, stub mode `API_STUB=1` | Switches mocks to the stub server | `curl localhost:8000/api/health`; log entry `[CONTRACT v1]` |
| SP2 | End of Day 4 | Vertical slice: CLI verify stores a checked finding; real finding JSON added to examples | Checks Screen 1 against the real finding shape | You run the CLI and open the finding |
| SP3 | End of Day 5 | Impact, graph, diff, audit, review endpoints real | Wires Screens 2 and 3 on Day 6 | Fixture amendment flags the expected findings |
| SP4 | End of Day 6 | Gap fixes | Full UI on real API | **Core gate:** whole demo path runs end to end |
| SP5 | End of Day 7 | Deployed build | Final polish | **Feature freeze** |
If Muse Code is late for a sync point, Cursor keeps building on the stub or mocks and Muse Code logs the delay. Nobody waits.

## 4. Contract-first protocol
- Source of truth: `openapi/openapi.json`, plus example payloads in `openapi/examples/*.json`. Field `info.version` is the contract version (`v0`, `v1`, …).
- Cursor generates its API types from `openapi.json` (`npm run gen:api`) and builds on `API_STUB=1` or mock handlers fed from the examples.
- After SP1, only **additive** changes (new optional fields, new endpoints). A breaking change needs your approval: Muse Code logs `[REQ → H] breaking change …` and waits.
- Every change is logged by Muse Code as `[CONTRACT vN → vN+1] what changed`. Cursor reads that log at the start of every session and regenerates types if the version moved.

## 5. Working at the same time in one folder
- Disjoint folders (section 1). Neither agent touches `.git`, `Makefile` (MC only), the other's folder, or root docs.
- Ports: backend `8000`, frontend `5173`. Do not change them.
- Database and `.cache/llm/` belong to Muse Code. Cursor never opens the SQLite file.
- Lane checks: Muse Code runs `make check-backend`; Cursor runs `make check-frontend`. Only you run the full `make check`.
- A broken lane never blocks the other: Cursor uses the stub or mocks if the backend is mid-change.
- If an agent sees changes it did not make in its own lane, it stops, logs `[CONFLICT]`, and waits for you.

## 6. Logging protocol (how you track everything)
Files: `docs/logs/MUSE_CODE_LOG.md`, `docs/logs/CURSOR_LOG.md` (each written only by its agent) and `docs/logs/HUMAN_LOG.md` (you: commits and decisions).
- At the **start** of a task the agent appends a `STARTED` entry; at the **end** it appends a `DONE`, `PARTIAL` or `BLOCKED` entry. Entries are never rewritten, only appended.
- Each agent reads the other agent's log (read-only) at session start.
- Heading format (greppable): `## [T2.1] DONE · <YYYY-MM-DD HH:MM IST>`. The agent gets the real time with `TZ=Asia/Kolkata date '+%Y-%m-%d %H:%M IST'`.
- Entry fields: files changed, what changed, checks run and result, decisions/assumptions, contract change, requests, new-work note, third-party added, credit spend, **ready for human commit (yes/no) + suggested commit message (no trailers)**.
- See the board any time: `make status` (prints every task heading from the logs).

## 7. Your routine (about 10 minutes, 2–3 times a day)
1. **Before starting an agent session:** commit your current checkpoint. Then `git diff` afterwards shows only what that agent did.
2. When an agent logs `DONE` and "ready for human commit: yes": run `git status` and `git diff --stat`, then skim the diff of its lane only (`git diff -- backend corpus scripts openapi` or `git diff -- frontend`).
3. Run the lane check (`make check-backend` or `make check-frontend`).
4. Commit by lane using the guarded alias (the agent's suggested message is a starting point):
   ```
   git add backend corpus scripts openapi Makefile
   git hc -m "T2.1: add LLM gateway with replay mode"
   git add frontend README.md
   git hc -m "T5.1: clause review screen on mocks"
   ```
5. Add one line to `docs/logs/HUMAN_LOG.md`: time, commit hash (`git log -1 --format=%h`), tasks covered.
6. End of day: `git hp` (guarded push), then update `PROGRESS.md` and `NEW_WORK.md` from the logs. Or paste both agent logs to me and I will write the `PROGRESS.md` update and `NEW_WORK.md` rows.
7. Never merge two lanes into one commit.
Hooks and aliases are installed once with `make hooks` (task T0.8). They block commits and pushes unless `CT_HUMAN=1` (set by `git hc` / `git hp`) and reject messages containing `Co-authored-by`, `Generated with` or the robot emoji.

## 8. The one prompt
Use `PROMPT.md`. It works for both tools: set `TOOL` (Muse Code or Cursor) and `TASK` (an ID from `docs/TASKS.md`, or `next`), paste, and go. It contains the lane, Meta-only model rule, read-only git, logging, and stop-and-ask rules.
End of session (either tool), if it forgets: `Append your final log entry now. List every file you changed, the checks you ran, and a suggested commit message. Do not commit.`

## 9. If something goes wrong
- **An agent committed anyway:** `git log -3` to see it. Undo keeping the files: `git reset --soft HEAD~1`, then recommit yourself with `git hc`. Note it in `HUMAN_LOG.md` and remind the agent of the rule. Check Cursor and Muse Code settings for any auto-commit or attribution option and turn it off.
- **A co-author or "generated" line slipped into a commit:** `git hc --amend` and delete the line. If already pushed, tell me before changing history.
- **Both agents edited the same file:** stop both, `git diff` the file, keep one version, log it in `HUMAN_LOG.md`.
- **Hooks block you:** you used plain `git commit`; use `git hc`.
- The hooks are a safety net, not a lock: the rule in `AGENTS.md` section 5 is the real control.

## 10. Done means
A task is done only when: its "Done when" lines in `docs/TASKS.md` pass; the lane check is green; the agent's `DONE` entry lists the files changed; and you have reviewed and committed it.
