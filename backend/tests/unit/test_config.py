"""Frontend origin allowed by CORS: spec 002 RF-9 (CA-9.1), task T-03."""

import pytest

from app.core.config import DEFAULT_FRONTEND_ORIGIN, get_frontend_origin


def test_frontend_origin_defaults_to_the_angular_dev_server(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """CA-9.1: without configuration, the only allowed origin is http://localhost:4200."""
    monkeypatch.delenv("FRONTEND_ORIGIN", raising=False)

    assert get_frontend_origin() == DEFAULT_FRONTEND_ORIGIN == "http://localhost:4200"


def test_frontend_origin_comes_from_the_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    """CA-9.1: the allowed origin is configurable."""
    monkeypatch.setenv("FRONTEND_ORIGIN", "http://127.0.0.1:4300")

    assert get_frontend_origin() == "http://127.0.0.1:4300"
