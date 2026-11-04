# 04 — API contracts

## Rules (inherited, non-negotiable)
- `openapi/openapi.json` is the source of truth; frontend types are generated
  from it, never hand-written.
- Additive-only after each freeze point; breaking changes need a migration
  note and a version bump, logged as `[CONTRACT vN → vN+1]`.
- Every response carries machine fields (ids, codes) **and** lawyer display
  fields (the v9 `*_label` convention); the lawyer UI renders only labels.
- Errors: `{error: {code, message}}` — code for machines, plain message for
  lawyers (no banned technical strings in `message`).

## v11 surface (rewrite target; v10 stays live until parity)
- Auth: `POST /api/auth/login`, `/logout`, `/invite`, `GET /api/me`.
- Tenancy: every matter-scoped route requires membership; cross-tenant → 404.
- Matters/documents: CRUD + `POST /api/documents` (multipart upload),
  `POST /api/documents/{id}/extract` (async → job), `GET /api/jobs/{id}`.
- Intake: `POST /api/scans` (image/PDF page), `POST /api/dictations` (WAV),
  both create **proposed** evidence only (trust rules unchanged).
- Verification: `POST /api/claims` (sync ask), `GET /api/claims/{id}/current`,
  history, `POST /api/findings/{id}/review`, `POST /api/proofs/verify`.
- Law: sources/versions/diff, `POST /api/sources/{id}/ingest` (draft),
  `POST /api/source-versions/{id}/approve` (new: lawyer gate before impact),
  impact reports, `POST /api/impact/{id}/reverify`, `GET /api/reverify-list`.
- What-if: `POST /api/counterfactual` (read-only; propositional verdicts).
- Evidence: `GET /api/graph`, `GET /api/audit`, `POST /api/exports/evidence-pack`.
- Admin: members/roles, tenant budget, eval-run status (staff only).

## Compatibility promise
The demo tenant keeps the v10 contract working until the new frontend passes
the full E2E suite against v11; then v10 is frozen (read-only) for judges.
