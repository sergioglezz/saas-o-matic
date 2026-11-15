"""ORM models. The Alembic migrations own the schema; these classes must mirror them."""

from sqlalchemy import CheckConstraint, Index, Integer, Text, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from app.domain.customers import PLANS


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


class CustomerRecord(Base):
    """A registered customer (spec 003 RF-9; 00-spec-first 8.5; plan section 3)."""

    __tablename__ = "customers"
    __table_args__ = (
        UniqueConstraint("tax_id", name="uq_customers_tax_id"),
        CheckConstraint(
            "length(company_name) BETWEEN 1 AND 120", name="ck_customers_company_name_length"
        ),
        CheckConstraint("country GLOB '[A-Z][A-Z]'", name="ck_customers_country_format"),
        CheckConstraint(
            f"plan IN ({', '.join(repr(plan) for plan in PLANS)})", name="ck_customers_plan"
        ),
        Index("ix_customers_company_name", "company_name"),
        # AUTOINCREMENT: an id is never reused, not even after deleting the last row (CA-1.3).
        {"sqlite_autoincrement": True},
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    company_name: Mapped[str] = mapped_column(Text, nullable=False)
    tax_id: Mapped[str] = mapped_column(Text, nullable=False)
    contact_email: Mapped[str] = mapped_column(Text, nullable=False)
    country: Mapped[str] = mapped_column(Text, nullable=False)
    plan: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[str] = mapped_column(Text, nullable=False)
