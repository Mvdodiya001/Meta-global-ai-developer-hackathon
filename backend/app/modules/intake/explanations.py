"""Phase 4: readability layer — per-clause explanations + document summary.

Every explanation is an AI *suggestion*: stored as a proposed fact
(`ai_inferred`), labelled as such in the UI, and never able to support a
finding until a lawyer confirms it. Tone is enforced, not hoped for:
model output containing advice-like phrasing is replaced field-by-field
with a quote-anchored safe fallback.
"""

import hashlib
import json
import re
from datetime import UTC, datetime
from typing import Any

import sqlalchemy as sa
from sqlalchemy.orm import Session

from app import models

# Advice-like phrasing that must never reach a lawyer-facing explanation.
BANNED_PHRASES = [
    r"you should",
    r"you must",
    r"this is legal",
    r"this is illegal",
    r"is compliant with",
    r"breaches the law",
    r"violates the law",
    r"we recommend",
    r"our advice",
    r"you need to",
]
_BANNED_RE = re.compile("|".join(BANNED_PHRASES), re.IGNORECASE)

SUGGESTION_LABEL = "AI suggestion — may be wrong. This is not legal advice."


def tone_safe(text: str) -> bool:
    """Whether text stays in suggestion tone (Phase 4 guardrail)."""
    return not _BANNED_RE.search(text or "")


def _utcnow() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def _fact_id(statement: str) -> str:
    return "F-E" + hashlib.sha256(statement.encode("utf-8")).hexdigest()[:14]


def _prompt(clause_ref: str, heading: str, text: str) -> dict[str, Any]:
    return {
        "input": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "input_text",
                        "text": (
                            "Explain this contract clause for a reader. Reply with JSON only: "
                            '{"says": "what it says, in plain words", '
                            '"binds": "who it binds", "triggers": "what triggers it", '
                            '"check": "what a lawyer may want to check"}. '
                            "Use suggestion language (appears to, suggests). Never give advice, "
                            "never say what anyone should do, never call anything\n"
                            "legal or illegal.\n\n"
                            f"Clause {clause_ref} {heading}:\n{text}"
                        ),
                    }
                ],
            }
        ]
    }


def _fallback(ref: str, text: str) -> dict[str, str]:
    """Quote-anchored deterministic explanation (mock/offline mode)."""
    first = " ".join(text.split())[:280]
    return {
        "says": f"This clause appears to say: {first}",
        "binds": "The parties named in this clause, as quoted.",
        "triggers": "The conditions stated in the quoted text.",
        "check": "A lawyer may want to check this wording against the cited law.",
    }


def _parse(text: str, ref: str, clause_text: str) -> dict[str, str]:
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        try:
            data = json.loads(match.group(0))
            out = {
                key: str(data.get(key, ""))[:500] for key in ("says", "binds", "triggers", "check")
            }
            if out["says"]:
                fallback = _fallback(ref, clause_text)
                return {
                    key: value if tone_safe(value) else fallback[key] for key, value in out.items()
                }
        except (ValueError, TypeError):
            pass
    return _fallback(ref, clause_text)


def explain_clause(
    ref: str, heading: str, text: str, *, mode: str | None = None, session: Session | None = None
) -> dict[str, str]:
    """One tone-guarded explanation for a clause (Phase 4)."""
    from app.agent import llm

    response = llm.call_llm(_prompt(ref, heading, text), mode=mode, session=session, role="explain")
    return _parse(response.text, ref, text)


def store_explanations(
    session: Session,
    *,
    matter_id: str,
    document_id: str,
    mode: str | None = None,
) -> int:
    """Explain every clause of the latest version; deduped (Phase 4)."""
    version = (
        session.execute(
            sa.select(models.DocumentVersion)
            .where(models.DocumentVersion.document_id == document_id)
            .order_by(models.DocumentVersion.created_at.desc(), models.DocumentVersion.id.desc())
        )
        .scalars()
        .first()
    )
    if version is None:
        return 0
    clauses = (
        session.execute(
            sa.select(models.Clause)
            .where(models.Clause.document_version_id == version.id)
            .order_by(models.Clause.id)
        )
        .scalars()
        .all()
    )
    all_facts = (
        session.execute(sa.select(models.Fact).where(models.Fact.matter_id == matter_id))
        .scalars()
        .all()
    )
    existing = {str(row.statement) for row in all_facts}
    # One live explanation per clause: re-generating must not pile up
    # near-duplicate drafts when the model rewords its answer.
    explained_clause_ids = {
        str(row.clause_id)
        for row in all_facts
        if (row.structured_json or {}).get("kind") == "explanation" and row.clause_id is not None
    }
    clauses = [clause for clause in clauses if str(clause.id) not in explained_clause_ids]
    now = _utcnow()
    created = 0
    # Draft explanations concurrently (gateway calls are network-bound);
    # sessions are not thread-safe, so workers run session-less and only
    # the storage below touches the database.
    from concurrent.futures import ThreadPoolExecutor

    def _draft(clause: models.Clause) -> dict[str, str]:
        return explain_clause(
            str(clause.ref), str(clause.heading), str(clause.text), mode=mode, session=None
        )

    with ThreadPoolExecutor(max_workers=4) as pool:
        drafted = list(pool.map(_draft, clauses))
    for clause, explanation in zip(clauses, drafted, strict=True):
        statement = f"Clause {clause.ref}: {explanation['says']}"[:600]
        if statement in existing:
            continue
        existing.add(statement)
        fact_id = _fact_id(statement + str(clause.id))
        if session.get(models.Fact, fact_id) is not None:
            continue
        session.add(
            models.Fact(
                id=fact_id,
                matter_id=matter_id,
                clause_id=str(clause.id),
                statement=statement,
                structured_json={
                    "kind": "explanation",
                    "clause_ref": str(clause.ref),
                    **explanation,
                },
                origin="extraction",
                trust_class="ai_inferred",
                created_at=now,
            )
        )
        created += 1
    session.commit()
    return created


def store_summary(
    session: Session,
    *,
    matter_id: str,
    document_id: str,
    mode: str | None = None,
) -> models.Fact:
    """One suggestion-labelled executive summary fact (Phase 4)."""
    from app.agent import llm

    version = (
        session.execute(
            sa.select(models.DocumentVersion)
            .where(models.DocumentVersion.document_id == document_id)
            .order_by(models.DocumentVersion.created_at.desc(), models.DocumentVersion.id.desc())
        )
        .scalars()
        .first()
    )
    text = str(version.text) if version is not None else ""
    prompt = {
        "input": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "input_text",
                        "text": (
                            "Summarise this contract in plain words for a busy reader: parties, "
                            "purpose, the main obligations, and key risks to check. Suggestion "
                            "language only (appears to, suggests). Never give advice.\n\n"
                            + text[:20000]
                        ),
                    }
                ],
            }
        ]
    }
    response = llm.call_llm(prompt, mode=mode, session=session, role="summary")
    summary = (
        response.text.strip()[:1600]
        or (
            "This document appears to be a contract. "
            "A lawyer may want to summarise it after reading."
        )
    )
    if not tone_safe(summary):
        summary = (
            "This document appears to set out an agreement between the named parties. "
            "A lawyer may want to check its obligations against the cited law."
        )
    statement = f"Document summary: {summary}"[:1600]
    fact_id = _fact_id(statement + document_id)
    existing = session.get(models.Fact, fact_id)
    if existing is not None:
        session.expunge(existing)
        return existing
    fact = models.Fact(
        id=fact_id,
        matter_id=matter_id,
        clause_id=None,
        statement=statement,
        structured_json={"kind": "summary"},
        origin="extraction",
        trust_class="ai_inferred",
        created_at=_utcnow(),
    )
    session.add(fact)
    session.commit()
    session.refresh(fact)
    session.expunge(fact)
    return fact
