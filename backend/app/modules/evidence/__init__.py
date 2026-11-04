"""Evidence domain: facts, trust actions, graph reads, audit.

Owns: premise lifecycle (propose → approve/challenge → supersede),
dependent traversal for display, and the audit trail surface.
Public interface: premises (trust actions), graph (read traversal),
graph_projection (FalkorDB rebuildable read model).
Forbidden: deciding finding status (verification does); mutating any
existing fact row (supersession only).
"""

from app.modules.evidence import graph, graph_projection, premises

__all__ = ["premises", "graph", "graph_projection"]
