# 03 — Data model

## Stores and what lives where
| Store | Contents | Truth? |
|---|---|---|
| PostgreSQL | tenants, users, matters, documents metadata, clauses, facts, claims, findings, events, sources, provisions, legal tests, audit, jobs, budgets | **Yes — system of record** |
| Neo4j | graph projection of findings/facts/tests/provisions/versions | No — rebuildable |
| Object storage | uploaded files, page renders, audio clips, evidence-pack PDFs | Bytes only; metadata in PG |
| SQLite | demo tenant + local dev + cassette replay | Demo only |
| MongoDB | **not adopted** (decision): blobs → object storage, metadata → PG; a document store would duplicate truth | — |

## PostgreSQL schema (v1 of the rewrite)
- Identity: `tenants(id, name, key_id)`, `users(id, tenant_id, email,
  password_hash, status)`, `memberships(user_id, tenant_id, role)`,
  `api_keys(id, tenant_id, hash, scopes)`.
- Matters: `matters`, `matter_context`, `documents(id, tenant_id, matter_id,
  title, kind, storage_ref)`, `document_versions(sha256, text)`,
  `clauses(ref, heading, text, spans)`.
- Evidence core (carried from the demo model, tenant_id added):
  `facts(trust_class, origin, supersedes_id, approved_by/at)`, `claims`,
  `findings(status, proof_json, checker_report_json)`, `finding_events`,
  `challenger_reports`, `reviews`, `audit_log`, `edges` (mirrored to Neo4j),
  `runs`, `tool_calls`, `llm_calls(+ cost, tenant_id)`.
- Law: `sources`, `source_versions(is_simulated, supersedes_id)`,
  `provisions(key, text, sha256, effective_from/until)`, `rule_cards`
  (legal tests; `requires`, trust_class, approved_by).
- Ops: `intake_jobs(id, tenant_id, kind, stage, status, idempotency_key,
  error)`, `exports`, `tenant_budgets`, `eval_runs`.

## Invariants enforced in the database
- Append-only (triggers, as today): findings, source_versions, provisions,
  audit_log — UPDATE/DELETE rejected.
- Facts change only by supersession (new row + supersedes_id).
- Unique content hashes: `(tenant_id, sha256)` on document/source versions —
  identical re-upload is a no-op.
- Row-level tenancy: every tenant-owned table has `tenant_id NOT NULL` +
  composite indexes `(tenant_id, matter_id)`, `(tenant_id, status)`.

## Migration from the demo schema
Demo SQLite schema maps 1:1 to the PG tables above (same names/fields plus
`tenant_id`, defaulting to the demo tenant). Migration script reads a seeded
SQLite file and emits PG inserts in FK order; the seeded demo dataset is the
test fixture for the migration (counts + hashes must match exactly).

## P1 schema delta (as built, 2026-11-02)
- New table `tenants(id, name)`; demo tenant id is the constant `demo`.
- `tenant_id TEXT NOT NULL DEFAULT 'demo'` added to: matters, documents,
  facts, claims, findings, audit_log. Law tables (sources, source_versions,
  provisions, rule_cards) stay **global** in v1 — the law is shared; only
  firm data is tenanted. Claims/findings carry tenant_id directly so hot
  queries never join through matters to scope.
- Identity helpers live in `app.modules.identity` (`DEMO_TENANT_ID`,
  principal placeholder); auth itself lands with the Identity service.
- Engine: `CLAUSETRACE_DB_URL` selects the database (SQLAlchemy URL);
  unset keeps the SQLite demo path. NullPool applies to SQLite files.
- Graph store decision (amended): the target graph database is
  **FalkorDB** (openCypher, already available in the dev environment);
  Cypher in doc 02/03 reads the same against Neo4j if ever swapped.

## Graph projection (FalkorDB)
Node labels and edges as in 02 §Graph. Projection consumer applies
`finding.decided` / edge events idempotently (MERGE on ids). Parity test:
for every fixture matter, Cypher traversal result == Postgres traversal
result (finding id sets equal).
