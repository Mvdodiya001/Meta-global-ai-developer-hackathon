"""Impact domain: amendment consequences and re-verification.

Owns: applying an approved source version (diff → AFFECTS → STALE),
re-verify with fresh-lookup enforcement, and the read-only
counterfactual dry run. Public interface: impact, reverify,
counterfactual; `graph` traversal is shared with evidence.
Forbidden: applying unapproved versions; writing findings directly
(re-verify decides through verification's memory service).
"""

from app.modules.evidence import graph
from app.modules.impact import counterfactual, impact, reverify

__all__ = ["impact", "reverify", "counterfactual", "graph"]
