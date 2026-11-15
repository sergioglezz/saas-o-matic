"""Helpers for the HTTP tests of the customer routes (spec 003)."""

import json
from datetime import UTC, datetime

from fastapi.testclient import TestClient
from httpx import Response

CUSTOMERS_PATH = "/customers"
JSON = "application/json"

# The instant of the examples of spec 003 section 5; the fixed_clock fixture freezes it.
FIXED_NOW = datetime(2026, 11, 13, 10, 0, 0, tzinfo=UTC)

AL_1: dict[str, object] = {
    "company_name": "Acme Telecom S.L.",
    "tax_id": "B12345674",
    "contact_email": "compras@acme.example",
    "country": "ES",
    "plan": "business",
}
AL_1_RESPONSE: dict[str, object] = {"id": 1, **AL_1, "created_at": "2026-11-13T10:00:00Z"}

# The six customers of spec table 6.6, in creation order (ids 1 to 6).
TABLE_6_6_CUSTOMERS = [
    ("Zeta Redes S.A.", "A00000000", "ES"),
    ("acme telecom s.l.", "B12345674", "ES"),
    ("COMPAÑÍA Ñandú", "12345678Z", "ES"),
    ("Telefónica Demo", "PT123456789", "PT"),
    ("100% Fibra GmbH", "DE1234567", "DE"),
    ("Acme Cloud Ltd", "GB7654321", "GB"),
]


def customer(*without: str, **changes: object) -> dict[str, object]:
    """AL-1 with some fields changed, added or (named in ``without``) removed."""
    return {key: value for key, value in {**AL_1, **changes}.items() if key not in without}


def post_customer(
    client: TestClient,
    body: dict[str, object] | str,
    content_type: str | None = JSON,
    headers: dict[str, str] | None = None,
) -> Response:
    """POST a customer; a dict is sent as JSON and a str exactly as written."""
    all_headers = dict(headers or {})
    if content_type is not None:
        all_headers["content-type"] = content_type
    raw = body if isinstance(body, str) else json.dumps(body)
    response: Response = client.post(
        CUSTOMERS_PATH, content=raw.encode("utf-8"), headers=all_headers
    )
    return response


def create_table_6_6(client: TestClient) -> None:
    for company_name, tax_id, country in TABLE_6_6_CUSTOMERS:
        body = customer(company_name=company_name, tax_id=tax_id, country=country)
        assert post_customer(client, body).status_code == 201, company_name


def total_customers(client: TestClient) -> int:
    total: int = client.get(CUSTOMERS_PATH).json()["total"]
    return total
