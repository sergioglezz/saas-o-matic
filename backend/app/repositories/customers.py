"""Access to the customers table: the only module that reads or writes it (spec 003 RNF-1).

Unlike the tax rate repository, ``add`` commits by itself: registering a customer is a single
write, and the API must know whether it succeeded before it answers (plan 003 DT-5).
"""

from sqlalchemy import ColumnElement, func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.models import CustomerRecord
from app.domain.customers import Customer, CustomerPage, NewCustomer
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

    def find_by_tax_id(self, tax_id: str) -> Customer | None:
        """The customer whose normalized tax id is exactly ``tax_id``, or None.

        Used by the demo seed to find its customers again (spec 004 CA-8.2, plan DT-13).
        """
        record = self._session.scalar(select(CustomerRecord).where(CustomerRecord.tax_id == tax_id))
        return _to_customer(record) if record is not None else None

    def search(
        self, name_fragment: str, tax_id_fragment: str, limit: int, offset: int
    ) -> CustomerPage:
        """Customers whose name or tax id contains a fragment, ordered by name and then id.

        ``name_fragment`` must come casefolded and ``tax_id_fragment`` normalized; an empty
        fragment is not searched, and with both empty every customer matches (CA-5.2, CA-5.3).
        instr() looks for literal text, so "%" and "_" are not wildcards (CA-5.4).
        """
        folded_name = func.casefold(CustomerRecord.company_name)
        conditions: list[ColumnElement[bool]] = []
        if name_fragment:
            conditions.append(func.instr(folded_name, name_fragment) > 0)
        if tax_id_fragment:
            conditions.append(func.instr(CustomerRecord.tax_id, tax_id_fragment) > 0)
        count = select(func.count()).select_from(CustomerRecord)
        page = select(CustomerRecord).order_by(folded_name, CustomerRecord.id)
        if conditions:
            count, page = count.where(or_(*conditions)), page.where(or_(*conditions))
        records = self._session.scalars(page.limit(limit).offset(offset)).all()
        return CustomerPage(
            items=tuple(_to_customer(record) for record in records),
            total=self._session.scalar(count) or 0,
        )


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
