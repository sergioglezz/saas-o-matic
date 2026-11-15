"""Helpers for the HTTP tests of POST /pricing/quote (spec 002).

Bodies are sent raw (exact bytes and Content-Type) so cases like 1e2, -0, repeated keys or a
missing Content-Type reach the API exactly as the spec tables write them.
"""

import json

from fastapi.testclient import TestClient
from httpx import Response

QUOTE_PATH = "/pricing/quote"
JSON = "application/json"

SPEC_SECTION_5_EXAMPLE: dict[str, object] = {
    "users": 15,
    "currency": "EUR",
    "tiers": [
        {
            "tier": 1,
            "from_users": 1,
            "to_users": 10,
            "units": 10,
            "unit_price_cents": 1000,
            "amount_cents": 10000,
        },
        {
            "tier": 2,
            "from_users": 11,
            "to_users": 50,
            "units": 5,
            "unit_price_cents": 800,
            "amount_cents": 4000,
        },
        {
            "tier": 3,
            "from_users": 51,
            "to_users": None,
            "units": 0,
            "unit_price_cents": 500,
            "amount_cents": 0,
        },
    ],
    "subtotal_cents": 14000,
    "tax_rate_bp": 2100,
    "tax_cents": 2940,
    "total_cents": 16940,
}


def post_quote(
    client: TestClient,
    body: str | bytes,
    content_type: str | None = JSON,
    headers: dict[str, str] | None = None,
) -> Response:
    """POST the raw body; content_type=None sends no Content-Type header at all."""
    all_headers = dict(headers or {})
    if content_type is not None:
        all_headers["content-type"] = content_type
    content = body.encode("utf-8") if isinstance(body, str) else body
    response: Response = client.post(QUOTE_PATH, content=content, headers=all_headers)
    return response


def details_of(response: Response) -> set[tuple[str, str]]:
    """The error details as a set of (field, message): the spec compares them as a set."""
    return {(d["field"], d["message"]) for d in response.json()["error"]["details"]}


def _no_floats(literal: str) -> float:
    raise AssertionError(f"number with decimals or exponent in the response: {literal}")


def json_without_floats(response: Response) -> object:
    """Parse the body and fail if any number has decimals or an exponent (O-9)."""
    return json.loads(response.text, parse_float=_no_floats)
