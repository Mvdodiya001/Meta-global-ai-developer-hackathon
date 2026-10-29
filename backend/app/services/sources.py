"""T1.2: hashed source snapshots + provision loading (F1, F2).

Cleaned provision texts live in `corpus/raw/` (human-verified in T0.6 via
`corpus/NOTES.md`); `manifest.json` binds each file to a source version with
provision keys and effective dates. Ingest is idempotent: identical content
for a source returns the existing version instead of inserting a new row
(DATA_MODEL_API §8). Simulated versions carry `is_simulated=true` (rule 8).
"""

import hashlib
import json
from pathlib import Path
from typing import Any

import sqlalchemy as sa
from sqlalchemy.orm import Session

from app import models
from app.core.errors import SourceUnavailable  # noqa: F401  (re-exported for callers)

DEFAULT_RAW_DIR = Path(__file__).resolve().parents[3] / "corpus" / "raw"


def sha256_text(text: str) -> str:
    """Stable hex digest of snapshot text (T1.2)."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def load_manifest(raw_dir: str | Path = DEFAULT_RAW_DIR) -> dict[str, Any]:
    """Read the corpus manifest binding files to versions (T1.2)."""
    manifest_path = Path(raw_dir) / "manifest.json"
    content: dict[str, Any] = json.loads(manifest_path.read_text(encoding="utf-8"))
    return content


def ensure_source(session: Session, spec: dict[str, Any]) -> None:
    """Insert a source row when its id is not yet registered (T1.2)."""
    exists = session.get(models.Source, spec["id"])
    if exists is None:
        session.add(
            models.Source(
                id=spec["id"],
                key=spec["key"],
                title=spec["title"],
                publisher=spec["publisher"],
                url=spec["url"],
                jurisdiction=spec["jurisdiction"],
            )
        )


def ingest_version(
    session: Session, spec: dict[str, Any], texts: dict[str, str]
) -> str:
    """Store one hashed version plus provisions; identical content is a no-op (T1.2)."""
    if session.get(models.Source, spec["source_id"]) is None:
        raise SourceUnavailable(f"unknown source: {spec['source_id']}")
    raw_text = "\n\n".join(texts[item["file"]] for item in spec["provisions"])
    digest = sha256_text(raw_text)
    existing = session.execute(
        sa.select(models.SourceVersion).where(
            models.SourceVersion.source_id == spec["source_id"],
            models.SourceVersion.content_sha256 == digest,
        )
    ).scalar_one_or_none()
    if existing is not None:
        return str(existing.id)
    session.add(
        models.SourceVersion(
            id=spec["id"],
            source_id=spec["source_id"],
            version_label=spec["version_label"],
            published_on=spec["published_on"],
            effective_from=min(
                item["effective_from"] for item in spec["provisions"]
            ),
            effective_until=None,
            retrieved_at=spec["retrieved_at"],
            content_sha256=digest,
            raw_text=raw_text,
            is_simulated=bool(spec["is_simulated"]),
            supersedes_id=spec["supersedes_id"],
        )
    )
    for item in spec["provisions"]:
        text = texts[item["file"]]
        session.add(
            models.Provision(
                id=item["id"],
                source_version_id=spec["id"],
                key=item["key"],
                text=text,
                text_sha256=sha256_text(text),
                effective_from=item["effective_from"],
                effective_until=item["effective_until"],
            )
        )
    session.commit()
    return str(spec["id"])


def load_corpus(
    session: Session, raw_dir: str | Path = DEFAULT_RAW_DIR
) -> dict[str, str]:
    """Ingest every manifest version; return version ids by manifest id (T1.2)."""
    manifest = load_manifest(raw_dir)
    files = {
        item["file"]
        for version in manifest["versions"]
        for item in version["provisions"]
    }
    texts = {
        name: (Path(raw_dir) / name).read_text(encoding="utf-8") for name in files
    }
    for spec in manifest["sources"]:
        ensure_source(session, spec)
    session.commit()
    return {
        version["id"]: ingest_version(session, version, texts)
        for version in manifest["versions"]
    }


def get_version(session: Session, version_id: str) -> models.SourceVersion:
    """Fetch one version row or raise a typed error (T1.2)."""
    version = session.get(models.SourceVersion, version_id)
    if version is None:
        raise SourceUnavailable(f"unknown source version: {version_id}")
    return version


def list_provisions(session: Session, version_id: str) -> list[models.Provision]:
    """List a version's provisions in id order (T1.2)."""
    get_version(session, version_id)
    return list(
        session.execute(
            sa.select(models.Provision)
            .where(models.Provision.source_version_id == version_id)
            .order_by(models.Provision.id)
        )
        .scalars()
        .all()
    )
