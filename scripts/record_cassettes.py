"""Record LLM cassettes (spends credits). Run at most once per task: `make record`.

T2.2 records the Master DPA extraction cassette, T2.3 one cassette per sample
question, T2.5 the clause-9.2 agent-loop turns, all into `corpus/cassettes/`.
Needs `MODEL_API_KEY` in the environment and a seeded demo database
(`make seed` first); never prints the key.
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

import sqlalchemy as sa  # noqa: E402
from sqlalchemy.orm import Session, sessionmaker  # noqa: E402

from app.agent import challenger, claims, extract, llm, loop  # noqa: E402
from app import models  # noqa: E402
from app.db import default_db_path, init_db  # noqa: E402
from app.services import seed  # noqa: E402


def document_text() -> str:
    """The exact snapshot bytes the seed stores (T2.2)."""
    raw = (ROOT / "corpus" / "contracts" / "master_dpa.md").read_text(encoding="utf-8")
    text, _ = seed.build_document(seed.parse_contract(raw))
    return text


def record_claims(cassettes: Path, inventory: str, session: Session) -> None:
    """Record one cassette per T2.3 sample question, skipping existing ones (T2.3)."""
    for sample in claims.CLAIM_SAMPLES:
        request = claims.claim_request(sample["question"], inventory)
        cassette = llm.cache_file(cassettes, llm.request_hash(request))
        if cassette.exists():
            print(f"cassette already recorded: {cassette.name} ({sample['id']})")
            continue
        draft = claims.structure_claim(
            sample["question"], inventory, mode="live", cache_dir=cassettes, session=session
        )
        print(f"recorded {cassette.name} ({sample['id']} -> {draft.claim_type})")


def record_loop(cassettes: Path, session: Session) -> None:
    """Record the clause-9.2 agent-loop cassettes, live, once (T2.5)."""
    claim_id = loop.ensure_demo_92_claim(session)
    result = loop.run_verify(
        session, claim_id=claim_id, matter_id="MAT-01", mode="live", cache_dir=cassettes
    )
    print(
        f"loop {result.outcome} after {result.tool_calls} tool calls "
        f"(accepted={result.accepted})"
    )
    if not result.accepted or result.report is None or not result.report["valid"]:
        raise SystemExit("loop did not yield a checker-valid proof; fix and re-run")


def record_challenger(cassettes: Path, session: Session) -> None:
    """Record the challenger review of the tampered 9.2 proof, live, once (T6.1)."""
    claim_id = loop.ensure_demo_92_claim(session)
    claim = session.get(models.Claim, claim_id)
    assert claim is not None
    proof = challenger.demo_flawed_proof()
    report = challenger.review_claim(
        question=str(claim.question_text),
        claim_type=str(claim.claim_type),
        params=dict(claim.params_json or {}),
        proof=proof,
        premise_lines=challenger.premise_lines(session, "MAT-01"),
        card_lines=challenger.card_lines(session),
        mode="live",
        cache_dir=cassettes,
        session=session,
    )
    print(
        f"challenger blocking={report.blocking} "
        f"({len(report.objections)} objections)"
    )


def main() -> None:
    """Record the extraction + claim + loop cassettes and print the cost."""
    cassettes = ROOT / "corpus" / "cassettes"
    text = document_text()
    engine = init_db(default_db_path())
    session = sessionmaker(bind=engine, future=True)()
    try:
        request = extract.extraction_request(text)
        cassette = llm.cache_file(cassettes, llm.request_hash(request))
        if cassette.exists():
            print(f"cassette already recorded: {cassette}")
        else:
            result = extract.extract_document(
                text, mode="live", cache_dir=cassettes, session=session
            )
            if len(result.clauses) != 12:
                cassette.unlink(missing_ok=True)
                raise SystemExit(
                    f"expected 12 clauses, got {len(result.clauses)}; cassette removed"
                )
            print(
                f"recorded {cassette} ({result.model}, "
                f"{len(result.clauses)} clauses, {len(result.facts)} facts)"
            )
        raw = (ROOT / "corpus" / "contracts" / "master_dpa.md").read_text(encoding="utf-8")
        inventory = claims.build_inventory(seed.parse_contract(raw))
        record_claims(cassettes, inventory, session)
        record_loop(cassettes, session)
        record_challenger(cassettes, session)
        row = session.execute(
            sa.select(models.LlmCall).order_by(models.LlmCall.id.desc())
        ).scalars().first()
        cost = row.cost_est if row is not None else 0.0
        print(f"latest llm_calls cost_est=${cost:.6f}")
    finally:
        session.close()


if __name__ == "__main__":
    main()
