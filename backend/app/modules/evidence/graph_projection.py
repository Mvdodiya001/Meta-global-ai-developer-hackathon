"""Graph projection to FalkorDB (Rewrite P1).

Postgres/SQLite stays the system of record; this module projects the
evidence graph (findings, facts, legal tests, provisions, versions and
their edges) into FalkorDB as a **rebuildable read model**. Any loss is
recovered by re-running `project`; parity with the record-side
traversal (`app.services.graph.dependent_findings`) is test-enforced.

Connection: `CT_GRAPH_HOST` / `CT_GRAPH_PORT` (default 127.0.0.1:6379),
graph name `CT_GRAPH_NAME` (default `clausetrace`).
"""

import os
from typing import Any

import sqlalchemy as sa
from sqlalchemy.orm import Session

from app import models

DEFAULT_GRAPH = "clausetrace"


def _connect(graph_name: str) -> Any:
    """One FalkorDB graph handle from the environment (P1)."""
    from falkordb import FalkorDB  # type: ignore[import-untyped]  # optional prod dep

    host = os.environ.get("CT_GRAPH_HOST", "127.0.0.1")
    port = int(os.environ.get("CT_GRAPH_PORT", "6379"))
    password = os.environ.get("CT_GRAPH_PASSWORD") or None
    db = FalkorDB(host=host, port=port, password=password)
    return db.select_graph(graph_name)


def graph_name() -> str:
    """Configured projection graph name (P1)."""
    return os.environ.get("CT_GRAPH_NAME", DEFAULT_GRAPH)


def project(session: Session, graph_name_value: str | None = None) -> dict[str, int]:
    """Rebuild the whole projection from the record tables (P1).

    Idempotent by construction: the graph is deleted and recreated
    from current rows, so it can never drift by accumulation.
    """
    name = graph_name_value or graph_name()
    graph = _connect(name)
    try:
        graph.delete()
    except Exception:
        pass  # first run: nothing to delete
    graph = _connect(name)
    edges = session.execute(sa.select(models.Edge)).scalars().all()
    node_ids: dict[str, str] = {}
    for edge in edges:
        node_ids[str(edge.src_id)] = str(edge.src_type)
        node_ids[str(edge.dst_id)] = str(edge.dst_type)
    # Findings/cards on edges are not the only nodes; add edge endpoints
    # only — traversal parity is defined over edges, as in the record.
    for node_id, kind in sorted(node_ids.items()):
        graph.query(
            "CREATE (n:Node {id: $id, kind: $kind})",
            {"id": node_id, "kind": kind},
        )
    for edge in edges:
        graph.query(
            "MATCH (a:Node {id: $src}), (b:Node {id: $dst}) "
            "CREATE (a)-[:EDGE {rel: $rel}]->(b)",
            {"src": str(edge.src_id), "dst": str(edge.dst_id), "rel": str(edge.rel)},
        )
    return {"nodes": len(node_ids), "edges": len(edges)}


def dependent_findings(graph_name_value: str | None, provision_id: str) -> list[str]:
    """CURRENT-free raw traversal in the projection (parity surface).

    Mirrors the shape of `services.graph.dependent_findings` minus the
    CURRENT filter, which stays on the record side: findings that
    depend (through legal tests) on one provision.
    """
    graph = _connect(graph_name_value or graph_name())
    result = graph.query(
        "MATCH (f:Node {kind: 'finding'})-[:EDGE {rel: 'DEPENDS_ON'}]->"
        "(c:Node {kind: 'rule_card'})-[:EDGE {rel: 'DERIVED_FROM'}]->"
        "(p:Node {id: $pid}) RETURN f.id",
        {"pid": provision_id},
    )
    return sorted(str(row[0]) for row in result.result_set)
