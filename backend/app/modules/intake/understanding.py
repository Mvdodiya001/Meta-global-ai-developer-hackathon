"""Phase 1: contract understanding — parties, obligations, terms, dates.

One gateway call turns document text into structured items; every item is
stored as a *proposed* fact (`ai_inferred`) so nothing here can support an
answer until a lawyer confirms it in the Control room. A deterministic
fallback (parties preamble + `shall` sentences) keeps mock/offline mode
useful and never invents text: every statement is anchored in the document.
"""

import json
import re
import uuid
from datetime import UTC, datetime
from typing import Any

import sqlalchemy as sa
from sqlalchemy.orm import Session

from app import models


def _utcnow() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def _new_id(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:12]}"


def _prompt(text: str) -> dict[str, Any]:
    return {
        "input": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "input_text",
                        "text": (
                            "Extract contract understanding as JSON only: "
                            '{"parties": [{"name": "...", "role": "...", "short": "..."}], '
                            '"obligations": [{"actor": "...", "action": "...", '
                            '"trigger": "...", "clause_ref": "9.2"}], '
                            '"defined_terms": [{"term": "...", "definition": "..."}], '
                            '"key_dates": [{"label": "...", "date": "YYYY-MM-DD"}]}. '
                            "Use only text present in the document.\n\n" + text[:24000]
                        ),
                    }
                ],
            }
        ]
    }


_PARTY_RE = re.compile(
    r"entered into by\s+(.+?)\s+\(\"([^\"]+)\",\s*the\s+([^)]+)\)"
    r"\s+and\s+(.+?)\s+\(\"([^\"]+)\",\s*the\s+([^)]+)\)",
    re.DOTALL,
)
_PARTY_RE_FALLBACK = re.compile(
    r"between\s+([A-Z][\w &]+?(?:Ltd|LLP|Inc|Limited))\s+\(\"([^\"]+)\",\s*the\s+([^)]+)\)"
    r"\s+and\s+([A-Z][\w &]+?(?:Ltd|LLP|Inc|Limited))\s+\(\"([^\"]+)\",\s*the\s+([^)]+)\)",
    re.DOTALL,
)
_REF_RE = re.compile(r"^(\d+(?:\.\d+)?)\s+\S")
_DATE_RE = re.compile(
    r"\b(\d{1,2}\s+(?:January|February|March|April|May|June|July|August|"
    r"September|October|November|December)\s+\d{4}|\d{4}-\d{2}-\d{2})\b"
)


def _fallback(text: str) -> dict[str, list[dict[str, Any]]]:
    """Deterministic extraction for mock/offline mode (Phase 1)."""
    parties: list[dict[str, Any]] = []
    match = _PARTY_RE.search(text) or _PARTY_RE_FALLBACK.search(text)
    if match:
        for name, short, role in (
            (match.group(1), match.group(2), match.group(3)),
            (match.group(4), match.group(5), match.group(6)),
        ):
            parties.append(
                {"name": " ".join(name.split())[:120], "role": role.strip(), "short": short}
            )
    obligations: list[dict[str, Any]] = []
    ref = ""
    for line in text.splitlines():
        ref_match = _REF_RE.match(line.strip())
        if ref_match:
            ref = ref_match.group(1)
        if " shall " in line and len(line.strip()) > 30 and len(obligations) < 16:
            sentence = " ".join(line.split())[:300]
            actor = sentence.split(" shall ")[0].split(". ")[-1][:60]
            obligations.append(
                {"actor": actor, "action": sentence, "trigger": "", "clause_ref": ref}
            )
    terms = [
        {"term": term[:60], "definition": definition.strip()[:240]}
        for term, definition in re.findall(r'"([^"]{3,40})"\s+means\s+([^.]+)\.', text)
    ][:12]
    dates = [
        {"label": "Date in document", "date": found}
        for found in sorted(set(_DATE_RE.findall(text)))
    ][:8]
    return {
        "parties": parties,
        "obligations": obligations,
        "defined_terms": terms,
        "key_dates": dates,
    }


def _parse(text: str, fallback_text: str) -> dict[str, list[dict[str, Any]]]:
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        try:
            data = json.loads(match.group(0))
            out: dict[str, list[dict[str, Any]]] = {}
            for kind in ("parties", "obligations", "defined_terms", "key_dates"):
                rows = data.get(kind, [])
                out[kind] = [row for row in rows if isinstance(row, dict)][:16]
            if any(out.values()):
                return out
        except (ValueError, TypeError):
            pass
    return _fallback(fallback_text)


def extract_understanding(
    text: str, *, mode: str | None = None, session: Session | None = None
) -> dict[str, list[dict[str, Any]]]:
    """Structured understanding of one document text (Phase 1)."""
    from app.agent import llm

    response = llm.call_llm(_prompt(text), mode=mode, session=session, role="understanding")
    return _parse(response.text, text)


def store_understanding(
    session: Session,
    *,
    matter_id: str,
    text: str,
    clause_ids_by_ref: dict[str, str] | None = None,
    mode: str | None = None,
) -> dict[str, int]:
    """Store understanding items as proposed facts; deduped (Phase 1)."""
    data = extract_understanding(text, mode=mode, session=session)
    clause_ids_by_ref = clause_ids_by_ref or {}
    existing = {
        str(row.statement)
        for row in session.execute(
            sa.select(models.Fact).where(models.Fact.matter_id == matter_id)
        ).scalars().all()
    }
    counts = {"parties": 0, "obligations": 0, "defined_terms": 0, "key_dates": 0}
    now = _utcnow()

    def add(kind: str, statement: str, structured: dict[str, Any], clause_ref: str = "") -> None:
        if statement in existing:
            return
        existing.add(statement)
        # Content-derived id: seeded understanding must stay deterministic
        # across databases or the replay-hash gate breaks (Phase 1).
        import hashlib

        fact_id = "F-U" + hashlib.sha256(statement.encode("utf-8")).hexdigest()[:14]
        if session.get(models.Fact, fact_id) is not None:
            return
        session.add(
            models.Fact(
                id=fact_id,
                matter_id=matter_id,
                clause_id=clause_ids_by_ref.get(clause_ref),
                statement=statement[:600],
                structured_json={"kind": kind, **structured},
                origin="extraction",
                trust_class="ai_inferred",
                created_at=now,
            )
        )
        counts[kind] += 1

    for party in data["parties"]:
        name = str(party.get("name", "")).strip()
        if name:
            role = str(party.get("role", "")).strip()
            add("parties", f"Party: {name} ({role})" if role else f"Party: {name}", party)
    for obligation in data["obligations"]:
        action = str(obligation.get("action", "")).strip()
        if action:
            add(
                "obligations",
                action,
                obligation,
                str(obligation.get("clause_ref", "")),
            )
    for term in data["defined_terms"]:
        name = str(term.get("term", "")).strip()
        if name:
            add("defined_terms", f'"{name}" means {term.get("definition", "")}', term)
    for key_date in data["key_dates"]:
        date = str(key_date.get("date", "")).strip()
        if date:
            add("key_dates", f"{key_date.get('label', 'Key date')}: {date}", key_date)
    session.commit()
    return counts
