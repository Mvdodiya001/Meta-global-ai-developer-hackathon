# Contract freeze and v11 draft (Rewrite P0)

- **Frozen:** contract **v10** in `openapi.json`. It describes the shipped
  demo exactly and does not change during the rewrite until the new stack
  reaches parity (docs/rewrite/04). Frontend work against v10 continues.
- **Draft:** `openapi.v11-draft.json` — a copy of v10 with
  `info.version: "v11-draft"`. All rewrite API work lands there first as
  additive changes (tenancy/auth, jobs, source-approve, evidence export).
  Nothing may be removed or renamed in the draft without a migration note.
- Promotion rule: when v11 reaches parity plus its new endpoints, it is
  copied over `openapi.json` in one `[CONTRACT v10 → v11]` change, frontend
  types are regenerated, and v10 is archived to `openapi/archive/`.
- **Promoted in P3 (2026-11-02):** `[CONTRACT v10 → v11]` — `openapi.json`
  is now v11 (additive: document upload, job status, fact correction).
  The draft file remains as the working copy for the next additive round.
