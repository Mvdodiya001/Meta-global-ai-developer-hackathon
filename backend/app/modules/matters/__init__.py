"""Matters domain: matters, documents, versions, clauses.

Owns: the document lifecycle (upload → version → clauses) and demo
seeding. Public interface: the seed module (document/matter creation
moves here fully in P3 with the intake jobs).
Forbidden: deciding findings, calling models directly (intake does).
"""

import app.modules.matters.seed as seed

__all__ = ["seed"]
