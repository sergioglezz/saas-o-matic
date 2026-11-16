"""Data and helpers for the HTTP tests of the simulation routes (spec 004).

Every table of spec section 6 used by more than one test file is written here once (entry 20
of ai-review-log.md).
"""

import json
from dataclasses import dataclass
from datetime import UTC, datetime

from fastapi import FastAPI
from fastapi.testclient import TestClient
from httpx import Response
from sqlalchemy import text

from app.repositories.tax_rates import TaxRateRepository
from app.services.pricing import set_tax_rate
from tests.api.customer_requests import JSON, customer, post_customer

SIMULATIONS_PATH = "/simulations"
AT_10_00 = datetime(2026, 11, 16, 10, 0, 0, tzinfo=UTC)
AT_10_05 = datetime(2026, 11, 16, 10, 5, 0, tzinfo=UTC)

# Starting customers of spec section 6, created by the API in this order (ids 1 to 6).
STARTING_CUSTOMERS: list[tuple[str, str, str]] = [
    ("Acme Telecom S.L.", "B12345674", "ES"),
    ("Lusitânia Cloud Lda", "PT123456789", "PT"),
    ("Nordwind Systeme GmbH", "DE123456789", "DE"),
    ("Hexagone Réseaux SAS", "FR12345678901", "FR"),
    ("Albion Connect Ltd", "GB123456789", "GB"),
    ("Liberty Mesh Inc.", "US123456789", "US"),
]
COUNTRY_OF = {index: country for index, (_, _, country) in enumerate(STARTING_CUSTOMERS, 1)}

SI_1: dict[str, object] = {
    "customer_id": 1,
    "active_users": 15,
    "storage_gb": 200,
    "api_calls_per_month": 50_000,
}


def _tier(tier: int, from_users: int, to_users: int | None, units: int, price: int) -> object:
    return {
        "tier": tier,
        "from_users": from_users,
        "to_users": to_users,
        "units": units,
        "unit_price_cents": price,
        "amount_cents": units * price,
    }


# The 201 response of spec 004 section 5.
SI_1_RESPONSE: dict[str, object] = {
    "id": 1,
    **SI_1,
    "currency": "EUR",
    "tiers": [_tier(1, 1, 10, 10, 1000), _tier(2, 11, 50, 5, 800), _tier(3, 51, None, 0, 500)],
    "subtotal_cents": 14_000,
    "tax_rate_bp": 2100,
    "tax_cents": 2940,
    "total_cents": 16_940,
    "created_at": "2026-11-16T10:00:00Z",
}
SI_7_TIERS = [_tier(1, 1, 10, 10, 1000), _tier(2, 11, 50, 40, 800), _tier(3, 51, None, 10, 500)]


@dataclass(frozen=True)
class SavedCase:
    """One row of spec table 6.1."""

    case: str
    customer_id: int
    active_users: int
    subtotal_cents: int
    tax_rate_bp: int
    tax_cents: int
    total_cents: int
    storage_gb: int = 200
    api_calls_per_month: int = 50_000

    def body(self) -> dict[str, object]:
        return simulation(
            customer_id=self.customer_id,
            active_users=self.active_users,
            storage_gb=self.storage_gb,
            api_calls_per_month=self.api_calls_per_month,
        )


TABLE_6_1 = [
    SavedCase("SI-1", 1, 15, 14_000, 2100, 2940, 16_940),
    SavedCase("SI-2", 1, 0, 0, 2100, 0, 0),
    SavedCase("SI-3", 2, 1, 1000, 2300, 230, 1230),
    SavedCase("SI-4", 3, 11, 10_800, 1900, 2052, 12_852),
    SavedCase("SI-5", 6, 15, 14_000, 0, 0, 14_000),
    SavedCase("SI-6", 4, 51, 42_500, 2000, 8500, 51_000),
    SavedCase("SI-7", 1, 60, 47_000, 2100, 9870, 56_870),
    SavedCase("SI-8", 5, 100, 67_000, 2000, 13_400, 80_400),
    SavedCase("SI-9", 1, 100_000, 50_017_000, 2100, 10_503_570, 60_520_570, 1_000_000, 10**9),
]
CASE = {row.case: row for row in TABLE_6_1}


@dataclass
class SettableClock:
    """The "now" of the API in the simulation tests; a test moves it between requests."""

    now: datetime = AT_10_00


def simulation(*without: str, **changes: object) -> dict[str, object]:
    """SI-1 with some fields changed, added or (named in ``without``) removed."""
    return {key: value for key, value in {**SI_1, **changes}.items() if key not in without}


def post_simulation(
    client: TestClient,
    body: dict[str, object] | str,
    content_type: str | None = JSON,
    headers: dict[str, str] | None = None,
) -> Response:
    """POST a simulation; a dict is sent as JSON and a str exactly as written."""
    all_headers = dict(headers or {})
    if content_type is not None:
        all_headers["content-type"] = content_type
    raw = body if isinstance(body, str) else json.dumps(body)
    response: Response = client.post(
        SIMULATIONS_PATH, content=raw.encode("utf-8"), headers=all_headers
    )
    return response


def history_path(customer_id: int | str) -> str:
    return f"/customers/{customer_id}/simulations"


def create_starting_customers(client: TestClient) -> None:
    for company_name, tax_id, country in STARTING_CUSTOMERS:
        body = customer(company_name=company_name, tax_id=tax_id, country=country)
        assert post_customer(client, body).status_code == 201, company_name


def amounts(body: dict[str, object]) -> dict[str, object]:
    """The snapshot of a simulation or a quote: what both must share (CA-4.1)."""
    keys = ("currency", "tiers", "subtotal_cents", "tax_rate_bp", "tax_cents", "total_cents")
    return {key: body[key] for key in keys}


def saved_simulations(app: FastAPI) -> int:
    """Simulations in the database, counted without the history route."""
    with app.state.session_factory() as session:
        count: int = session.execute(text("SELECT count(*) FROM simulations")).scalar_one()
        return count


def change_rate(app: FastAPI, country: str, rate_bp: int | None) -> None:
    """Configure the tax rate of ``country`` (001 RF-13); ``None`` removes it."""
    with app.state.session_factory() as session:
        rates = TaxRateRepository(session)
        if rate_bp is None:
            rates.delete(country)
        else:
            set_tax_rate(country, rate_bp, rates)
        session.commit()
