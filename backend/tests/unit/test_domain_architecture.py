"""Layer rule for the domain: constitution principle 3 and spec 001 RNF-2.

The domain must stay pure: no web framework, no database access and no upper layers. The
imports of every module are read with ``ast``, so the check covers imports inside functions
too, without executing the code.
"""

import ast
from pathlib import Path

import pytest

APP_DIR = Path(__file__).resolve().parents[2] / "app"
DOMAIN_DIR = APP_DIR / "domain"
FORBIDDEN_PREFIXES = (
    "sqlalchemy",
    "alembic",
    "fastapi",
    "pydantic",
    "app.db",
    "app.repositories",
    "app.services",
)
DOMAIN_FILES = sorted(DOMAIN_DIR.rglob("*.py"))


def _package_of(path: Path) -> list[str]:
    return ["app", *path.parent.relative_to(APP_DIR).parts]


def _absolute_module(node: ast.ImportFrom, path: Path) -> str:
    if node.level == 0:
        return node.module or ""
    package = _package_of(path)
    base = package[: len(package) - (node.level - 1)]
    return ".".join([*base, node.module] if node.module else base)


def _imported_modules(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            modules.add(_absolute_module(node, path))
    return modules


def _is_forbidden(module: str) -> bool:
    return any(module == prefix or module.startswith(f"{prefix}.") for prefix in FORBIDDEN_PREFIXES)


def test_domain_modules_are_found() -> None:
    """Guard: a wrong path would make the import check pass without checking anything."""
    assert {path.name for path in DOMAIN_FILES} >= {"errors.py", "pricing.py", "tax.py"}


@pytest.mark.parametrize("path", [pytest.param(path, id=path.name) for path in DOMAIN_FILES])
def test_domain_module_imports_nothing_from_other_layers(path: Path) -> None:
    forbidden = sorted(module for module in _imported_modules(path) if _is_forbidden(module))

    assert forbidden == [], f"{path.name} imports {forbidden}"
