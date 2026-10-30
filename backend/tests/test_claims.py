"""T2.3 tests: claim typing per ARCHITECTURE §7, UNKNOWN with explanation.

The six replay tests need cassettes (`corpus/cassettes/`, via `make record`
with a key) and skip without them.
"""

from pathlib import Path

import pytest

from app.agent import claims
from app.core.errors import ClaimError
from app.services import seed

CORPUS_ROOT = Path(__file__).resolve().parents[2] / "corpus"
CASSETTES_DIR = CORPUS_ROOT / "cassettes"

EXPECTED_TYPES = {
    "ct1-window": "CT1",
    "ct2-deletion": "CT2",
    "ct3-inforce": "CT3",
    "ct4-role": "CT4",
    "unk-fairness": "UNKNOWN",
    "unk-summary": "UNKNOWN",
}


def inventory() -> str:
    """The clause inventory the structurer sees (T2.3)."""
    raw = (CORPUS_ROOT / "contracts" / "master_dpa.md").read_text(encoding="utf-8")
    return claims.build_inventory(seed.parse_contract(raw))


def test_sample_set_covers_required_cases() -> None:
    """T2.3: 3+ supported and 2 unsupported samples exist."""
    types = [sample["id"].split("-")[0] for sample in claims.CLAIM_SAMPLES]
    assert len(claims.CLAIM_SAMPLES) >= 5
    assert sum(1 for tag in types if tag != "unk") >= 3
    assert sum(1 for tag in types if tag == "unk") >= 2


def test_claim_request_shape() -> None:
    """T2.3: the model is asked for a typed claim with temp 0."""
    request = claims.claim_request("Is Nimbus a processor?", inventory())
    assert request["model"] == "muse-spark-1.3-contributor"
    assert request["temperature"] == 0
    assert request["tool_choice"] == "auto"
    assert request["parallel_tool_calls"] is False
    assert request["tools"][0]["name"] == "emit_claim"
    assert "2026-11-20" in request["input"]
    assert "9.2" in request["input"]


def test_parse_supported_shapes() -> None:
    """T2.3: one valid payload per supported type parses."""
    payloads = [
        {
            "claim_type": "CT1",
            "params": {"value": 72, "unit": "hours"},
            "question_text": "q",
        },
        {
            "claim_type": "CT2",
            "params": {"element": "deletion on instruction"},
            "question_text": "q",
        },
        {"claim_type": "CT3", "params": {"date": "2027-06-01"}, "question_text": "q"},
        {
            "claim_type": "CT4",
            "params": {"party": "Nimbus", "role": "Data Processor"},
            "question_text": "q",
        },
    ]
    for payload in payloads:
        draft = claims.parse_claim(payload, "q")
        assert draft.claim_type == payload["claim_type"]
        assert draft.explanation == ""


def test_parse_unknown_needs_explanation() -> None:
    """T2.3: UNKNOWN without an explanation is rejected."""
    with pytest.raises(ClaimError):
        claims.parse_claim({"claim_type": "UNKNOWN", "params": {}, "question_text": "q"}, "q")
    draft = claims.parse_claim(
        {
            "claim_type": "UNKNOWN",
            "params": {},
            "question_text": "q",
            "explanation": "fairness is not a rule test",
        },
        "q",
    )
    assert draft.claim_type == "UNKNOWN"
    assert draft.explanation != ""


def test_parse_rejects_bad_shapes() -> None:
    """T2.3: wrong types and missing params are rejected."""
    with pytest.raises(ClaimError):
        claims.parse_claim({"claim_type": "CT5", "params": {}, "question_text": "q"}, "q")
    with pytest.raises(ClaimError):
        claims.parse_claim(
            {"claim_type": "CT1", "params": {"unit": "hours"}, "question_text": "q"}, "q"
        )
    with pytest.raises(ClaimError):
        claims.parse_claim(
            {"claim_type": "CT3", "params": {"date": "next June"}, "question_text": "q"}, "q"
        )
    with pytest.raises(ClaimError):
        claims.parse_claim({"claim_type": "CT2", "params": {}}, "")
    with pytest.raises(ClaimError):
        claims.parse_claim("not-an-object", "q")  # type: ignore[arg-type]


def test_mock_claim_fails_loudly(tmp_path: Path) -> None:
    """T2.3: mock mode has no function call, so structuring refuses it."""
    with pytest.raises(ClaimError):
        claims.structure_claim(
            "Is Nimbus a processor?", inventory(), mode="mock", cache_dir=tmp_path
        )


@pytest.mark.parametrize("sample_id,expected", sorted(EXPECTED_TYPES.items()))
def test_replay_samples(sample_id: str, expected: str) -> None:
    """T2.3: Done when the samples behave correctly from recorded cassettes."""
    sample = next(item for item in claims.CLAIM_SAMPLES if item["id"] == sample_id)
    request = claims.claim_request(sample["question"], inventory())
    from app.agent import llm

    cassette = llm.cache_file(CASSETTES_DIR, llm.request_hash(request))
    if not cassette.exists():
        pytest.skip("claim cassettes not recorded; export MODEL_API_KEY and run make record")
    draft = claims.structure_claim(
        sample["question"], inventory(), mode="replay", cache_dir=CASSETTES_DIR
    )
    assert draft.claim_type == expected, draft
    if expected == "UNKNOWN":
        assert draft.explanation != ""
