"""OpenAPI documentation of the customer routes (spec 003 RNF-4).

Kept apart from the routes so they stay short. The examples are the ones of spec 003
section 5, and every documented error shows the single format (spec 002 RF-6).
"""

from typing import Any

from app.api.openapi_examples import Responses, error_example, invalid_example, json_example
from app.core.errors import CONFLICT_MESSAGE, NOT_FOUND_MESSAGE
from app.schemas.customers import (
    CUSTOMER_LIST_RESPONSE_EXAMPLE,
    CUSTOMER_REQUEST_EXAMPLE,
    CUSTOMER_RESPONSE_EXAMPLE,
    TAX_ID_DUPLICATED_MESSAGE,
    TAX_ID_SPANISH_MESSAGE,
    CustomerCreate,
)
from app.schemas.pagination import LIMIT_INVALID_MESSAGE

_NOT_FOUND = json_example(
    "Cliente no encontrado", error_example("not_found", NOT_FOUND_MESSAGE, [])
)
_CONFLICT = json_example(
    "Identificador fiscal ya registrado",
    error_example(
        "conflict", CONFLICT_MESSAGE, [{"field": "tax_id", "message": TAX_ID_DUPLICATED_MESSAGE}]
    ),
)


# The body is read by hand (plan 002 DT-1), so FastAPI cannot infer it for /docs.
REGISTER_BODY_DOC: dict[str, Any] = {
    "requestBody": {
        "required": True,
        "content": {
            "application/json": {
                "schema": CustomerCreate.model_json_schema(),
                "example": CUSTOMER_REQUEST_EXAMPLE,
            }
        },
    }
}
REGISTER_RESPONSES: Responses = {
    201: json_example("Cliente registrado", CUSTOMER_RESPONSE_EXAMPLE),
    409: _CONFLICT,
    422: invalid_example("tax_id", TAX_ID_SPANISH_MESSAGE),
}
LIST_RESPONSES: Responses = {
    200: json_example("Clientes que coinciden con la búsqueda", CUSTOMER_LIST_RESPONSE_EXAMPLE),
    422: invalid_example("limit", LIMIT_INVALID_MESSAGE),
}
DETAIL_RESPONSES: Responses = {
    200: json_example("Datos del cliente", CUSTOMER_RESPONSE_EXAMPLE),
    404: _NOT_FOUND,
}
DELETE_RESPONSES: Responses = {
    204: {"description": "Cliente borrado junto con todo su historial de simulaciones"},
    404: _NOT_FOUND,
}

_FRAMEWORK_VALIDATION_SCHEMAS = ("HTTPValidationError", "ValidationError")


def without_framework_validation_error(schema: dict[str, Any]) -> dict[str, Any]:
    """Drop the 422 that FastAPI documents by itself for any route with parameters.

    The API never answers with that format (spec 003 RF-7): the routes that can answer 422
    declare their own example, and advertising another one would mislead whoever reads /docs.
    """
    for path_item in schema["paths"].values():
        for operation in path_item.values():
            responses = operation.get("responses", {})
            if "HTTPValidationError" in str(responses.get("422", "")):
                del responses["422"]
    schemas = schema.get("components", {}).get("schemas", {})
    for name in _FRAMEWORK_VALIDATION_SCHEMAS:
        schemas.pop(name, None)
    return schema
