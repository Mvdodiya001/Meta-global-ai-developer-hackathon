# 06 — Testing and quality

## Layers
1. **Unit** — checker + proplogic (property-style cases: tampered premise,
   superseded version, conflicting tests, disputed facts), parsers, diff.
2. **Service** — memory status paths (all five statuses + bands), impact
   exactness, re-verify fresh-lookup rule, premise supersession, tenancy
   isolation (cross-tenant = 404 everywhere).
3. **Contract** — every endpoint against openapi examples; stub parity tests
   (the demo pattern, kept); frontend type generation is a CI step.
4. **Graph parity** — Neo4j traversal == Postgres traversal on fixtures.
5. **Intake** — PDF (text + image-only), scan, and ASR replay cassettes;
   malformed uploads → typed errors; live never runs in tests.
6. **E2E** — browser flows per screen on staging (golden path + law-change
   path + approval-gate path).
7. **AI evaluation (release gate)** — golden matters with known outcomes:
   verdict agreement, citation exactness = 100% on admitted evidence,
   premise-admission violations = 0, cost per verified clause within budget.
   A failing eval blocks release; results are stored per run.

## Rules (carried over)
- Tests first for checker, memory, impact, intake.
- Every bug gets a regression test (the approve-500 / run-id / audit fixes
  are the template).
- Lane checks must be green before any task is called done:
  backend ruff + mypy + pytest; frontend lint + vitest + build.
- No live model calls in any test, ever.

## Performance budgets (fail the build/release if regressed > 20%)
Ask p95 < 8 s live; checker < 10 ms; impact apply < 2 s; read endpoints
p95 < 300 ms; intake jobs report progress within 2 s of upload.
