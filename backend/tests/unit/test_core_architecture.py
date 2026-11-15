"""Layer rule for app/core: spec 003 RF-7 (plan DT-14), review log entry 16.

The single error format and the settings must stay generic: if core imported a feature, every
new spec would have to edit it. The imports are read with ``ast``, as in the domain rule.
"""

from pathlib import Path

import pytest

from tests.unit.test_domain_architecture import APP_DIR, _imported_modules

CORE_DIR = APP_DIR / "core"
FORBIDDEN_PREFIXES = (
    "app.api",
    "app.schemas",
    "app.services",
    "app.repositories",
    "app.domain",
    "app.db",
)
CORE_FILES = sorted(CORE_DIR.rglob("*.py"))


def _is_forbidden(module: str) -> bool:
    return any(module == prefix or module.startswith(f"{prefix}.") for prefix in FORBIDDEN_PREFIXES)


def test_core_modules_are_found() -> None:
    """Guard: a wrong path would make the import check pass without checking anything."""
    assert {path.name for path in CORE_FILES} >= {"config.py", "errors.py"}


@pytest.mark.parametrize("path", [pytest.param(path, id=path.name) for path in CORE_FILES])
def test_core_module_imports_no_other_layer(path: Path) -> None:
    """Spec 003 RF-7: core knows no feature, so the error format serves any route."""
    forbidden = sorted(module for module in _imported_modules(path) if _is_forbidden(module))

    assert forbidden == [], f"{path.name} imports {forbidden}"
