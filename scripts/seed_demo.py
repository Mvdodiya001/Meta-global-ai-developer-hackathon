"""T1.4 CLI: seed the demo database. Run with `make seed` from the repo root."""

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.db import default_db_path  # noqa: E402
from app.services.seed import seed_demo  # noqa: E402


def main() -> None:
    """Parse args, seed, print a one-line summary (T1.4)."""
    parser = argparse.ArgumentParser(description="Seed the ClauseTrace demo database")
    parser.add_argument("--db", default=str(default_db_path()))
    parser.add_argument("--corpus-root", default=str(ROOT / "corpus"))
    args = parser.parse_args()
    result = seed_demo(args.db, args.corpus_root)
    print(
        f"seeded {result['db']}: matter {result['matter_id']}, "
        f"{result['clauses']} clauses, "
        f"{len(result['versions'])} versions, "
        f"{len(result['cards'])} cards"
    )


if __name__ == "__main__":
    main()
