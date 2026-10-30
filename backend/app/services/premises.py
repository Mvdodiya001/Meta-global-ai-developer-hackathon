"""T4.4: premise challenge/approve/reject — Flow C (F8, F15).

A trust-class change is always a new fact row superseding the old one;
old rows (and the findings tied to them) are never modified. Challenge
and reject mark the new row `disputed` and STALE every CURRENT finding
that depends on the old row, so re-verify recomputes them. Approval
confirms the premise (`lawyer_confirmed`) and leaves dependents alone.
Every action writes a review row and an audit row.
"""

import uuid
from datetime import UTC, datetime

import sqlalchemy as sa
from sqlalchemy.orm import Session

from app import models
from app.core.errors import MemoryServiceError
from app.services.graph import is_current_finding


def _utcnow() -> str:
    """Current UTC time in ISO-8601 (T4.4)."""
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def _new_id(prefix: str) -> str:
    """One prefixed random id for premise rows (T4.4)."""
    return f"{prefix}-{uuid.uuid4().hex[:12]}"


def _current_fact(session: Session, fact_id: str) -> models.Fact:
    """Fetch a fact that no newer row supersedes (T4.4)."""
    fact = session.get(models.Fact, fact_id)
    if fact is None:
        raise MemoryServiceError(f"unknown fact {fact_id!r}")
    newer = session.execute(
        sa.select(models.Fact.id).where(models.Fact.supersedes_id == fact_id)
    ).first()
    if newer is not None:
        raise MemoryServiceError(
            f"fact {fact_id!r} is superseded by {newer[0]!r}"
        )
    return fact


def _copy_fact(
    session: Session,
    old: models.Fact,
    *,
    trust_class: str,
    reviewer: str,
    approved: bool,
) -> models.Fact:
    """Insert the new trust-class row for one fact (T4.4)."""
    now = _utcnow()
    new = models.Fact(
        id=_new_id("F"),
        matter_id=old.matter_id,
        clause_id=old.clause_id,
        statement=old.statement,
        structured_json=old.structured_json,
        origin=old.origin,
        trust_class=trust_class,
        created_at=now,
        approved_by=reviewer if approved else None,
        approved_at=now if approved else None,
        supersedes_id=old.id,
    )
    session.add(new)
    return new


def _record_action(
    session: Session,
    old: models.Fact,
    new: models.Fact,
    *,
    action: str,
    reason: str,
    reviewer: str,
) -> None:
    """Review plus audit rows for a premise action (T4.4)."""
    session.add(
        models.Review(
            id=_new_id("RV"),
            item_type="fact",
            item_id=str(old.id),
            reason=reason,
            status=action,
            reviewer=reviewer,
            note=str(new.id),
            created_at=_utcnow(),
        )
    )
    session.add(
        models.AuditLog(
            id=_new_id("A"),
            ts=_utcnow(),
            actor_type="lawyer",
            actor_id=reviewer,
            event=f"fact.{action}",
            object_type="fact",
            object_id=str(new.id),
            details_json={"old_fact_id": str(old.id), "reason": reason},
        )
    )


def _stale_dependents(session: Session, old: models.Fact, new: models.Fact) -> None:
    """STALE every CURRENT finding depending on the old row (T4.4)."""
    edges = session.execute(
        sa.select(models.Edge).where(
            models.Edge.rel == "DEPENDS_ON",
            models.Edge.dst_type == "fact",
            models.Edge.dst_id == old.id,
            models.Edge.src_type == "finding",
        )
    ).scalars().all()
    for edge in edges:
        if is_current_finding(session, str(edge.src_id)):
            session.add(
                models.FindingEvent(
                    id=_new_id("FE"),
                    finding_id=str(edge.src_id),
                    state="STALE",
                    reason=f"premise {old.id} superseded by {new.id}",
                    caused_by_type="fact",
                    caused_by_id=str(new.id),
                    created_at=_utcnow(),
                )
            )


def challenge_fact(
    session: Session, *, fact_id: str, reason: str, reviewer: str = "lawyer"
) -> models.Fact:
    """Dispute a fact and stale its dependents (T4.4)."""
    if not reason.strip():
        raise MemoryServiceError("challenge needs a reason")
    old = _current_fact(session, fact_id)
    new = _copy_fact(
        session, old, trust_class="disputed", reviewer=reviewer, approved=False
    )
    _record_action(
        session, old, new, action="challenged", reason=reason, reviewer=reviewer
    )
    _stale_dependents(session, old, new)
    session.commit()
    return new


def reject_fact(
    session: Session, *, fact_id: str, reason: str, reviewer: str = "lawyer"
) -> models.Fact:
    """Reject a fact and stale its dependents (T4.4)."""
    if not reason.strip():
        raise MemoryServiceError("rejection needs a reason")
    old = _current_fact(session, fact_id)
    new = _copy_fact(
        session, old, trust_class="disputed", reviewer=reviewer, approved=False
    )
    _record_action(
        session, old, new, action="rejected", reason=reason, reviewer=reviewer
    )
    _stale_dependents(session, old, new)
    session.commit()
    return new


def approve_fact(
    session: Session, *, fact_id: str, reviewer: str = "lawyer"
) -> models.Fact:
    """Confirm a fact; dependents stay valid (T4.4)."""
    old = _current_fact(session, fact_id)
    new = _copy_fact(
        session, old, trust_class="lawyer_confirmed", reviewer=reviewer, approved=True
    )
    _record_action(
        session, old, new, action="approved", reason="", reviewer=reviewer
    )
    session.commit()
    return new
