import ast
from pathlib import Path

import pytest

ROUTES_DIR = Path(__file__).resolve().parents[2] / "app" / "routes"
FORBIDDEN_PREFIXES = ("app.models", "app.extensions")


def _route_modules() -> list[Path]:
    return sorted(ROUTES_DIR.glob("*.py"))


def _imported_modules(tree: ast.AST) -> set[str]:
    modules = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            modules.add(node.module)
    return modules


def test_route_modules_are_discovered():
    assert _route_modules(), f"no route modules found under {ROUTES_DIR}"


@pytest.mark.parametrize("path", _route_modules(), ids=lambda path: path.name)
def test_route_modules_does_not_import_models_or_db(path: Path):
    modules = _imported_modules(ast.parse(path.read_text(encoding="utf-8")))
    offenders = sorted(name for name in modules if name.startswith(FORBIDDEN_PREFIXES))
    assert not offenders, (
        f"{path.name} imports {offenders}. Tenant-scoped queries belong in the "
        "service layer so the org filter lives in the WHERE clause."
    )
    