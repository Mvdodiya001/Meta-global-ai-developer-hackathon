"""T3.2: `python -m checker verify proof.json` (F9).

Reads a self-contained bundle
`{proof, premises, provisions, rule_cards, versions, clauses, as_of}`,
prints the `verify_derivation` report as JSON, and exits 0 whether the proof
is valid or not. Exit 2 means the input itself was unusable.
"""

import json
import sys
from pathlib import Path
from typing import Any

from checker.verify import verify

USAGE = "usage: python -m checker verify proof.json"


def _fail(message: str) -> int:
    """Report unusable input on stderr (T3.2)."""
    print(f"checker: {message}", file=sys.stderr)
    return 2


def main(argv: list[str]) -> int:
    """Verify one proof bundle file (T3.2)."""
    if len(argv) != 2 or argv[0] != "verify":
        return _fail(USAGE)
    try:
        bundle: Any = json.loads(Path(argv[1]).read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        return _fail(f"cannot read proof bundle: {exc}")
    if not isinstance(bundle, dict) or not isinstance(bundle.get("proof"), dict):
        return _fail("bundle needs a proof object")
    report = verify(
        bundle["proof"],
        bundle.get("premises", {}),
        bundle.get("provisions", {}),
        bundle.get("rule_cards", {}),
        bundle.get("versions", {}),
        bundle.get("clauses", {}),
        bundle.get("as_of", ""),
    )
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
