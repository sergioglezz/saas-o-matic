"""Access to the customers table: the only module that reads or writes it (spec 003 RNF-1).

Unlike the tax rate repository, ``add`` commits by itself: registering a customer is a single
write, and the API must know whether it succeeded before it answers (plan 003 DT-5).
"""

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.models import CustomerRecord
from app.domain.customers import Customer, NewCustomer
from app.domain.errors import DuplicateTaxIdError

# How SQLite names the violated constraint in its error (checked in plan 003 section 10).
_TAX_ID_UNIQUE_VIOLATION = "customers.tax_id"


class CustomerRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, new: NewCustomer, created_at: str) -> Customer:
        """Save ``new`` and return it with its id. Raises DuplicateTaxIdError.

        The unique constraint is the only judge of a repeated tax id, so two registrations at
        the same time cannot both pass (CA-4.4, plan 003 DT-4).
        """
        record = CustomerRecord(
            company_name=new.company_name,
            tax_id=new.tax_id,
            contact_email=new.contact_email,
            country=new.country,
            plan=new.plan,
            created_at=created_at,
        )
        self._session.add(record)
        try:
            self._session.commit()
        except IntegrityError as error:
            self._session.rollback()
            if _TAX_ID_UNIQUE_VIOLATION in str(error.orig):
                raise DuplicateTaxIdError(new.tax_id) from None
            raise
        return _to_customer(record)

    def get(self, customer_id: int) -> Customer | None:
        record = self._session.get(CustomerRecord, customer_id)
        return _to_customer(record) if record is not None else None


def _to_customer(record: CustomerRecord) -> Customer:
    return Customer(
        id=record.id,
        company_name=record.company_name,
        tax_id=record.tax_id,
        contact_email=record.contact_email,
        country=record.country,
        plan=record.plan,
        created_at=record.created_at,
    )
