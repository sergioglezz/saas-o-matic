"""ORM models. The Alembic migrations own the schema; these classes must mirror them."""

from sqlalchemy import CheckConstraint, Integer, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class TaxRate(Base):
    """Tax rate per country in basis points (spec 001 RF-4, RF-13; plan section 3)."""

    __tablename__ = "tax_rates"
    __table_args__ = (
        CheckConstraint("country GLOB '[A-Z][A-Z]'", name="ck_tax_rates_country_format"),
        # typeof() is needed because SQLite would otherwise store 21.5 in an INTEGER column.
        CheckConstraint(
            "typeof(rate_bp) = 'integer' AND rate_bp BETWEEN 0 AND 10000",
            name="ck_tax_rates_rate_bp_range",
        ),
    )

    country: Mapped[str] = mapped_column(Text, primary_key=True)
    rate_bp: Mapped[int] = mapped_column(Integer, nullable=False)
