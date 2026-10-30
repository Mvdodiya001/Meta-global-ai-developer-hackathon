"""Record LLM cassettes (spends credits). Run at most once per task: `make record`.

T2.2 records the Master DPA extraction cassette into `corpus/cassettes/`.
Needs `MODEL_API_KEY` in the environment; never prints it.
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

import sqlalchemy as sa  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402

from app.agent import extract, llm  # noqa: E402
from app import models  # noqa: E402
from app.db import default_db_path, init_db  # noqa: E402
from app.services import seed  # noqa: E402


def document_text() -> str:
    """The exact snapshot bytes the seed stores (T2.2)."""
    raw = (ROOT / "corpus" / "contracts" / "master_dpa.md").read_text(encoding="utf-8")
    text, _ = seed.build_document(seed.parse_contract(raw))
    return text


def main() -> None:
    """Record the extraction cassette once and print its cost (T2.2)."""
    cassettes = ROOT / "corpus" / "cassettes"
    text = document_text()
    request = extract.extraction_request(text)
    cassette = llm.cache_file(cassettes, llm.request_hash(request))
    if cassette.exists():
        print(f"cassette already recorded: {cassette}")
        return
    engine = init_db(default_db_path())
    session = sessionmaker(bind=engine, future=True)()
    try:
        result = extract.extract_document(
            text, mode="live", cache_dir=cassettes, session=session
        )
    except Exception:
        if cassette.exists():
            cassette.unlink()
        raise
    if len(result.clauses) != 12:
        if cassette.exists():
            cassette.unlink()
        raise SystemExit(f"expected 12 clauses, got {len(result.clauses)}; cassette removed")
    row = session.execute(
        sa.select(models.LlmCall).order_by(models.LlmCall.id.desc())
    ).scalars().first()
    cost = row.cost_est if row is not None else 0.0
    print(
        f"recorded {cassette} ({result.model}, "
        f"{len(result.clauses)} clauses, {len(result.facts)} facts, "
        f"cost_est=${cost:.6f})"
    )
    session.close()


if __name__ == "__main__":
    main()
