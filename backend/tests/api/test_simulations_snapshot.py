"""The snapshot does not change after saving (level I), spec 004 task T-09.

RF-4 (CA-4.3 to CA-4.5) with cases SN-3 to SN-5 of table 6.2: the tax rates change through the
rate configuration of spec 001 (RF-13) between requests.
"""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from tests.api.simulation_requests import (
    CASE,
    SI_1,
    SettableClock,
    change_rate,
    create_starting_customers,
    history_path,
    post_simulation,
)


@pytest.fixture
def client_with_customers(client: TestClient, simulation_clock: SettableClock) -> TestClient:
    create_starting_customers(client)
    return client


def _tax(body: dict[str, object]) -> tuple[object, object, object]:
    return body["tax_rate_bp"], body["tax_cents"], body["total_cents"]


def test_sn_3_history_keeps_the_rate_it_was_saved_with(
    app: FastAPI, client_with_customers: TestClient
) -> None:
    """SN-3, CA-4.3: the ES rate goes to 2150 and the saved SI-1 keeps 2100."""
    saved = post_simulation(client_with_customers, SI_1).json()
    change_rate(app, "ES", 2150)

    items = client_with_customers.get(history_path(1)).json()["items"]

    assert items == [saved]
    assert _tax(items[0]) == (2100, 2940, 16_940)


def test_sn_4_a_new_simulation_uses_the_new_rate(
    app: FastAPI, client_with_customers: TestClient
) -> None:
    """SN-4, CA-4.3 (001 CA-13.2): after SN-3, SI-1 again costs 2150, 3010 and 17010."""
    post_simulation(client_with_customers, SI_1)
    change_rate(app, "ES", 2150)

    newer = post_simulation(client_with_customers, SI_1).json()
    items = client_with_customers.get(history_path(1)).json()["items"]

    assert _tax(newer) == (2150, 3010, 17_010)
    assert [_tax(item) for item in items] == [(2150, 3010, 17_010), (2100, 2940, 16_940)]


def test_sn_5_history_survives_the_country_losing_its_rate(
    app: FastAPI, client_with_customers: TestClient
) -> None:
    """SN-5, CA-4.4, CA-4.5, spec decision D-4: the PT simulation is read as it was saved."""
    saved = post_simulation(client_with_customers, CASE["SI-3"].body()).json()
    change_rate(app, "PT", None)

    response = client_with_customers.get(history_path(2))

    assert response.status_code == 200
    assert response.json() == {"items": [saved], "total": 1}
