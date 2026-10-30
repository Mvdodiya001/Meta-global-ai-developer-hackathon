"""T3.1: backend/checker/ never imports app.agent or any LLM/network client.

AST scan over every checker module: banned are `app.agent*`, dynamic imports,
and any module that speaks to a network or a model vendor.
"""

import ast
from pathlib import Path

CHECKER_DIR = Path(__file__).resolve().parents[1] / "checker"

BANNED_PREFIXES = ("app.agent",)
BANNED_ROOTS = frozenset(
    {
        "urllib",
        "urllib3",
        "httpx",
        "httpx2",
        "requests",
        "http",
        "socket",
        "ssl",
        "openai",
        "anthropic",
        "boto3",
        "botocore",
        "importlib",
    }
)


def violations_in(path: Path) -> list[str]:
    """Collect banned import usages in one file (T3.1)."""
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    found: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name == "app.agent" or alias.name.startswith("app.agent."):
                    found.append(f"{path.name}:{node.lineno}: imports app.agent")
                if alias.name.split(".")[0] in BANNED_ROOTS:
                    found.append(f"{path.name}:{node.lineno}: imports {alias.name}")
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            if module == "app.agent" or module.startswith("app.agent."):
                found.append(f"{path.name}:{node.lineno}: imports app.agent")
            if module.split(".")[0] in BANNED_ROOTS:
                found.append(f"{path.name}:{node.lineno}: imports {module}")
        elif isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name) and func.id == "__import__":
                found.append(f"{path.name}:{node.lineno}: dynamic __import__")
            if isinstance(func, ast.Attribute) and func.attr == "import_module":
                found.append(f"{path.name}:{node.lineno}: dynamic import_module")
    return found


def test_checker_has_no_banned_imports() -> None:
    """T3.1: Done when the AST scan passes over every checker module."""
    files = sorted(CHECKER_DIR.glob("*.py"))
    assert files, "checker package is empty"
    problems = [problem for path in files for problem in violations_in(path)]
    assert problems == []
