"""T1.5: version diff by provision key + hash, and as-of applicability (F11).

`diff_versions` compares two snapshots of one source the way the amendment
flow needs (DATA_MODEL_API §6 step 2): same key + same `text_sha256` means
unchanged; a hash or effective-date change flags the key; missing keys are
added/removed. `in_force` answers whether a provision applies on a plain
`as_of` date: `effective_from <= as_of < effective_until or open end`.
"""

from dataclasses import dataclass, field
from typing import Any

from sqlalchemy.orm import Session

from app import models
from app.services import sources


@dataclass(frozen=True)
class VersionDiff:
    """Added/removed/changed/unchanged provision keys between two versions (T1.5)."""

    old_version_id: str
    new_version_id: str
    changed_keys: list[str] = field(default_factory=list)
    added_keys: list[str] = field(default_factory=list)
    removed_keys: list[str] = field(default_factory=list)
    unchanged_keys: list[str] = field(default_factory=list)


def _fingerprint(row: models.Provision) -> Any:
    """Hash plus effective dates: what counts as 'the same provision' (T1.5)."""
    return (row.text_sha256, row.effective_from, row.effective_until)


def diff_versions(session: Session, old_id: str, new_id: str) -> VersionDiff:
    """Diff two versions of one source by provision key (T1.5, F11)."""
    old_rows = {row.key: row for row in sources.list_provisions(session, old_id)}
    new_rows = {row.key: row for row in sources.list_provisions(session, new_id)}
    changed = sorted(
        key
        for key in old_rows
        if key in new_rows and _fingerprint(old_rows[key]) != _fingerprint(new_rows[key])
    )
    added = sorted(key for key in new_rows if key not in old_rows)
    removed = sorted(key for key in old_rows if key not in new_rows)
    unchanged = sorted(
        key
        for key in old_rows
        if key in new_rows and _fingerprint(old_rows[key]) == _fingerprint(new_rows[key])
    )
    return VersionDiff(
        old_version_id=old_id,
        new_version_id=new_id,
        changed_keys=changed,
        added_keys=added,
        removed_keys=removed,
        unchanged_keys=unchanged,
    )


def in_force(provision: models.Provision, as_of: str) -> bool:
    """Whether a provision applies on a plain `as_of` date (T1.5)."""
    day = as_of[:10]
    if day < provision.effective_from:
        return False
    if provision.effective_until is not None and day >= provision.effective_until:
        return False
    return True
