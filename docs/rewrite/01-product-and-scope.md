# 01 — Product and scope (Rewrite, Option B)

## Goal
Rebuild ClauseTrace as a production-level, lawyer-first system in both
frontend and backend, while the current verified demo path (SQLite +
cassettes, contract v10) stays runnable as the demo tenant until the new
stack passes the same end-to-end flows.

## Users and jobs
- **Lawyer (primary):** ask whether a clause meets a requirement; approve or
  challenge facts; re-check answers when the law changes; export evidence.
- **Firm admin:** matters, members, roles, budgets.
- **Reviewer:** read-only evidence packs.

## Scope of the rewrite
IN: multi-tenant matters; real document intake (text/PDF/scan/audio);
maintained law sources; live AI with evaluation gates; lawyer-first UI;
evidence export; audit everywhere.
OUT (unchanged from SHOWDOWN): legal advice claims, other jurisdictions at
launch, end-client access, open-weight hosting, realtime voice.

## Non-negotiable invariants (carried over, restated for the new stack)
1. The deterministic checker decides validity; the model only drafts.
2. Only the memory/decision service sets a finding's status.
3. Evidence is append-only; deletion is crypto-shredding, never edits.
4. Only lawyer_confirmed / document_extracted facts support a proof.
5. Every citation resolves to (source_version, provision, span, sha256).
6. Conclusions are always conditional on listed facts + law version.
7. No technical strings (ids, hashes, JSON) in lawyer-facing UI or copy.

## Success definition
A cold-start lawyer can: create a matter, upload a DPA (PDF/scan) or dictate
a fact, approve the proposed facts, ask a clause question and read a checked
cited answer, watch a law amendment flag affected answers, re-check them,
resolve a conflicting-interpretation answer, and export the evidence pack —
on the new stack, with the golden-set eval report green.
