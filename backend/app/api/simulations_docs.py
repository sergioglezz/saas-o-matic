"""OpenAPI documentation of the simulation routes (spec 004 RNF-5).

Kept apart from the routes so they stay short. The examples are the ones of spec 004 section 5,
and every documented error shows the single format (spec 002 RF-6).
"""

from typing import Any

from app.api.openapi_examples import Responses, error_example, invalid_example, json_example
from app.core.errors import NOT_FOUND_MESSAGE
from app.schemas.pagination import LIMIT_INVALID_MESSAGE
from app.schemas.pricing import USERS_INVALID_MESSAGE
from app.schemas.simulations import (
    SIMULATION_LIST_RESPONSE_EXAMPLE,
    SIMULATION_REQUEST_EXAMPLE,
    SIMULATION_RESPONSE_EXAMPLE,
    SimulationCreate,
)

SAVE_PATH = "/simulations"
HISTORY_PATH = "/customers/{customer_id}/simulations"

_NOT_FOUND = json_example(
    "Cliente no encontrado", error_example("not_found", NOT_FOUND_MESSAGE, [])
)

# The body is read by hand (plan 002 DT-1), so FastAPI cannot infer it for /docs.
SAVE_BODY_DOC: dict[str, Any] = {
    "requestBody": {
        "required": True,
        "content": {
            "application/json": {
                "schema": SimulationCreate.model_json_schema(),
                "example": SIMULATION_REQUEST_EXAMPLE,
            }
        },
    }
}
SAVE_RESPONSES: Responses = {
    201: json_example("Simulación guardada", SIMULATION_RESPONSE_EXAMPLE),
    404: _NOT_FOUND,
    422: invalid_example("active_users", USERS_INVALID_MESSAGE),
}
HISTORY_RESPONSES: Responses = {
    200: json_example("Simulaciones del cliente", SIMULATION_LIST_RESPONSE_EXAMPLE),
    404: _NOT_FOUND,
    422: invalid_example("limit", LIMIT_INVALID_MESSAGE),
}


def restore_simulation_examples(schema: dict[str, Any]) -> dict[str, Any]:
    """Put the exact examples back into the generated OpenAPI schema (RNF-5, plan DT-11).

    FastAPI drops every null value when it builds /openapi.json, examples included, which would
    hide "to_users": null in the last tier of every documented simulation.
    """
    paths = schema["paths"]
    _set_example(paths[SAVE_PATH]["post"], "201", SIMULATION_RESPONSE_EXAMPLE)
    _set_example(paths[HISTORY_PATH]["get"], "200", SIMULATION_LIST_RESPONSE_EXAMPLE)
    return schema


def _set_example(operation: dict[str, Any], status: str, example: object) -> None:
    operation["responses"][status]["content"]["application/json"]["example"] = example
