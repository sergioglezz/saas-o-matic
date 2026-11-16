"""Valid saves and the snapshot over HTTP (level I), spec 004 task T-07.

RF-1 (CA-1.1, CA-1.2, CA-1.6; CA-1.3 is HI-9 in T-09) and RF-4 (CA-4.1, CA-4.6,
CA-4.7) with cases SI-1 to SI-13 (table 6.1), SN-1 and SN-2 (table 6.2). The clock is fixed
at 2026-11-16T10:00:00Z.
"""

import pytest
from fastapi.testclient import TestClient

from tests.api.customer_requests import CUSTOMERS_PATH
from tests.api.simulation_requests import (
    CASE,
    COUNTRY_OF,
    SI_1,
    SI_1_RESPONSE,
    SI_7_TIERS,
    TABLE_6_1,
    SavedCase,
    SettableClock,
    amounts,
    create_starting_customers,
    post_simulation,
    simulation,
)

TABLE_6_1_PARAMS = [pytest.param(row, id=row.case) for row in TABLE_6_1]


@pytest.fixture
def client_with_customers(client: TestClient, simulation_clock: SettableClock) -> TestClient:
    create_starting_customers(client)
    return client


def test_si_1_returns_exactly_the_response_of_section_5(client_with_customers: TestClient) -> None:
    """SI-1, CA-1.1, CA-4.7: 201 with the exact body of section 5, as JSON and without
    Location (spec decision D-11)."""
    response = post_simulation(client_with_customers, SI_1)

    assert response.status_code == 201
    assert response.json() == SI_1_RESPONSE
    assert response.headers["content-type"].startswith("application/json")
    assert "location" not in response.headers


@pytest.mark.parametrize("row", TABLE_6_1_PARAMS)
def test_table_6_1_amounts(client_with_customers: TestClient, row: SavedCase) -> None:
    """SI-1 to SI-9, CA-1.1, CA-3.3: the amounts of the customer's country, in cents."""
    response = post_simulation(client_with_customers, row.body())

    assert response.status_code == 201
    body = response.json()
    assert body["customer_id"] == row.customer_id
    assert body["active_users"] == row.active_users
    assert (body["storage_gb"], body["api_calls_per_month"]) == (
        row.storage_gb,
        row.api_calls_per_month,
    )
    assert (body["subtotal_cents"], body["tax_rate_bp"]) == (row.subtotal_cents, row.tax_rate_bp)
    assert (body["tax_cents"], body["total_cents"]) == (row.tax_cents, row.total_cents)
    assert "users" not in body


def test_si_2_has_three_tiers_with_no_units(client_with_customers: TestClient) -> None:
    """SI-2, CA-4.7: zero users still lists the three tiers, all at 0."""
    tiers = post_simulation(client_with_customers, CASE["SI-2"].body()).json()["tiers"]

    assert [(tier["units"], tier["amount_cents"]) for tier in tiers] == [(0, 0)] * 3
    assert tiers[2]["to_users"] is None


def test_si_7_splits_the_users_across_the_three_tiers(client_with_customers: TestClient) -> None:
    """SI-7, RN-1: 60 users are 10, 40 and 10 users in tiers 1, 2 and 3."""
    tiers = post_simulation(client_with_customers, CASE["SI-7"].body()).json()["tiers"]

    assert tiers == SI_7_TIERS


def test_si_10_accepts_zero_storage_and_zero_calls(client_with_customers: TestClient) -> None:
    """SI-10, CA-2.3, CA-2.4: 0 is a valid amount of storage and of API calls."""
    response = post_simulation(
        client_with_customers, simulation(storage_gb=0, api_calls_per_month=0)
    )

    assert response.status_code == 201


def test_si_11_numbers_the_simulations(client_with_customers: TestClient) -> None:
    """SI-11, CA-1.2: two saves in a row get ids 1 and 2."""
    first = post_simulation(client_with_customers, SI_1).json()
    second = post_simulation(client_with_customers, SI_1).json()

    assert (first["id"], second["id"]) == (1, 2)


def test_si_12_minus_zero_users_is_zero(client_with_customers: TestClient) -> None:
    """SI-12, CA-2.2 (002 CA-2.1): -0 is saved as 0, with the amounts of SI-2."""
    raw = '{"customer_id": 1, "active_users": -0, "storage_gb": 200, "api_calls_per_month": 50000}'

    body = post_simulation(client_with_customers, raw).json()

    assert body["active_users"] == 0
    assert body["total_cents"] == 0


def test_si_13_saving_does_not_change_the_customer(client_with_customers: TestClient) -> None:
    """SI-13, CA-1.6: the detail and the list are the same before and after saving."""
    before = (
        client_with_customers.get(f"{CUSTOMERS_PATH}/1").json(),
        client_with_customers.get(CUSTOMERS_PATH).json(),
    )

    assert post_simulation(client_with_customers, SI_1).status_code == 201

    after = (
        client_with_customers.get(f"{CUSTOMERS_PATH}/1").json(),
        client_with_customers.get(CUSTOMERS_PATH).json(),
    )
    assert after == before


@pytest.mark.parametrize("row", TABLE_6_1_PARAMS)
def test_sn_1_snapshot_is_the_quote(client_with_customers: TestClient, row: SavedCase) -> None:
    """SN-1, CA-4.1, RNF-2: the same snapshot as POST /pricing/quote for the customer's country."""
    quote = client_with_customers.post(
        "/pricing/quote",
        json={"users": row.active_users, "country": COUNTRY_OF[row.customer_id]},
    ).json()

    saved = post_simulation(client_with_customers, row.body()).json()

    assert amounts(saved) == amounts(quote)


def test_sn_2_storage_and_calls_do_not_change_the_price(client_with_customers: TestClient) -> None:
    """SN-2, CA-4.6 (RN-9): three usages, the same amounts."""
    usages = ((200, 50_000), (0, 0), (1_000_000, 1_000_000_000))

    saved = [
        post_simulation(
            client_with_customers, simulation(storage_gb=storage, api_calls_per_month=calls)
        ).json()
        for storage, calls in usages
    ]

    assert amounts(saved[0]) == amounts(saved[1]) == amounts(saved[2])
