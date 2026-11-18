"""Reading the request body without a server (level U): spec 002 RF-7, task T-10.

Covers CA-7.1 to CA-7.3 with cases E-37 to E-42, O-1, O-2 and O-15. The requests are built by
hand as Starlette sees them, so the exact bytes and headers of each case are under control.
"""

import asyncio

import pytest
from starlette.requests import Request
from starlette.types import Message

from app.api.validation import read_json_object
from app.core.errors import ApiError, FieldError

VALID_BODY = b'{"users": 15, "country": "ES"}'
# Deeper than the JSON parser can go: it gives up with RecursionError instead of a JSON error.
TOO_DEEP_BODY = b'{"users": ' + b"[" * 100_000 + b"]" * 100_000 + b', "country": "ES"}'
BODY_ERROR = FieldError(field="body", message="El cuerpo debe ser un objeto JSON")


def _request(body: bytes, content_type: str | None) -> Request:
    headers = [] if content_type is None else [(b"content-type", content_type.encode("latin-1"))]

    async def receive() -> Message:
        return {"type": "http.request", "body": body, "more_body": False}

    return Request({"type": "http", "method": "POST", "path": "/", "headers": headers}, receive)


def _read(body: bytes, content_type: str | None) -> dict[str, object]:
    return asyncio.run(read_json_object(_request(body, content_type)))


@pytest.mark.parametrize(
    ("body", "content_type"),
    [
        pytest.param(b"no es json", "application/json", id="E-37"),
        pytest.param(b'[15, "ES"]', "application/json", id="E-38"),
        pytest.param(b"null", "application/json", id="E-39"),
        pytest.param(b"", "application/json", id="E-40"),
        pytest.param(VALID_BODY, "text/plain", id="E-41"),
        pytest.param(VALID_BODY, None, id="E-42"),
        pytest.param(b"15", "application/json", id="number"),
        pytest.param(b'"ES"', "application/json", id="string"),
        pytest.param(b"\xff\xfe", "application/json", id="not-utf-8"),
        pytest.param(VALID_BODY, "application/jsonx", id="similar-media-type"),
        pytest.param(TOO_DEEP_BODY, "application/json", id="too-deep"),
    ],
)
def test_anything_but_a_json_object_with_json_content_type_is_rejected(
    body: bytes, content_type: str | None
) -> None:
    """CA-7.2: 422 validation_error with the single detail body / BODY."""
    with pytest.raises(ApiError) as error:
        _read(body, content_type)

    assert (error.value.status, error.value.code) == (422, "validation_error")
    assert error.value.message == "Datos no válidos"
    assert error.value.details == [BODY_ERROR]


@pytest.mark.parametrize(
    "content_type",
    [
        pytest.param("application/json", id="plain"),
        pytest.param("application/json; charset=utf-8", id="O-1"),
        pytest.param("Application/JSON", id="O-15"),
        pytest.param("application/json;charset=UTF-8", id="no-space"),
    ],
)
def test_json_object_is_read_whatever_the_media_type_case_or_charset(content_type: str) -> None:
    """CA-7.1: application/json, case-insensitive, with or without charset."""
    assert _read(VALID_BODY, content_type) == {"users": 15, "country": "ES"}


def test_repeated_key_keeps_the_last_value() -> None:
    """O-2, CA-7.3: with a repeated key the last value wins."""
    body = b'{"users": 1, "users": 15, "country": "ES"}'

    assert _read(body, "application/json") == {"users": 15, "country": "ES"}
