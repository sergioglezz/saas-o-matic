"""Layer rule for the routers: spec 003 RNF-1, constitution principle 3.

The API layer validates and translates; it reaches the database only through the services.
app/api/dependencies.py is the one injection point allowed to build repositories (plan 002).
"""

from pathlib import Path

import pytest

from tests.unit.test_domain_architecture import APP_DIR, _imported_modules

API_DIR = APP_DIR / "api"
INJECTION_POINT = "dependencies.py"
FORBIDDEN_PREFIXES = ("sqlalchemy", "alembic", "app.db", "app.repositories")
ROUTER_FILES = sorted(path for path in API_DIR.rglob("*.py") if path.name != INJECTION_POINT)


def _is_forbidden(module: str) -> bool:
    return any(module == prefix or module.startswith(f"{prefix}.") for prefix in FORBIDDEN_PREFIXES)


def test_api_modules_are_found() -> None:
    """Guard: a wrong path would make the import check pass without checking anything."""
    assert {path.name for path in ROUTER_FILES} >= {"customers.py", "pricing.py", "validation.py"}
    assert (API_DIR / INJECTION_POINT).exists()


@pytest.mark.parametrize("path", [pytest.param(path, id=path.name) for path in ROUTER_FILES])
def test_api_module_does_not_reach_the_database(path: Path) -> None:
    """Spec 003 RNF-1: no SQL and no repository in the routers; only the services know them."""
    forbidden = sorted(module for module in _imported_modules(path) if _is_forbidden(module))

    assert forbidden == [], f"{path.name} imports {forbidden}"
