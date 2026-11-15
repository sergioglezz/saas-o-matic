"""Application factory and request dependencies: spec 002 base of RF-1 and RNF-5, task T-04."""

from typing import Annotated

from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

from app.api.dependencies import get_rate_source
from app.services.pricing import TaxRateSource


def test_the_module_named_in_agents_md_exposes_the_application() -> None:
    """`uvicorn app.main:app` needs a FastAPI instance at that import path."""
    from app.main import app

    assert isinstance(app, FastAPI)


def test_interactive_docs_and_openapi_schema_are_served(client: TestClient) -> None:
    """RNF-5 (base): /docs and /openapi.json respond."""
    assert client.get("/docs").status_code == 200

    response = client.get("/openapi.json")
    assert response.status_code == 200
    assert response.json()["openapi"].startswith("3.")


def test_rate_source_dependency_reads_the_migrated_database(app: FastAPI) -> None:
    """The per-request session and rate source are wired to the configured database."""

    def probe(rates: Annotated[TaxRateSource, Depends(get_rate_source)]) -> dict[str, int | None]:
        return {"ES": rates.get_rate_bp("ES"), "XX": rates.get_rate_bp("XX")}

    app.add_api_route("/_probe/rates", probe, methods=["GET"])

    with TestClient(app) as client:
        assert client.get("/_probe/rates").json() == {"ES": 2100, "XX": None}
