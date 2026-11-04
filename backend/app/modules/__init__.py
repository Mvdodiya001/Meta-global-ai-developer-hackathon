"""Modular service boundaries (Rewrite P0).

The backend is a modular monolith first: one deployable, with package
boundaries that match the microservice split in `docs/rewrite/02`. Each
subpackage is the public facade for its domain — other code imports from
`app.modules.<domain>`, never from a sibling domain's internals.

Dependency rules (enforced by tests/test_module_boundaries.py):
- `checker/` imports nothing from `app` (unchanged, AST-enforced).
- Domains may depend on `app.core` and on lower domains only:
  law/evidence data < verification < api. Intake depends on the model
  gateway (`app.agent.llm` / `app.agent.transcribe`) and matters.
- No domain imports `app.api` (the HTTP layer sits above all domains).
- Only `verification` (via services.memory) may decide a finding status.

Behaviour moves behind these facades in P2; in P0 they only re-export the
existing implementations so the split is structural, not behavioural.
"""
