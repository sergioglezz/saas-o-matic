"""Demo data: `python -m app.db.seed`, after `alembic upgrade head` (spec 003 RF-10).

This is an entry point, like app.main, so it may use the upper layers: every demo customer
goes through the same schema and service as POST /customers (CA-10.3). All data is invented:
synthetic tax ids and mailboxes of .example domains (RNF-5).
"""

from datetime import datetime

from sqlalchemy.orm import Session

from app.core.clock import utc_now
from app.db.session import create_db_engine, create_session_factory
from app.domain.errors import DuplicateTaxIdError
from app.repositories.customers import CustomerRepository
from app.repositories.tax_rates import TaxRateRepository
from app.schemas.customers import CustomerCreate
from app.services.customers import register_customer


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


def main() -> None:
    engine = create_db_engine()
    try:
        with create_session_factory(engine)() as session:
            created = seed_customers(session, utc_now())
    finally:
        engine.dispose()
    existing = len(DEMO_CUSTOMERS) - created
    print(f"Clientes de demostración: {created} creados, {existing} ya existían.")


if __name__ == "__main__":
    main()
