"""POST /customers over HTTP (level I), spec 003 tasks T-12 and T-13.

Covers RF-1 (CA-1.1 to CA-1.3, CA-1.5), RF-2, RF-3 and RF-4 with tables 6.3 (AL), 6.4 (VA) and
6.5 (CO). AL-4 lives in test_customers_detail.py, next to the two reads it needs.
"""

import re

import pytest
from fastapi.testclient import TestClient
from httpx import Response
from sqlalchemy import Engine, text

from tests.api.customer_requests import AL_1, AL_1_RESPONSE, customer, post_customer
from tests.api.quote_requests import details_of
from tests.unit.test_customer_schema import TABLE_6_4

NSP = "País no soportado"
TID = "Debe tener entre 5 y 20 letras o dígitos"
PLN = "Debe ser starter, business o enterprise"
EML = "Debe ser un email válido"
DUP = "Ya existe un cliente con este identificador"

# The rows of table 6.4 that need the tax rates of the database; the others are shared with
# the unit tests of the schema, which check the same data without a server.
TABLE_6_4_WITH_DATABASE: list[tuple[str, dict[str, object], set[tuple[str, str]]]] = [
    ("VA-17", customer(country="XX"), {("country", NSP)}),
    ("VA-26", customer(country="XX", tax_id="12"), {("country", NSP), ("tax_id", TID)}),
    ("VA-27", customer(country="xx", plan="x"), {("country", NSP), ("plan", PLN)}),
]

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


@pytest.mark.parametrize(
    ("payload", "expected"),
    [
        pytest.param(payload, expected, id=case_id)
        for case_id, payload, expected in [*TABLE_6_4, *TABLE_6_4_WITH_DATABASE]
    ],
)
def test_invalid_customers_return_422_and_save_nothing(
    client: TestClient,
    migrated_engine: Engine,
    payload: dict[str, object],
    expected: set[tuple[str, str]],
) -> None:
    """VA-1 to VA-27; CA-1.5, CA-2.1 to CA-2.7, CA-2.9, CA-3.2, CA-3.3, CA-3.7 to CA-3.9."""
    response = post_customer(client, payload)

    assert response.status_code == 422
    error = response.json()["error"]
    assert (error["code"], error["message"]) == ("validation_error", "Datos no válidos")
    assert details_of(response) == expected
    assert len(error["details"]) == len(expected)  # one element per field (CA-2.9)
    assert _stored_customers(migrated_engine) == 0


@pytest.mark.parametrize(
    ("body", "content_type"),
    [
        pytest.param("no es json", "application/json", id="VA-28-not-json"),
        pytest.param("[1]", "application/json", id="VA-28-a-list"),
        pytest.param('{"company_name": "Acme"}', "text/plain", id="VA-28-text-plain"),
    ],
)
def test_a_body_that_is_not_a_json_object_is_rejected(
    client: TestClient, body: str, content_type: str
) -> None:
    """VA-28, CA-2.8: the same rule and the same detail as the quote (002 RF-7)."""
    response = post_customer(client, body, content_type=content_type)

    assert response.status_code == 422
    assert details_of(response) == {("body", "El cuerpo debe ser un objeto JSON")}


def _assert_conflict(response: Response) -> None:
    assert response.status_code == 409
    assert response.headers["content-type"].startswith("application/json")
    assert response.json() == {
        "error": {
            "code": "conflict",
            "message": "El recurso ya existe",
            "details": [{"field": "tax_id", "message": DUP}],
        }
    }


def test_the_same_customer_twice_is_a_conflict(client: TestClient, migrated_engine: Engine) -> None:
    """CO-1, CA-4.1, CA-1.5: the second registration answers 409 and stores nothing."""
    assert post_customer(client, AL_1).status_code == 201

    _assert_conflict(post_customer(client, AL_1))
    assert _stored_customers(migrated_engine) == 1


def test_tax_ids_are_compared_normalized(client: TestClient) -> None:
    """CO-2, CA-4.2: 12.345.678-z collides with 12345678Z."""
    assert post_customer(client, customer(tax_id="12345678Z")).status_code == 201

    _assert_conflict(post_customer(client, customer(company_name="Otra", tax_id="12.345.678-z")))


def test_uniqueness_does_not_depend_on_the_country(client: TestClient) -> None:
    """CO-3, CA-4.1: the same tax id in another country is still a conflict (decision D-14)."""
    assert post_customer(client, AL_1).status_code == 201

    _assert_conflict(post_customer(client, customer(country="FR")))


def test_validation_errors_go_before_the_conflict(client: TestClient) -> None:
    """CO-4, CA-4.3: an invalid request answers 422 and never mentions the conflict."""
    assert post_customer(client, AL_1).status_code == 201

    response = post_customer(client, customer(contact_email="x"))

    assert response.status_code == 422
    assert details_of(response) == {("contact_email", EML)}
