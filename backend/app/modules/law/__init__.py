"""Law domain: sources, versions, provisions, legal tests (rule cards).

Owns: the legal corpus lifecycle — snapshot ingest with content hashes,
verbatim-span card loading, version diff and as-of applicability.
Public interface: sources, rulecards, diff.
Forbidden: marking findings stale (impact does, on approved versions),
deciding findings.
"""

from app.modules.law import diff, rulecards, sources

__all__ = ["sources", "rulecards", "diff"]
