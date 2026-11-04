"""T7.3: counterfactual mode — read-only what-if impact (F19).

Answers "what if this version were applied?" without writing anything:
the same diff and reverse traversal as `services/impact.py`, then a
deterministic propositional-logic check per affected finding. Each
finding's proof becomes propositions — one atom per premise, rule,
force and evidence step, plus the proof's inference rule
`(all atoms) -> conclusion` — and `checker.proplogic.entails` decides
whether the conclusion still follows when the atoms tied to changed
provisions are removed. Findings that would no longer be valid are
returned in `reverify_list`. No STALE events, edges, findings or audit
rows are written; `services/impact.py` remains the only applier.
"""

import re
from typing import Any

import sqlalchemy as sa
from sqlalchemy.orm import Session

from app import models
from app.modules.evidence import graph
from app.modules.impact import impact
from checker import proplogic

ADMITTED_TRUST = frozenset({"lawyer_confirmed", "document_extracted"})
CONCLUSION_ATOM = "conclusion_holds"


def _finding_logic(
    session: Session, finding: models.Finding, changed_keys: set[str]
) -> dict[str, Any]:
    """Propositional validity of one finding under the change (T7.3)."""
    proof = finding.proof_json if isinstance(finding.proof_json, dict) else None
    if proof is None:
        return {"valid": False, "consistent": False, "counterexample": None, "atoms": []}
    atoms: list[str] = []
    holding: list[str] = []

    def atom(name: str, holds: bool) -> None:
        safe = re.sub(r"[^A-Za-z0-9_]", "_", name)
        if safe not in atoms:
            atoms.append(safe)
        if holds and safe not in holding:
            holding.append(safe)

    for entry in proof.get("premises", []):
        if not isinstance(entry, dict):
            continue
        fact_id = entry.get("fact_id")
        fact = session.get(models.Fact, fact_id) if isinstance(fact_id, str) else None
        atom(
            f"fact_{fact_id}",
            fact is not None and str(fact.trust_class) in ADMITTED_TRUST,
        )
    for step in proof.get("steps", []):
        if not isinstance(step, dict):
            continue
        kind = step.get("kind")
        if kind == "cite_rule":
            card_id = step.get("rule_card_id")
            card = session.get(models.RuleCard, card_id) if isinstance(card_id, str) else None
            provision = (
                session.get(models.Provision, card.provision_id) if card is not None else None
            )
            atom(
                f"rule_{card_id}",
                provision is not None and str(provision.key) not in changed_keys,
            )
        elif kind == "in_force":
            provision_id = step.get("provision_id")
            provision = (
                session.get(models.Provision, provision_id)
                if isinstance(provision_id, str)
                else None
            )
            atom(
                f"force_{provision_id}",
                provision is not None and str(provision.key) not in changed_keys,
            )
        elif kind in ("contains_element", "role_applies"):
            atom(f"evidence_{step.get('clause_id')}", True)
        elif kind == "compare":
            atom("compare_ok", True)
    if not atoms:
        return {"valid": False, "consistent": False, "counterexample": None, "atoms": []}
    rule = f"({' & '.join(atoms)}) -> {CONCLUSION_ATOM}"
    return proplogic.entails(holding + [rule], CONCLUSION_ATOM)


def run_counterfactual(session: Session, source_version_id: str) -> dict[str, Any]:
    """Dry-run applying one version; never writes (T7.3, F19)."""
    version = session.get(models.SourceVersion, source_version_id)
    if version is None:
        return {
            "available": False,
            "note": f"unknown source version: {source_version_id}",
            "source_version_id": source_version_id,
            "changed_keys": [],
            "affected": [],
            "reverify_list": [],
            "nodes": [],
            "edges": [],
        }
    changed_keys: list[str] = []
    if version.supersedes_id is not None:
        old_rows = impact.version_provisions(session, str(version.supersedes_id))
        new_rows = impact.version_provisions(session, str(version.id))
        diff = impact.diff_provisions(
            [impact.snapshot(r) for r in old_rows],
            [impact.snapshot(r) for r in new_rows],
        )
        changed_keys = sorted(diff["changed"] + diff["removed"])
    changed = set(changed_keys)
    keyed_rows = [
        row
        for row in session.execute(
            sa.select(models.Provision)
            .join(
                models.SourceVersion,
                models.Provision.source_version_id == models.SourceVersion.id,
            )
            .where(models.SourceVersion.source_id == version.source_id)
        )
        .scalars()
        .all()
        if str(row.key) in changed
    ]
    finding_ids: set[str] = set()
    for row in keyed_rows:
        finding_ids.update(graph.dependent_findings_live(session, str(row.id))[0])
    affected: list[dict[str, Any]] = []
    nodes: dict[str, dict[str, Any]] = {}
    edges: list[dict[str, str]] = []
    for finding_id in sorted(finding_ids):
        finding = session.get(models.Finding, finding_id)
        if finding is None:
            continue
        logic = _finding_logic(session, finding, changed)
        valid = bool(logic["valid"])
        affected.append(
            {
                "finding_id": finding_id,
                "claim_id": str(finding.claim_id),
                "would_remain_valid": valid,
                "would_follow_label": (
                    "Would still meet the requirement"
                    if valid
                    else "This answer would no longer follow"
                ),
                "logic": logic,
            }
        )
        nodes[finding_id] = {
            "id": finding_id,
            "kind": "finding",
            "label": f"{finding_id} {finding.status}",
        }
        for edge in session.execute(
            sa.select(models.Edge).where(
                models.Edge.src_type == "finding",
                models.Edge.src_id == finding_id,
                models.Edge.rel == "DEPENDS_ON",
            )
        ).scalars().all():
            nodes.setdefault(
                str(edge.dst_id),
                {"id": str(edge.dst_id), "kind": str(edge.dst_type), "label": str(edge.dst_id)},
            )
            edges.append(
                {"src": finding_id, "dst": str(edge.dst_id), "rel": "DEPENDS_ON"}
            )
    return {
        "available": True,
        "note": (
            "Read-only counterfactual: no findings were marked stale. "
            "Findings in reverify_list would no longer be valid if this "
            "version were applied."
        ),
        "source_version_id": str(version.id),
        "changed_keys": changed_keys,
        "affected": affected,
        "reverify_list": [
            item["finding_id"] for item in affected if not item["would_remain_valid"]
        ],
        "nodes": [nodes[key] for key in sorted(nodes)],
        "edges": edges,
    }
