# 07 — Deployment and operations

## Environments
- **local:** SQLite/demo tenant, replay cassettes, seeded fixtures.
- **staging:** full new stack (Postgres + Neo4j + Redis + object storage),
  live models, demo tenant + sandbox tenant; E2E + eval gates run here.
- **production:** same topology as staging; separate keys, budgets, backups.

## Packaging
- One container per service (gateway, verification, law, matter, evidence,
  intake-worker, challenger-worker); frontend as static build behind the
  gateway origin (single https origin to the browser).
- Compose for local/staging parity; the same images promote to production.
- Config is env-only (no secrets in images or repo); `.env.example` lists
  every variable with a plain-language comment.

## Data safety
- Postgres: managed backups + point-in-time recovery; restore drill before
  pilot and quarterly.
- Object storage: versioned buckets; exports retained per tenant policy.
- Neo4j: treated as disposable — rebuild script from Postgres events is the
  backup strategy; drill it in staging.
- Demo reset (`make reset-demo`) exists only in local/demo environments.

## Operations
- Health: `/health` per service + aggregate; the root route stays a service
  index (pattern exists).
- Metrics/alerts: Ask latency + failures, queue depth/DLQ, model spend per
  tenant vs budget, eval failures, 5xx rate.
- Runbooks: model outage (queue Asks, show plain-language notice), source
  fetch failure, graph projection rebuild, key rotation.
- Releases: contract version noted in the deploy log; frontend and backend
  deploy independently against the additive contract.

## Security checklist (gate before any external user)
TLS everywhere; hashed API keys; session rotation; rate limits per tenant;
upload type/size validation (WAV/PDF/image allowlists); audit on reads of
findings; secrets never logged (pattern exists in the gateway).
