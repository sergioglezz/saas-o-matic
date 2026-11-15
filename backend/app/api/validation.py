"""Request reading and validation errors shared by the API routes (spec 002 RF-2, RF-5, RF-6).

Pydantic reports several errors per field in its own format; the spec wants one detail per
field with fixed Spanish messages (CA-6.3). This module does that translation.
"""

from collections.abc import Mapping

from pydantic import ValidationError

from app.core.errors import FieldError

REQUIRED_MESSAGE = "Campo obligatorio"
NOT_ALLOWED_MESSAGE = "Campo no permitido"


def field_errors(error: ValidationError, invalid_messages: Mapping[str, str]) -> list[FieldError]:
    """One FieldError per field: missing, not allowed, or the field's own invalid message."""
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
            message = invalid_messages[field]
        details[field] = FieldError(field=field, message=message)
    return list(details.values())
