"""T4.2: impact engine — amendment diff, AFFECTS, STALE, report (F11, F12).

`diff_provisions` is pure: keys present in both versions compare by
content hash plus effective dates; the rest are added/removed.
`apply_version` runs the DATA_MODEL_API §6 steps for one new version:
diff against the superseded version, AFFECTS edges from the provision
row carrying the key (the new row when the key survives, else the old
one), STALE events for CURRENT dependents with the new version as the
cause, one audit row, and the impact report. Re-applying is a no-op
for edges and STALE events.
"""

import uuid
from datetime import UTC, datetime
from typing import Any

import sqlalchemy as sa
from sqlalchemy.orm import Session

from app import models
from app.core.errors import SourceUnavailable
from app.services import graph

SNAPSHOT_KEYS = ("key", "sha", "from", "until")


def _utcnow() -> str:
    """Current UTC time in ISO-8601 (T4.2)."""
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def _new_id(prefix: str) -> str:
    """One prefixed random id for impact rows (T4.2)."""
    return f"{prefix}-{uuid.uuid4().hex[:12]}"


def diff_provisions(
    old: list[dict[str, Any]], new: list[dict[str, Any]]
) -> dict[str, list[str]]:
    """Diff provision snapshots by key, hash and effective dates (T4.2)."""
    old_by_key = {str(item["key"]): item for item in old}
    new_by_key = {str(item["key"]): item for item in new}
    changed = sorted(
        key
        for key in old_by_key
        if key in new_by_key
        and any(old_by_key[key].get(field) != new_by_key[key].get(field)
                for field in ("sha", "from", "until"))
    )
    return {
        "changed": changed,
        "added": sorted(key for key in new_by_key if key not in old_by_key),
        "removed": sorted(key for key in old_by_key if key not in new_by_key),
    }


def snapshot(row: models.Provision) -> dict[str, Any]:
    """Row snapshot for the pure diff (T4.2)."""
    return {
        "key": str(row.key),
        "sha": str(row.text_sha256),
        "from": str(row.effective_from),
        "until": row.effective_until,
    }


def version_provisions(session: Session, version_id: str) -> list[models.Provision]:
    """One version's provisions in id order (T4.2)."""
    return list(
        session.execute(
            sa.select(models.Provision)
            .where(models.Provision.source_version_id == version_id)
            .order_by(models.Provision.id)
        )
        .scalars()
        .all()
    )


def _already_stale(session: Session, finding_id: str, version_id: str) -> bool:
    """A STALE event from this version already exists (T4.2)."""
    return (
        session.execute(
            sa.select(models.FindingEvent.id).where(
                models.FindingEvent.finding_id == finding_id,
                models.FindingEvent.state == "STALE",
                models.FindingEvent.caused_by_type == "source_version",
                models.FindingEvent.caused_by_id == version_id,
            )
        ).first()
        is not None
    )


def apply_version(session: Session, new_version_id: str) -> dict[str, Any]:
    """Apply one new source version and report its impact (T4.2, F11, F12)."""
    version = session.get(models.SourceVersion, new_version_id)
    if version is None:
        raise SourceUnavailable(f"unknown source version: {new_version_id}")
    report: dict[str, Any] = {
        "source_id": str(version.source_id),
        "old_version_id": version.supersedes_id,
        "new_version_id": str(version.id),
        "changed": [],
        "added": [],
        "removed": [],
        "affected_rule_cards": [],
        "stale_findings": [],
    }
    if version.supersedes_id is None:
        return report
    old_rows = version_provisions(session, str(version.supersedes_id))
    new_rows = version_provisions(session, str(version.id))
    diff = diff_provisions(
        [snapshot(row) for row in old_rows], [snapshot(row) for row in new_rows]
    )
    report.update(diff)
    new_by_key = {str(row.key): row for row in new_rows}
    keyed_rows: dict[str, list[models.Provision]] = {}
    for row in session.execute(
        sa.select(models.Provision)
        .join(
            models.SourceVersion,
            models.Provision.source_version_id == models.SourceVersion.id,
        )
        .where(models.SourceVersion.source_id == version.source_id)
    ).scalars().all():
        keyed_rows.setdefault(str(row.key), []).append(row)
    affected: set[str] = set()
    stale_for_key: dict[str, str] = {}
    for key in diff["changed"] + diff["removed"]:
        src_row = new_by_key.get(key) or keyed_rows[key][0]
        for row in keyed_rows.get(key, []):
            cards = session.execute(
                sa.select(models.RuleCard).where(
                    models.RuleCard.provision_id == row.id
                )
            ).scalars().all()
            for card in cards:
                graph.add_edge(
                    session,
                    src_type="provision",
                    src_id=str(src_row.id),
                    dst_type="rule_card",
                    dst_id=str(card.id),
                    rel="AFFECTS",
                )
                affected.add(str(card.id))
            for finding_id in graph.dependent_findings(session, str(row.id)):
                stale_for_key.setdefault(finding_id, key)
    for finding_id in sorted(stale_for_key):
        if not _already_stale(session, finding_id, str(version.id)):
            key = stale_for_key[finding_id]
            verb = "changed" if key in diff["changed"] else "removed"
            session.add(
                models.FindingEvent(
                    id=_new_id("FE"),
                    finding_id=finding_id,
                    state="STALE",
                    reason=f"provision '{key}' {verb} in {version.id}",
                    caused_by_type="source_version",
                    caused_by_id=str(version.id),
                    created_at=_utcnow(),
                )
            )
        report["stale_findings"].append(finding_id)
    report["affected_rule_cards"] = sorted(affected)
    session.add(
        models.AuditLog(
            id=_new_id("A"),
            ts=_utcnow(),
            actor_type="system",
            actor_id="impact-engine",
            event="impact.applied",
            object_type="source_version",
            object_id=str(version.id),
            details_json={
                "changed": report["changed"],
                "added": report["added"],
                "removed": report["removed"],
                "stale_findings": report["stale_findings"],
            },
        )
    )
    session.commit()
    return report
