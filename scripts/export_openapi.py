"""T0.7: export the FastAPI OpenAPI schema to `openapi/openapi.json` (contract v0).

Run from the repo root with the backend env:
`backend/.venv/bin/python scripts/export_openapi.py`.
"""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.main import app  # noqa: E402


def main() -> None:
    """Write `openapi/openapi.json` with a trailing newline (T0.7)."""
    out = ROOT / "openapi" / "openapi.json"
    out.write_text(json.dumps(app.openapi(), indent=2) + "\n")


if __name__ == "__main__":
    main()
