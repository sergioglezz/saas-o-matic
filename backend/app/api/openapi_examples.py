"""Building blocks of the documented responses in /docs, shared by the routes' docs modules.

Every documented error shows the single format {"error": {code, message, details}} (spec 002
RF-6), the same that the API answers.
"""

from typing import Any

from app.core.errors import VALIDATION_ERROR_MESSAGE

Responses = dict[int | str, dict[str, Any]]


def json_example(description: str, example: object) -> dict[str, Any]:
    return {"description": description, "content": {"application/json": {"example": example}}}


def error_example(code: str, message: str, details: list[dict[str, str]]) -> dict[str, object]:
    return {"error": {"code": code, "message": message, "details": details}}


def invalid_example(field: str, message: str) -> dict[str, Any]:
    """A documented 422 with one field detail."""
    details = [{"field": field, "message": message}]
    return json_example(
        "Datos no válidos", error_example("validation_error", VALIDATION_ERROR_MESSAGE, details)
    )
