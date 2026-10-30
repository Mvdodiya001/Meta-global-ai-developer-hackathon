"""T3.3: memory service — the only place that sets a finding's status (F7).

`decide_finding` follows DATA_MODEL_API §5: unsupported types and missing
rule cards yield UNKNOWN; otherwise the deterministic checker verdict, a
fresh-lookup re-query check over the run's tool log, and the challenger
flags decide between FOLLOWS, RULED_OUT and REQUIRES_REVIEW. The confidence
band is computed from stored evidence classes per ARCHITECTURE §6, never
from model output — a `status` key smuggled into the proof is ignored.
Every decision writes a finding row, a CURRENT event (superseding prior
CURRENT findings of the claim), DEPENDS_ON edges and an audit row.
"""

import os
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import sqlalchemy as sa
from sqlalchemy.orm import Session

from app import models
from app.agent import challenger as challenger_agent
from app.agent import llm
from app.core.errors import MemoryServiceError
from app.services.graph import is_current_finding, is_current_version
from checker import verify as checker

SUPPORTED_TYPES = frozenset({"CT1", "CT2", "CT3", "CT4"})

CONCLUSION_HOLDS = "holds"
CONCLUSION_FAILS = "does not hold"

STATUSES = ("FOLLOWS", "RULED_OUT", "UNKNOWN", "REQUIRES_REVIEW")


def _utcnow() -> str:
    """Current UTC time in ISO-8601 (T3.3)."""
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def _new_id(prefix: str) -> str:
    """One prefixed random id for memory-created rows (T3.3)."""
    return f"{prefix}-{uuid.uuid4().hex[:12]}"


def _in_force_on(provision: models.Provision, as_of: str) -> bool:
    """Plain-date applicability, same convention as the checker (T3.3)."""
    if as_of < str(provision.effective_from):
        return False
    until = provision.effective_until
    return until is None or as_of < str(until)


def _fresh_lookups(session: Session, run_id: str) -> set[str]:
    """Source versions this run fetched via a successful lookup (T3.3)."""
    rows = session.execute(
        sa.select(models.ToolCall).where(
            models.ToolCall.run_id == run_id,
            models.ToolCall.tool == "lookup_source",
            models.ToolCall.ok.is_(True),
        )
    ).scalars().all()
    found: set[str] = set()
    for row in rows:
        result = row.result_json
        if isinstance(result, dict):
            version_id = result.get("source_version_id")
            if isinstance(version_id, str):
                found.add(version_id)
    return found


def _tool_log_ok(session: Session, run_id: str, cited: list[str]) -> bool:
    """Every cited version needs a fresh lookup of a current version (T3.3)."""
    if not cited:
        return True
    logged = _fresh_lookups(session, run_id)
    return all(
        version_id in logged and is_current_version(session, version_id)
        for version_id in cited
    )


def _proof_facts(
    session: Session, matter_id: str, proof: dict[str, Any]
) -> dict[str, models.Fact]:
    """Premise fact rows for a proof, scoped to the claim's matter (T3.3)."""
    entries = proof.get("premises", [])
    if not isinstance(entries, list):
        raise MemoryServiceError("proof premises must be a list")
    facts: dict[str, models.Fact] = {}
    for entry in entries:
        fact_id = entry.get("fact_id") if isinstance(entry, dict) else None
        if not isinstance(fact_id, str):
            continue
        fact = session.get(models.Fact, fact_id)
        if fact is not None and fact.matter_id == matter_id:
            facts[str(fact.id)] = fact
    return facts


def _cited_cards(session: Session, proof: dict[str, Any]) -> dict[str, models.RuleCard]:
    """Rule card rows cited by cite_rule steps (T3.3)."""
    cards: dict[str, models.RuleCard] = {}
    for step in proof.get("steps", []):
        if not isinstance(step, dict) or step.get("kind") != "cite_rule":
            continue
        card_id = step.get("rule_card_id")
        if not isinstance(card_id, str):
            continue
        card = session.get(models.RuleCard, card_id)
        if card is not None:
            cards[str(card.id)] = card
    return cards


def _cited_provisions(
    session: Session, proof: dict[str, Any]
) -> dict[str, models.Provision]:
    """Provision rows cited by citations and in_force steps (T3.3)."""
    ids: set[str] = set()
    for step in proof.get("steps", []):
        if not isinstance(step, dict):
            continue
        if step.get("kind") == "in_force":
            provision_id = step.get("provision_id")
            if isinstance(provision_id, str):
                ids.add(provision_id)
        elif step.get("kind") == "cite_rule":
            citation = step.get("citation")
            if isinstance(citation, dict):
                provision_id = citation.get("provision_id")
                if isinstance(provision_id, str):
                    ids.add(provision_id)
    rows: dict[str, models.Provision] = {}
    for provision_id in ids:
        provision = session.get(models.Provision, provision_id)
        if provision is not None:
            rows[str(provision.id)] = provision
    return rows


def _checker_stores(session: Session) -> dict[str, dict[str, Any]]:
    """Premise/provision/card/version/clause stores from the database (T3.3)."""
    provisions = {
        str(row.id): {
            "source_version_id": str(row.source_version_id),
            "key": str(row.key),
            "text": str(row.text),
            "text_sha256": str(row.text_sha256),
            "effective_from": str(row.effective_from),
            "effective_until": row.effective_until,
        }
        for row in session.execute(sa.select(models.Provision)).scalars().all()
    }
    rule_cards = {
        str(row.id): {
            "provision_id": str(row.provision_id),
            "claim_type": str(row.claim_type),
        }
        for row in session.execute(sa.select(models.RuleCard)).scalars().all()
    }
    versions = {
        str(row.id): {"supersedes_id": row.supersedes_id}
        for row in session.execute(sa.select(models.SourceVersion)).scalars().all()
    }
    clauses = {
        str(row.id): str(row.text)
        for row in session.execute(sa.select(models.Clause)).scalars().all()
    }
    return {
        "provisions": provisions,
        "rule_cards": rule_cards,
        "versions": versions,
        "clauses": clauses,
    }


def _confidence_band(
    as_of: str,
    facts: dict[str, models.Fact],
    cards: dict[str, models.RuleCard],
    provisions: dict[str, models.Provision],
    versions: dict[str, models.SourceVersion],
    challenger_note: bool,
) -> str:
    """Band from stored evidence classes per ARCHITECTURE §6 (T3.3)."""
    if challenger_note:
        return "low"
    if any(card.kind == "interpretation" for card in cards.values()):
        return "low"
    if any(version.is_simulated for version in versions.values()):
        return "low"
    if all(fact.trust_class == "lawyer_confirmed" for fact in facts.values()) and all(
        _in_force_on(provision, as_of) for provision in provisions.values()
    ):
        return "high"
    return "medium"


def _cited_versions(
    session: Session, cited_ids: list[str]
) -> dict[str, models.SourceVersion]:
    """Source version rows behind the checker's cited list (T3.3)."""
    rows: dict[str, models.SourceVersion] = {}
    for version_id in cited_ids:
        version = session.get(models.SourceVersion, version_id)
        if version is not None:
            rows[str(version.id)] = version
    return rows


def _store_decision(
    session: Session,
    claim: models.Claim,
    proof: dict[str, Any],
    status: str,
    band: str,
    report: dict[str, Any] | None,
    run_id: str,
    fact_ids: list[str],
    card_ids: list[str],
    challenge: challenger_agent.ChallengerReport | None = None,
) -> models.Finding:
    """Write finding, event, edges and audit rows for a decision (T3.3).

    A run challenger pass is stored as one append-only `challenger_reports`
    row so the finding payload can echo it (ask-frontend).
    """
    prior = list(
        session.execute(
            sa.select(models.Finding)
            .where(models.Finding.claim_id == claim.id)
            .order_by(models.Finding.version_no)
        )
        .scalars()
        .all()
    )
    finding_id = _new_id("FND")
    cited = list(report.get("cited_source_versions", [])) if report else []
    finding = models.Finding(
        id=finding_id,
        claim_id=claim.id,
        version_no=len(prior) + 1,
        status=status,
        confidence_band=band,
        proof_json=proof,
        as_of=str(claim.as_of),
        source_version_ids_json=cited,
        premise_ids_json=fact_ids,
        rule_card_ids_json=card_ids,
        checker_report_json=report,
        run_id=run_id,
        created_at=_utcnow(),
        supersedes_finding_id=prior[-1].id if prior else None,
    )
    session.add(finding)
    for old in prior:
        if is_current_finding(session, str(old.id)):
            session.add(
                models.FindingEvent(
                    id=_new_id("FE"),
                    finding_id=old.id,
                    state="SUPERSEDED",
                    reason=f"superseded by {finding_id}",
                    caused_by_type="finding",
                    caused_by_id=finding_id,
                    created_at=_utcnow(),
                )
            )
    session.add(
        models.FindingEvent(
            id=_new_id("FE"),
            finding_id=finding_id,
            state="CURRENT",
            reason=f"decided {status}",
            caused_by_type="run",
            caused_by_id=run_id,
            created_at=_utcnow(),
        )
    )
    seen: set[tuple[str, str, str]] = set()
    for dst_id in fact_ids + card_ids:
        key = ("finding", finding_id, dst_id)
        if key in seen:
            continue
        seen.add(key)
        session.add(
            models.Edge(
                id=_new_id("E"),
                src_type="finding",
                src_id=finding_id,
                dst_type="fact" if dst_id in fact_ids else "rule_card",
                dst_id=dst_id,
                rel="DEPENDS_ON",
                created_at=_utcnow(),
            )
        )
    session.add(
        models.AuditLog(
            id=_new_id("A"),
            ts=_utcnow(),
            actor_type="system",
            actor_id="memory-service",
            event="finding.decided",
            object_type="finding",
            object_id=finding_id,
            details_json={
                "status": status,
                "confidence_band": band,
                "claim_id": claim.id,
                "run_id": run_id,
            },
        )
    )
    if challenge is not None:
        session.add(
            models.ChallengerReport(
                id=_new_id("CR"),
                claim_id=claim.id,
                finding_id=finding_id,
                model=challenge.model,
                objections_json=[dict(item) for item in challenge.objections],
                created_at=_utcnow(),
            )
        )
    session.commit()
    return finding


def decide_finding(
    session: Session,
    *,
    claim_id: str,
    proof: dict[str, Any],
    run_id: str,
    challenger_blocking: bool = False,
    challenger_note: bool = False,
    challenger: bool | None = None,
    challenger_cache_dir: str | Path = llm.DEFAULT_CACHE_DIR,
) -> models.Finding:
    """Decide one claim and record the finding (T3.3, F7; T6.1 challenger).

    Status comes only from this function: the checker verdict, the
    fresh-lookup check and the challenger flags. Anything smuggled into
    the proof (including a `status` key) is ignored. `challenger=None`
    follows the `CHALLENGER` env flag (`on` runs the second pass).
    """
    claim = session.get(models.Claim, claim_id)
    if claim is None:
        raise MemoryServiceError(f"unknown claim {claim_id!r}")
    if not isinstance(proof, dict):
        raise MemoryServiceError("proof must be an object")
    matter_id = str(claim.matter_id)
    as_of = str(claim.as_of)

    if str(claim.claim_type) not in SUPPORTED_TYPES:
        return _store_decision(
            session, claim, proof, "UNKNOWN", "low", None, run_id, [], []
        )
    if (
        session.execute(
            sa.select(models.RuleCard.id).where(
                models.RuleCard.claim_type == claim.claim_type
            )
        ).first()
        is None
    ):
        return _store_decision(
            session, claim, proof, "UNKNOWN", "low", None, run_id, [], []
        )

    run_challenger = (
        challenger if challenger is not None else os.getenv("CHALLENGER", "off") == "on"
    )
    challenge: challenger_agent.ChallengerReport | None = None
    if run_challenger:
        challenge = challenger_agent.review_claim(
            question=str(claim.question_text),
            claim_type=str(claim.claim_type),
            params=dict(claim.params_json or {}),
            proof=proof,
            premise_lines=challenger_agent.premise_lines(session, matter_id),
            card_lines=challenger_agent.card_lines(session),
            session=session,
            run_id=run_id,
            cache_dir=challenger_cache_dir,
        )
        challenger_blocking = challenger_blocking or challenge.blocking
        challenger_note = challenger_note or challenge.note

    facts = _proof_facts(session, matter_id, proof)
    stores = _checker_stores(session)
    premises = {
        fact_id: {
            "statement": str(fact.statement),
            "trust_class": str(fact.trust_class),
        }
        for fact_id, fact in facts.items()
    }
    report = checker.verify(
        proof,
        premises,
        stores["provisions"],
        stores["rule_cards"],
        stores["versions"],
        stores["clauses"],
        as_of=as_of,
    )
    verdict: dict[str, Any] = {
        "valid": bool(report["valid"]),
        "errors": list(report["errors"]),
        "cited_source_versions": list(report["cited_source_versions"]),
    }
    cards = _cited_cards(session, proof)
    provisions = _cited_provisions(session, proof)
    versions = _cited_versions(session, verdict["cited_source_versions"])

    if not verdict["valid"]:
        status = "REQUIRES_REVIEW"
    elif any(fact.trust_class == "disputed" for fact in facts.values()):
        status = "REQUIRES_REVIEW"
    elif challenger_blocking:
        status = "REQUIRES_REVIEW"
    elif not _tool_log_ok(session, run_id, verdict["cited_source_versions"]):
        status = "REQUIRES_REVIEW"
    elif proof.get("conclusion") == CONCLUSION_HOLDS:
        status = "FOLLOWS"
    elif proof.get("conclusion") == CONCLUSION_FAILS:
        status = "RULED_OUT"
    else:
        status = "REQUIRES_REVIEW"

    band = _confidence_band(
        as_of, facts, cards, provisions, versions, challenger_note
    )
    return _store_decision(
        session,
        claim,
        proof,
        status,
        band,
        verdict,
        run_id,
        sorted(facts),
        sorted(cards),
        challenge,
    )
