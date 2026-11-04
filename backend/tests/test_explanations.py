"""Phase 4: readability layer — tone guardrails + explanation storage."""

from pathlib import Path

from sqlalchemy.orm import sessionmaker

from app import models
from app.db import init_db
from app.modules.intake import explanations


def test_tone_filter_rejects_advice() -> None:
    """Phase 4: advice-like phrasing is never tone-safe."""
    assert not explanations.tone_safe("You should sign this clause.")
    assert not explanations.tone_safe("This is legal and compliant.")
    assert not explanations.tone_safe("We recommend accepting.")
    assert explanations.tone_safe("This clause appears to require notice.")


def test_explain_clause_mock_is_quote_anchored() -> None:
    """Phase 4: mock-mode explanation quotes the clause and stays safe."""
    out = explanations.explain_clause(
        "9.2",
        "Transfer logs",
        "Nimbus shall keep transfer logs for review.",
        mode="mock",
    )
    assert "transfer logs" in out["says"]
    assert all(explanations.tone_safe(value) for value in out.values())


def test_store_explanations_and_summary(tmp_path: Path) -> None:
    """Phase 4: explanations + summary land as ai_inferred facts, deduped."""
    engine = init_db(tmp_path / "reading.db")
    session = sessionmaker(bind=engine, future=True)()
    session.add(models.Matter(id="MAT-01", client_name="Acme", title="M1"))
    session.add(models.Document(id="DOC-01", matter_id="MAT-01", title="DPA", kind="dpa"))
    session.add(
        models.DocumentVersion(
            id="DV-01",
            document_id="DOC-01",
            text="contract text",
            sha256="0" * 64,
            created_at="2026-01-01T00:00:00Z",
        )
    )
    session.add(
        models.Clause(
            id="CL-01",
            document_version_id="DV-01",
            ref="9.2",
            heading="Transfer",
            text="Nimbus shall keep transfer logs for review.",
            span_start=0,
            span_end=10,
        )
    )
    session.commit()

    created = explanations.store_explanations(
        session, matter_id="MAT-01", document_id="DOC-01", mode="mock"
    )
    assert created == 1
    fact = session.query(models.Fact).one()
    assert fact.trust_class == "ai_inferred"
    assert (fact.structured_json or {}).get("kind") == "explanation"
    assert (
        explanations.store_explanations(
            session, matter_id="MAT-01", document_id="DOC-01", mode="mock"
        )
        == 0
    )

    summary = explanations.store_summary(
        session, matter_id="MAT-01", document_id="DOC-01", mode="mock"
    )
    assert (summary.structured_json or {}).get("kind") == "summary"
    assert explanations.tone_safe(summary.statement)
    session.close()
