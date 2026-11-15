"""POST /customers over HTTP (level I), spec 003 tasks T-12 and T-13.

Covers RF-1 (CA-1.1 to CA-1.3, CA-1.5), RF-2, RF-3 and RF-4 with tables 6.3 (AL), 6.4 (VA) and
6.5 (CO). AL-4 lives in test_customers_detail.py, next to the two reads it needs.
"""

import re

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import Engine, text

from tests.api.customer_requests import AL_1, AL_1_RESPONSE, customer, post_customer

DOMAIN_189 = ".".join(["d" * 63, "d" * 63, "d" * 58, "es"])
EMAIL_254 = "l" * 64 + "@" + DOMAIN_189


def _stored_customers(engine: Engine) -> int:
    with engine.connect() as connection:
        count: int = connection.execute(text("SELECT count(*) FROM customers")).scalar_one()
    return count


@pytest.mark.usefixtures("fixed_clock")
def test_registering_the_example_returns_exactly_the_contract(client: TestClient) -> None:
    """AL-1, CA-1.1, CA-1.3: 201 with the response of spec section 5, and nothing else."""
    response = post_customer(client, AL_1)

    assert response.status_code == 201
    assert response.headers["content-type"].startswith("application/json")
    assert response.json() == AL_1_RESPONSE
    assert "location" not in response.headers  # spec decision D-8


@pytest.mark.usefixtures("fixed_clock")
def test_values_are_saved_and_returned_normalized(client: TestClient) -> None:
    """AL-2, CA-1.2: spaces, case and separators cleaned; same result as AL-1."""
    response = post_customer(
        client,
        {
            "company_name": "  Acme   Telecom  S.L. ",
            "tax_id": "b-12.345.674",
            "contact_email": " compras@acme.example ",
            "country": " es ",
            "plan": "business",
        },
    )

    assert response.status_code == 201
    assert response.json() == AL_1_RESPONSE


def test_ids_grow_one_by_one(client: TestClient, migrated_engine: Engine) -> None:
    """AL-3, CA-1.3: two registrations get ids 1 and 2, and both are stored."""
    first = post_customer(client, AL_1)
    second = post_customer(client, customer(tax_id="12345678Z"))

    assert (first.json()["id"], second.json()["id"]) == (1, 2)
    assert _stored_customers(migrated_engine) == 2


def test_created_at_is_the_current_instant_in_utc_text(client: TestClient) -> None:
    """CA-1.3: with the real clock, ISO 8601 with seconds and the Z suffix."""
    created_at = post_customer(client, AL_1).json()["created_at"]

    assert re.fullmatch(
        r"20[0-9]{2}-[01][0-9]-[0-3][0-9]T[0-2][0-9]:[0-5][0-9]:[0-5][0-9]Z", created_at
    )


@pytest.mark.parametrize(
    "changes",
    [
        pytest.param({"country": "PT", "tax_id": "PT123456789", "plan": "starter"}, id="AL-5"),
        pytest.param({"tax_id": "12345678Z", "plan": "enterprise"}, id="AL-6"),
        pytest.param({"company_name": "x" * 120}, id="AL-7"),
        pytest.param({"contact_email": EMAIL_254}, id="AL-8"),
    ],
)
def test_valid_customers_of_table_6_3_are_registered(
    client: TestClient, changes: dict[str, object]
) -> None:
    """AL-5 to AL-8, CA-1.1, CA-2.1, CA-2.2, CA-2.4, CA-3.8: 201 with the values sent."""
    assert len(EMAIL_254) == 254
    response = post_customer(client, customer(**changes))

    assert response.status_code == 201
    assert response.json() == {
        **AL_1_RESPONSE,
        **changes,
        "created_at": response.json()["created_at"],
    }


@pytest.mark.parametrize("country", ["ES", "PT", "FR", "DE", "IT", "GB", "US"])
def test_a_customer_of_every_supported_country_is_registered(
    client: TestClient, country: str
) -> None:
    """AL-9, CA-2.3: the seven countries with a tax rate are accepted."""
    tax_id = "B12345674" if country == "ES" else f"{country}1234567"
    response = post_customer(client, customer(country=country.lower(), tax_id=tax_id))

    assert response.status_code == 201
    assert response.json()["country"] == country
