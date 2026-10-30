"""T2.2 tests: extraction prompt shape, parsing/validation, span computation.

The live replay proof (`test_replay_extraction`) needs the recorded cassette
(`corpus/cassettes/`, via `make record` with a key) and skips without it.
"""

from pathlib import Path

import pytest

from app.agent import extract, prompts
from app.core.errors import ExtractionError
from app.services import seed

CORPUS_ROOT = Path(__file__).resolve().parents[2] / "corpus"
CASSETTES_DIR = CORPUS_ROOT / "cassettes"


def document_text() -> str:
    """The exact snapshot bytes the seed stores (T2.2)."""
    raw = (CORPUS_ROOT / "contracts" / "master_dpa.md").read_text(encoding="utf-8")
    clauses = seed.parse_contract(raw)
    text, _ = seed.build_document(clauses)
    return text


def synthetic_arguments() -> dict:
    """Well-formed tool arguments quoting the real contract (T2.2)."""
    raw = (CORPUS_ROOT / "contracts" / "master_dpa.md").read_text(encoding="utf-8")
    clauses = seed.parse_contract(raw)
    text, _ = seed.build_document(clauses)
    out_clauses = []
    out_facts = []
    for ref, heading, body in clauses:
        assert text.count(body) == 1
        out_clauses.append({"ref": ref, "heading": heading, "text": body})
        out_facts.append(
            {
                "statement": f"Clause {ref} ({heading}) applies as written.",
                "clause_ref": ref,
                "structured": {"clause_ref": ref},
            }
        )
    return {"clauses": out_clauses, "facts": out_facts}


def test_extraction_request_shape() -> None:
    """T2.2: the model is asked for structured output with temp 0."""
    request = extract.extraction_request("some contract text")
    assert request["model"] == "muse-spark-1.3"
    assert request["temperature"] == 0
    assert request["tool_choice"] == "auto"
    assert request["parallel_tool_calls"] is False
    tools = request["tools"]
    assert len(tools) == 1
    assert tools[0]["name"] == "emit_extraction"
    assert "input" in request and "some contract text" in request["input"]


def test_prompt_names_all_refs() -> None:
    """T2.2: the prompt lists the expected clause refs."""
    built = prompts.build_extraction_input("x")
    assert "emit_extraction" in built
    for ref in ("1", "8", "9.1", "9.2", "10", "11"):
        assert ref in built


def test_parse_synthetic_response() -> None:
    """T2.2: valid tool arguments parse to 12 span-exact clauses and facts."""
    text = document_text()
    result = extract.parse_extraction(text, synthetic_arguments())
    assert [clause.ref for clause in result.clauses] == seed.EXPECTED_REFS
    assert len(result.facts) == 12
    for clause in result.clauses:
        assert text[clause.span_start : clause.span_end] == clause.text
    for fact in result.facts:
        assert fact.trust_class == "document_extracted"
        assert text[fact.span_start : fact.span_end] != ""


def test_parse_rejects_duplicate_quote() -> None:
    """T2.2: a quote occurring twice is rejected instead of guessed."""
    text = document_text() + "\n" + document_text()
    with pytest.raises(ExtractionError):
        extract.parse_extraction(text, synthetic_arguments())


def test_parse_rejects_unknown_fact_ref() -> None:
    """T2.2: a fact pointing at no clause is rejected."""
    arguments = synthetic_arguments()
    arguments["facts"].append({"statement": "stray", "clause_ref": "99"})
    with pytest.raises(ExtractionError):
        extract.parse_extraction(document_text(), arguments)


def test_parse_rejects_missing_clauses() -> None:
    """T2.2: an empty clause list is rejected."""
    with pytest.raises(ExtractionError):
        extract.parse_extraction(document_text(), {"clauses": [], "facts": []})


def test_mock_extraction_fails_loudly(tmp_path: Path) -> None:
    """T2.2: mock mode has no function call, so extraction refuses it."""
    with pytest.raises(ExtractionError):
        extract.extract_document("text", mode="mock", cache_dir=tmp_path)


def test_replay_extraction() -> None:
    """T2.2: Done when 12 clauses extract from the recorded cassette with exact spans."""
    text = document_text()
    request = extract.extraction_request(text)
    from app.agent import llm

    cassette = llm.cache_file(CASSETTES_DIR, llm.request_hash(request))
    if not cassette.exists():
        pytest.skip("cassette not recorded; export MODEL_API_KEY and run make record")
    result = extract.extract_document(text, mode="replay", cache_dir=CASSETTES_DIR)
    assert [clause.ref for clause in result.clauses] == seed.EXPECTED_REFS
    assert len(result.clauses) == 12
    for clause in result.clauses:
        assert text[clause.span_start : clause.span_end] == clause.text
    assert len(result.facts) == 12
    assert {fact.trust_class for fact in result.facts} == {"document_extracted"}
