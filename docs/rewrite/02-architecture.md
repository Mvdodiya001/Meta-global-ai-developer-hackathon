# 02 — System architecture (microservices)

## Topology

```
Browser (React SPA)
   │ HTTPS
   ▼
API Gateway (FastAPI) ── authN/Z, tenancy, rate limit, request ids
   ├── Identity Service        users, tenants, roles, sessions, API keys
   ├── Matter Service          matters, documents, versions, clauses
   ├── Verification Service    agent loop, six tools, memory (status owner)
   │      └── checker library  pure, in-process (verify + proplogic)
   ├── Law Service             sources, versions, provisions, legal tests
   ├── Impact Service          diff, stale marking, re-verify, counterfactual
   ├── Intake Workers (async)  PDF parse, page render, scan vision, ASR,
   │                           extraction — queue consumers, idempotent
   ├── Challenger Worker       second-pass review (optional per tenant)
   └── Evidence Service        graph queries, audit, evidence-pack export

Data: PostgreSQL (system of record) · Neo4j (graph projection, rebuildable)
      Object storage (files, scans, audio, exports) · Redis (queue/cache)
Models: ONE model gateway module used by every service that calls Meta APIs.
```

## Service boundaries and rules
- A service owns its tables; cross-service reads go through the owning
  service's API or published events — never another service's tables.
- **Verification Service is the only writer of finding status.** Other
  services emit facts/evidence; they never decide.
- **Checker stays a pure library** inside Verification (no network, no model
  imports, AST-isolation test carried over). Propositional logic module
  (`proplogic`) ships with it.
- Events (at-least-once, idempotent consumers): `document.uploaded`,
  `document.extracted`, `fact.proposed`, `fact.approved`, `source.approved`,
  `finding.decided`, `finding.stale`, `finding.reverified`.
- Sync path (Ask) stays synchronous end-to-end (structure → loop → checker →
  decide); everything slow is a job with a status endpoint.

## Graph database role (Neo4j)
- Projection, not truth: nodes Finding/Fact/RuleCard(legal test)/Provision/
  SourceVersion/Clause; edges DEPENDS_ON, DERIVED_FROM, PART_OF, AFFECTS.
- Rebuilt from Postgres events (`scripts/rebuild_graph.py`); any projection
  loss is recoverable by replay. Impact/counterfactual traversals run in
  Cypher; the Postgres recursive-CTE implementation remains as fallback and
  as the parity oracle in tests (both must agree on fixtures).

## Model gateway (all Meta calls, one place)
- Responses API: structure, extraction, loop, challenger (Muse Spark).
- Vision input: scanned pages and image-only PDF pages (Muse Spark).
- ASR: Muse Voice Transcribe file endpoint (dictation; diarization for
  recordings). Live/replay/mock modes; request-hash cassettes in CI/demo;
  per-tenant budgets, token + audio-hour metering, circuit breaker.

## Cross-cutting
- Tenancy: `tenant_id` from the authenticated principal, injected by the
  gateway, enforced in a data-access helper; cross-tenant reads return 404.
- Observability: structured logs with request/tenant/matter ids, traces
  across gateway → services → workers, metrics (Ask latency, tool calls,
  model spend, queue depth), alerting on eval-gate failures.
- Errors: machine `code` + lawyer-safe `message` at the edge (v9 convention,
  kept); internal errors never leak stack traces or hashes to the UI.
