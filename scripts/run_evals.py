"""Run the golden-set evaluation gate (Rewrite P5). Replay only.

Usage: backend/.venv/bin/python scripts/run_evals.py [--db PATH]
Exit code 0 iff the gate passes (all cases agree, zero premise
violations). Safe to run in CI: it never calls a live model.
"""

import argparse
import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.agent.evals import run_evals  # noqa: E402


def main() -> int:
    """Run the gate and print the report as JSON (P5)."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", default=None)
    args = parser.parse_args()
    db = args.db or str(Path(tempfile.mkdtemp(prefix="ct-evals-")) / "evals.db")
    report = run_evals(db)
    print(json.dumps(report, indent=2))
    return 0 if report["gate_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
