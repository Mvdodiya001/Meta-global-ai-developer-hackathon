"""T4.1: finding/source graph — edges plus reverse traversal (F10).

`add_edge` is the single writer for graph edges and is idempotent, so
loaders can ensure structural edges on every run. `ensure_card_edges`
binds each rule card to its provision (DERIVED_FROM); the rule-card
loader calls it after ingest. `dependent_findings` walks the reverse
chain provision <- DERIVED_FROM <- rule_card <- DEPENDS_ON <- finding
with a recursive CTE and returns only findings that are still CURRENT,
per DATA_MODEL_API §3.
"""

import uuid
from datetime import UTC, datetime
from typing import Any

import sqlalchemy as sa
from sqlalchemy.orm import Session

from app import models

TRAVERSAL_RELS = ("DERIVED_FROM", "DEPENDS_ON")


def _utcnow() -> str:
    """Current UTC time in ISO-8601 (T4.1)."""
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def _new_id(prefix: str) -> str:
    """One prefixed random id for graph rows (T4.1)."""
    return f"{prefix}-{uuid.uuid4().hex[:12]}"


def is_current_version(session: Session, version_id: str) -> bool:
    """A version is current when no other version supersedes it (T4.3)."""
    clash = session.execute(
        sa.select(models.SourceVersion.id).where(
            models.SourceVersion.supersedes_id == version_id
        )
    ).first()
    return clash is None


def is_current_finding(session: Session, finding_id: str) -> bool:
    """A finding is current with a CURRENT event and no SUPERSEDED one (T4.1).

    Set-based, so same-second `created_at` ties can never misread it.
    """
    states = {
        str(row.state)
        for row in session.execute(
            sa.select(models.FindingEvent).where(
                models.FindingEvent.finding_id == finding_id
            )
        )
        .scalars()
        .all()
    }
    return "CURRENT" in states and "SUPERSEDED" not in states


def add_edge(
    session: Session,
    *,
    src_type: str,
    src_id: str,
    dst_type: str,
    dst_id: str,
    rel: str,
) -> models.Edge:
    """Insert one edge, returning the existing row when present (T4.1)."""
    existing = session.execute(
        sa.select(models.Edge).where(
            models.Edge.src_type == src_type,
            models.Edge.src_id == src_id,
            models.Edge.dst_type == dst_type,
            models.Edge.dst_id == dst_id,
            models.Edge.rel == rel,
        )
    ).scalars().first()
    if existing is not None:
        return existing
    edge = models.Edge(
        id=_new_id("E"),
        src_type=src_type,
        src_id=src_id,
        dst_type=dst_type,
        dst_id=dst_id,
        rel=rel,
        created_at=_utcnow(),
    )
    session.add(edge)
    return edge


def ensure_card_edges(session: Session) -> int:
    """Bind every rule card to its provision; return edges created (T4.1)."""
    created = 0
    for card in session.execute(sa.select(models.RuleCard)).scalars().all():
        before = session.execute(
            sa.select(sa.func.count())
            .select_from(models.Edge)
            .where(
                models.Edge.src_type == "rule_card",
                models.Edge.src_id == card.id,
                models.Edge.dst_type == "provision",
                models.Edge.dst_id == card.provision_id,
                models.Edge.rel == "DERIVED_FROM",
            )
        ).scalar()
        if not before:
            add_edge(
                session,
                src_type="rule_card",
                src_id=str(card.id),
                dst_type="provision",
                dst_id=str(card.provision_id),
                rel="DERIVED_FROM",
            )
            created += 1
    return created


def _upstream_cte(provision_id: str) -> Any:
    """Recursive CTE over reverse edges from one provision (T4.1, F10)."""
    anchor = sa.select(
        sa.literal(provision_id).label("node_id"),
        sa.literal("provision").label("node_type"),
    ).cte(name="upstream", recursive=True)
    edges = models.Edge.__table__
    hop = sa.select(
        edges.c.src_id.label("node_id"), edges.c.src_type.label("node_type")
    ).where(
        edges.c.dst_id == anchor.c.node_id,
        edges.c.dst_type == anchor.c.node_type,
        edges.c.rel.in_(TRAVERSAL_RELS),
    )
    return anchor.union_all(hop)


def dependent_findings(session: Session, provision_id: str) -> list[str]:
    """Finding ids depending on a provision, CURRENT ones only (T4.1)."""
    upstream = _upstream_cte(provision_id)
    candidate_ids = {
        str(row)
        for row in session.execute(
            sa.select(upstream.c.node_id).where(upstream.c.node_type == "finding")
        )
        .scalars()
        .all()
    }
    return sorted(
        finding_id
        for finding_id in candidate_ids
        if is_current_finding(session, finding_id)
    )
