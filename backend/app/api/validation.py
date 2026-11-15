"""Request reading and validation errors shared by the API routes (spec 002 RF-2, RF-5, RF-6).

Pydantic reports several errors per field in its own format; the spec wants one detail per
field with fixed Spanish messages (CA-6.3). This module does that translation.
"""

import json
from collections.abc import Mapping

from fastapi import Request
from pydantic import ValidationError

from app.core.errors import VALIDATION_ERROR_MESSAGE, ApiError, FieldError, InvalidFieldError

REQUIRED_MESSAGE = "Campo obligatorio"
NOT_ALLOWED_MESSAGE = "Campo no permitido"
BODY_INVALID_MESSAGE = "El cuerpo debe ser un objeto JSON"
JSON_MEDIA_TYPE = "application/json"


def validation_error(details: list[FieldError]) -> ApiError:
    """422 validation_error with the given field details (CA-6.1, CA-6.2)."""
    return ApiError(
        status=422, code="validation_error", message=VALIDATION_ERROR_MESSAGE, details=details
    )


async def read_json_object(request: Request) -> dict[str, object]:
    """The request body as a JSON object (RF-7), read by hand on purpose (plan 002 DT-1).

    Media types are case-insensitive and may carry a charset (CA-7.1). With a repeated key,
    json.loads keeps the last value (CA-7.3). Anything else raises 422 body/BODY (CA-7.2).
    """
    media_type = request.headers.get("content-type", "").split(";", 1)[0].strip().lower()
    if media_type != JSON_MEDIA_TYPE:
        raise _body_error()
    try:
        data = json.loads((await request.body()).decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        raise _body_error() from None
    if not isinstance(data, dict):
        raise _body_error()
    return data


def _body_error() -> ApiError:
    return validation_error([FieldError(field="body", message=BODY_INVALID_MESSAGE)])


def field_errors(error: ValidationError, invalid_messages: Mapping[str, str]) -> list[FieldError]:
    """One FieldError per field: missing, not allowed, or the field's own invalid message.

    A validator that raised InvalidFieldError chose its own message (spec 003 RF-3).
    """
    details: dict[str, FieldError] = {}
    for item in error.errors():
        field = str(item["loc"][0])
        if field in details:
            continue
        if item["type"] == "missing":
            message = REQUIRED_MESSAGE
        elif item["type"] == "extra_forbidden":
            message = NOT_ALLOWED_MESSAGE
        else:
            raised = item.get("ctx", {}).get("error")
            own_message = raised.message if isinstance(raised, InvalidFieldError) else None
            message = own_message or invalid_messages[field]
        details[field] = FieldError(field=field, message=message)
    return list(details.values())
