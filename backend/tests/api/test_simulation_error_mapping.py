"""The simulation domain errors as HTTP responses, spec 004 task T-06 (level I, test routes).

InvalidStorageError and InvalidApiCallsError cannot reach the API from a valid request (the
schema stops those values first, plan 004 DT-2), so their mapping is checked with test routes.
"""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.error_mapping import register_domain_error_handlers
from app.core.errors import register_error_handlers
from app.domain.errors import (
    InvalidApiCallsError,
    InvalidStorageError,
    UnsupportedCustomerCountryError,
)


@pytest.mark.parametrize(
    ("error", "field", "message"),
    [
        pytest.param(
            InvalidStorageError(-1),
            "storage_gb",
            "Debe ser un número entero entre 0 y 1000000",
            id="STO",
        ),
        pytest.param(
            InvalidApiCallsError(-1),
            "api_calls_per_month",
            "Debe ser un número entero entre 0 y 1000000000",
            id="APC",
        ),
        pytest.param(
            UnsupportedCustomerCountryError(2),
            "customer_id",
            "El país del cliente no está soportado",
            id="CNS",
        ),
    ],
)
def test_simulation_errors_become_422_on_their_field(
    error: Exception, field: str, message: str
) -> None:
    """CA-2.3, CA-2.4, CA-3.4: 422 validation_error with the detail of section 5."""
    app = FastAPI()
    register_error_handlers(app)
    register_domain_error_handlers(app)

    @app.get("/raise")
    def raise_error() -> None:
        raise error

    response = TestClient(app).get("/raise")

    assert response.status_code == 422
    assert response.json() == {
        "error": {
            "code": "validation_error",
            "message": "Datos no válidos",
            "details": [{"field": field, "message": message}],
        }
    }
