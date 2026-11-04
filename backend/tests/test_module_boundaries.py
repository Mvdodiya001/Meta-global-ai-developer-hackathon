"""Rewrite P0: modular boundaries hold (facades exist, layers respected)."""

import ast
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]


def _imports_of(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            names.add(node.module)
    return names


def test_domain_facades_expose_public_interfaces() -> None:
    """P0: every domain facade imports and exposes its public names."""
    from app.modules import evidence, identity, impact, intake, law, matters, verification

    assert hasattr(verification, "memory")
    assert hasattr(verification.memory, "decide_finding")
    assert hasattr(verification, "agent_loop")
    assert hasattr(law, "sources") and hasattr(law, "rulecards") and hasattr(law, "diff")
    assert hasattr(impact, "reverify") and hasattr(impact, "counterfactual")
    assert hasattr(intake, "scan") and hasattr(intake, "transcribe")
    assert hasattr(evidence, "premises") and hasattr(evidence, "graph")
    assert hasattr(matters, "seed")
    assert identity is not None


def test_no_domain_imports_the_http_layer() -> None:
    """P0: agent/services/modules/checker never import app.api or app.main."""
    offenders: list[str] = []
    for root in ("app/agent", "app/services", "app/modules", "checker"):
        for path in sorted((BACKEND / root).rglob("*.py")):
            imported = _imports_of(path)
            if any(
                name == "app.api" or name.startswith("app.api.") or name == "app.main"
                for name in imported
            ):
                offenders.append(f"{path.relative_to(BACKEND)} imports the HTTP layer")
    assert offenders == []
