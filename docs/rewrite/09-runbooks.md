# 09 — Runbooks (Rewrite P5)

## Model outage (Meta API unreachable / erroring)
1. Symptoms: Ask/scan/dictation return the plain "prepared set / try again"
   message; `llm_calls` stops growing; eval smoke fails.
2. Action: switch tenants to replay/demo mode (`LLM_MODE=replay`) so the
   recorded paths keep working; page the on-call with the gateway error
   rate. Never fabricate answers while the model is down — UNKNOWN and
   "needs your review" are the honest outputs.
3. Recovery: when the API recovers, run `scripts/run_evals.py`; require
   the gate green before restoring live mode.

## Tenant over budget
1. Symptom: live Ask raises "over its model budget" (typed, logged).
2. Action: check spend on `/api/admin/overview`; raise
   `CT_TENANT_BUDGET_USD` only with the firm admin's written approval;
   never silently.

## Source fetch / amendment failure
1. Symptom: a law version fails span verification or fetch.
2. Action: the amendment is **not** applied — old findings stay current
   and nothing is marked stale. Fix the snapshot, re-run ingest; impact
   only ever runs on approved versions.

## Graph projection rebuild (FalkorDB lost or drifted)
1. The record (Postgres/SQLite) is the truth; the graph is disposable.
2. Run: `CT_GRAPH_PASSWORD=... backend/.venv/bin/python -c
   "from app.modules.evidence.graph_projection import project; ..."`
   or the parity test (`CT_GRAPH_TEST=1 pytest tests/test_graph_projection.py`).
3. Verify: parity test green (projection dependents ⊇ record dependents
   for the seeded provisions).

## Key rotation (MODEL_API_KEY)
1. Create the new key in the Meta dashboard; deploy it to the server env;
   restart the API; run the eval gate; revoke the old key.
2. The key is never printed, logged, or committed (`.env` is git-ignored).

## Database restore (Postgres)
1. Restore the latest backup to a scratch instance (PITR where available).
2. Run the parity check: migrate/compare row counts per table against
   production (`scripts/migrate_sqlite_to_postgres.py` prints the table
   counts used for this), then the eval gate against the restored copy.
3. Only then promote it. Drill this before pilot and quarterly.

## Demo reset (local/demo environments only)
`make reset-demo` reseeds the demo database. With the NullPool engine it
is safe while the server runs. Never run it against a tenant database.
