"""T4.3: re-verify stale findings with re-query enforcement (F12).

`reverify_finding` replaces one stale finding: the finding must carry a
STALE event and no SUPERSEDED one, and the run's tool log must show a
fresh `lookup_source` of the STALE-causing version while it is still
current — otherwise the re-verify is rejected with no writes at all
(AGENTS.md invariant 7). The new decision itself comes from
`memory.decide_finding`, so the old row is kept, the new row supersedes
it, and an equal outcome adds a `finding.rechecked` audit row.
"""

import uuid
from datetime import UTC, datetime
from typing import Any

import sqlalchemy as sa
from sqlalchemy.orm import Session

from app import models
from app.core.errors import MemoryServiceError
from app.services import graph, memory


def _utcnow() -> str:
    """Current UTC time in ISO-8601 (T4.3)."""
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def _new_id(prefix: str) -> str:
    """One prefixed random id for reverify rows (T4.3)."""
    return f"{prefix}-{uuid.uuid4().hex[:12]}"


def _stale_events(session: Session, finding_id: str) -> list[models.FindingEvent]:
    """STALE events for one finding, latest first (T4.3)."""
    return list(
        session.execute(
            sa.select(models.FindingEvent)
            .where(
                models.FindingEvent.finding_id == finding_id,
                models.FindingEvent.state == "STALE",
            )
            .order_by(
                models.FindingEvent.created_at.desc(), models.FindingEvent.id.desc()
            )
        )
        .scalars()
        .all()
    )


def _has_superseded(session: Session, finding_id: str) -> bool:
    """Whether a SUPERSEDED event already exists (T4.3)."""
    return (
        session.execute(
            sa.select(models.FindingEvent.id).where(
                models.FindingEvent.finding_id == finding_id,
                models.FindingEvent.state == "SUPERSEDED",
            )
        ).first()
        is not None
    )


def _fresh_lookup_of(session: Session, run_id: str, version_id: str) -> bool:
    """The run fetched exactly this version and it is still current (T4.3)."""
    rows = session.execute(
        sa.select(models.ToolCall).where(
            models.ToolCall.run_id == run_id,
            models.ToolCall.tool == "lookup_source",
            models.ToolCall.ok.is_(True),
        )
    ).scalars().all()
    for row in rows:
        result = row.result_json
        if (
            isinstance(result, dict)
            and result.get("source_version_id") == version_id
            and graph.is_current_version(session, version_id)
        ):
            return True
    return False


def reverify_finding(
    session: Session,
    *,
    finding_id: str,
    proof: dict[str, Any],
    run_id: str,
    challenger_blocking: bool = False,
    challenger_note: bool = False,
) -> models.Finding:
    """Replace a stale finding with a freshly decided one (T4.3, F12)."""
    old = session.get(models.Finding, finding_id)
    if old is None:
        raise MemoryServiceError(f"unknown finding {finding_id!r}")
    stale = _stale_events(session, finding_id)
    if not stale:
        raise MemoryServiceError(f"finding {finding_id!r} is not stale")
    if _has_superseded(session, finding_id):
        raise MemoryServiceError(f"finding {finding_id!r} is already superseded")
    cause = stale[0]
    if cause.caused_by_type != "source_version" or not isinstance(
        cause.caused_by_id, str
    ):
        raise MemoryServiceError(f"finding {finding_id!r} has no version cause")
    if not _fresh_lookup_of(session, run_id, cause.caused_by_id):
        raise MemoryServiceError(
            f"rejected: no fresh lookup of {cause.caused_by_id} in run {run_id!r}"
        )
    new = memory.decide_finding(
        session,
        claim_id=str(old.claim_id),
        proof=proof,
        run_id=run_id,
        challenger_blocking=challenger_blocking,
        challenger_note=challenger_note,
    )
    if new.status == old.status:
        session.add(
            models.AuditLog(
                id=_new_id("A"),
                ts=_utcnow(),
                actor_type="system",
                actor_id="reverify",
                event="finding.rechecked",
                object_type="finding",
                object_id=str(new.id),
                details_json={
                    "old_finding_id": str(old.id),
                    "status": str(new.status),
                    "unchanged": True,
                },
            )
        )
        session.commit()
    return new
