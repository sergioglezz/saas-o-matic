"""Demo data: `python -m app.db.seed`, after `alembic upgrade head` (003 RF-10, 004 RF-8).

This is an entry point, like app.main, so it may use the upper layers: every demo customer
goes through the same schema and service as POST /customers (CA-10.3), and every demo
simulation through those of POST /simulations (004 CA-8.3). All data is invented:
synthetic tax ids and mailboxes of .example domains (RNF-5).
"""

from datetime import datetime

from sqlalchemy.orm import Session

from app.core.clock import utc_now
from app.db.session import create_db_engine, create_session_factory
from app.domain.errors import DuplicateTaxIdError
from app.repositories.customers import CustomerRepository
from app.repositories.simulations import SimulationRepository
from app.repositories.tax_rates import TaxRateRepository
from app.schemas.customers import CustomerCreate
from app.schemas.simulations import SimulationCreate
from app.services.customers import register_customer
from app.services.simulations import save_simulation


def _demo(company_name: str, tax_id: str, mailbox: str, country: str, plan: str) -> dict[str, str]:
    return {
        "company_name": company_name,
        "tax_id": tax_id,
        "contact_email": mailbox,
        "country": country,
        "plan": plan,
    }


# The 7 supported countries and the 3 plans (CA-10.1). The Spanish ones cover a CIF with a
# digit, a CIF with a letter and a DNI.
DEMO_CUSTOMERS: tuple[dict[str, str], ...] = (
    _demo("Acme Telecom S.L.", "B12345674", "compras@acme.example", "ES", "business"),
    _demo("Redes Ibéricas S.A.", "A11111119", "it@redesibericas.example", "ES", "enterprise"),
    _demo("Estudio Lucía Ferrer", "12345678Z", "lucia@estudioferrer.example", "ES", "starter"),
    _demo("Consorcio Digital del Norte", "P1234567D", "sistemas@cdn.example", "ES", "enterprise"),
    _demo("Lusitânia Cloud Lda", "PT123456789", "geral@lusitania.example", "PT", "starter"),
    _demo("Hexagone Réseaux SAS", "FR12345678901", "achats@hexagone.example", "FR", "business"),
    _demo("Nordwind Systeme GmbH", "DE123456789", "einkauf@nordwind.example", "DE", "enterprise"),
    _demo("Tirreno Fibra S.r.l.", "IT12345678901", "acquisti@tirreno.example", "IT", "starter"),
    _demo("Albion Connect Ltd", "GB123456789", "purchasing@albion.example", "GB", "business"),
    _demo("Liberty Mesh Inc.", "US123456789", "procurement@liberty.example", "US", "enterprise"),
)


# Spec 004 table 6.9: tax id of the demo customer, active users, storage in GB and API calls a
# month. They cover the three tiers and a country taxed at 0 % (CA-8.1).
DEMO_SIMULATIONS: tuple[tuple[str, int, int, int], ...] = (
    ("B12345674", 15, 200, 50_000),
    ("B12345674", 60, 500, 250_000),
    ("PT123456789", 1, 10, 1_000),
    ("DE123456789", 11, 100, 20_000),
    ("GB123456789", 100, 1_000, 1_000_000),
    ("US123456789", 51, 300, 100_000),
)


def seed_customers(session: Session, now: datetime) -> int:
    """Register the demo customers that do not exist yet; returns how many were created.

    A customer whose tax id is already taken is left untouched, so running the seed again
    changes nothing (CA-10.2, CA-10.4).
    """
    customers, rates = CustomerRepository(session), TaxRateRepository(session)
    created = 0
    for raw in DEMO_CUSTOMERS:
        new = CustomerCreate.model_validate(raw).to_new_customer()
        try:
            register_customer(new, customers, rates, now)
        except DuplicateTaxIdError:
            continue
        created += 1
    return created


def seed_simulations(session: Session, now: datetime) -> int:
    """Save the demo simulations of every demo customer that has none; returns how many.

    A customer with any simulation is left untouched, so running the seed again changes
    nothing, and a database seeded by spec 003 gets its simulations (CA-8.2, CA-8.4).
    """
    customers = CustomerRepository(session)
    simulations = SimulationRepository(session)
    rates = TaxRateRepository(session)
    created = 0
    for tax_id in dict.fromkeys(row[0] for row in DEMO_SIMULATIONS):  # in order, no repeats
        customer = customers.find_by_tax_id(tax_id)
        if customer is None or simulations.list_for_customer(customer.id, 1, 0).total > 0:
            continue
        for _, users, storage_gb, api_calls in (r for r in DEMO_SIMULATIONS if r[0] == tax_id):
            raw = {
                "customer_id": customer.id,
                "active_users": users,
                "storage_gb": storage_gb,
                "api_calls_per_month": api_calls,
            }
            new = SimulationCreate.model_validate(raw).to_new_simulation()
            save_simulation(new, customers, simulations, rates, now)
            created += 1
    return created


def main() -> None:
    engine = create_db_engine()
    try:
        with create_session_factory(engine)() as session:
            now = utc_now()
            created = seed_customers(session, now)
            simulations = seed_simulations(session, now)
    finally:
        engine.dispose()
    existing = len(DEMO_CUSTOMERS) - created
    print(f"Clientes de demostración: {created} creados, {existing} ya existían.")
    print(f"Simulaciones de demostración: {simulations} creadas.")


if __name__ == "__main__":
    main()
