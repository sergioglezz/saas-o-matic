"""HTTP test fixtures: the real application on a migrated temporary database (plan 002 DT-8)."""

from collections.abc import Iterator
from datetime import datetime

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import Engine

from app.api.dependencies import get_now
from app.main import create_app
from tests.api.customer_requests import FIXED_NOW


@pytest.fixture
def app(database_url: str, migrated_engine: Engine) -> FastAPI:
    # Depending on migrated_engine guarantees the schema exists before the app uses it.
    return create_app(database_url=database_url)


@pytest.fixture
def client(app: FastAPI) -> Iterator[TestClient]:
    # raise_server_exceptions=False: a 500 must come back as a response, as a browser sees it.
    with TestClient(app, raise_server_exceptions=False) as test_client:
        yield test_client


@pytest.fixture
def fixed_clock(app: FastAPI) -> datetime:
    """Freeze "now" at the instant of the examples of spec 003 section 5 (plan 003 DT-10)."""
    app.dependency_overrides[get_now] = lambda: FIXED_NOW
    return FIXED_NOW
