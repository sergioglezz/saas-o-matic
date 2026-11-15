"""Access to the tax_rates table: the only module that reads or writes it (plan section 2).

The caller owns the transaction (it commits or rolls back). Writes are flushed immediately so a
database constraint fails at the call that broke it, not at a later commit.
"""

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.db.models import TaxRate


class TaxRateRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def get_rate_bp(self, country: str) -> int | None:
        """Rate for the exact country code, or None if it has none (CA-4.7: no normalising)."""
        return self._session.scalar(select(TaxRate.rate_bp).where(TaxRate.country == country))

    def upsert(self, country: str, rate_bp: int) -> None:
        self._session.merge(TaxRate(country=country, rate_bp=rate_bp))
        self._session.flush()

    def delete(self, country: str) -> None:
        self._session.execute(delete(TaxRate).where(TaxRate.country == country))
        self._session.flush()
