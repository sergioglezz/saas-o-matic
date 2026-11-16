"""ORM models. The Alembic migrations own the schema; these classes must mirror them."""

from sqlalchemy import (
    CheckConstraint,
    ForeignKey,
    Index,
    Integer,
    PrimaryKeyConstraint,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from app.domain.customers import PLANS
from app.domain.pricing import MAX_USERS
from app.domain.simulations import MAX_API_CALLS_PER_MONTH, MAX_STORAGE_GB
from app.domain.tax import FULL_RATE_BP


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


def _integer(column: str, condition: str) -> str:
    # typeof() is needed because SQLite would otherwise store 1.5 in an INTEGER column.
    return f"typeof({column}) = 'integer' AND {column} {condition}"


class SimulationRecord(Base):
    """A saved simulation and its price snapshot (spec 004 RF-7; plan 004 section 3)."""

    __tablename__ = "simulations"
    __table_args__ = (
        CheckConstraint(
            _integer("active_users", f"BETWEEN 0 AND {MAX_USERS}"),
            name="ck_simulations_active_users",
        ),
        CheckConstraint(
            _integer("storage_gb", f"BETWEEN 0 AND {MAX_STORAGE_GB}"),
            name="ck_simulations_storage_gb",
        ),
        CheckConstraint(
            _integer("api_calls_per_month", f"BETWEEN 0 AND {MAX_API_CALLS_PER_MONTH}"),
            name="ck_simulations_api_calls_per_month",
        ),
        CheckConstraint(_integer("subtotal_cents", ">= 0"), name="ck_simulations_subtotal"),
        CheckConstraint(
            _integer("tax_rate_bp", f"BETWEEN 0 AND {FULL_RATE_BP}"),
            name="ck_simulations_tax_rate_bp",
        ),
        CheckConstraint(_integer("tax_cents", ">= 0"), name="ck_simulations_tax"),
        CheckConstraint(
            _integer("total_cents", "= subtotal_cents + tax_cents"), name="ck_simulations_total"
        ),
        Index("ix_simulations_customer_id_created_at", "customer_id", "created_at"),
        # AUTOINCREMENT: an id is never reused, not even after deleting the last row (CA-1.2).
        {"sqlite_autoincrement": True},
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    # No ON DELETE: a customer with simulations cannot be deleted (CA-7.3).
    customer_id: Mapped[int] = mapped_column(
        ForeignKey("customers.id", name="fk_simulations_customer_id"), nullable=False
    )
    active_users: Mapped[int] = mapped_column(Integer, nullable=False)
    storage_gb: Mapped[int] = mapped_column(Integer, nullable=False)
    api_calls_per_month: Mapped[int] = mapped_column(Integer, nullable=False)
    subtotal_cents: Mapped[int] = mapped_column(Integer, nullable=False)
    tax_rate_bp: Mapped[int] = mapped_column(Integer, nullable=False)
    tax_cents: Mapped[int] = mapped_column(Integer, nullable=False)
    total_cents: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[str] = mapped_column(Text, nullable=False)
    # Saved together with the simulation in one commit, so a failure leaves nothing (DT-4).
    tiers: Mapped[list["SimulationTierRecord"]] = relationship(
        order_by="SimulationTierRecord.tier", cascade="all, delete-orphan"
    )


class SimulationTierRecord(Base):
    """One tier line of a simulation snapshot, with its limits (spec 004 D-3, CA-4.2)."""

    __tablename__ = "simulation_tiers"
    __table_args__ = (
        PrimaryKeyConstraint("simulation_id", "tier", name="pk_simulation_tiers"),
        CheckConstraint("tier BETWEEN 1 AND 3", name="ck_simulation_tiers_tier"),
        CheckConstraint(_integer("from_users", ">= 1"), name="ck_simulation_tiers_from_users"),
        CheckConstraint(
            "to_users IS NULL OR typeof(to_users) = 'integer'", name="ck_simulation_tiers_to_users"
        ),
        CheckConstraint(_integer("units", ">= 0"), name="ck_simulation_tiers_units"),
        CheckConstraint(
            _integer("unit_price_cents", ">= 0"), name="ck_simulation_tiers_unit_price"
        ),
        CheckConstraint(_integer("amount_cents", ">= 0"), name="ck_simulation_tiers_amount"),
    )

    simulation_id: Mapped[int] = mapped_column(
        ForeignKey("simulations.id", name="fk_simulation_tiers_simulation_id"), nullable=False
    )
    tier: Mapped[int] = mapped_column(Integer, nullable=False)
    from_users: Mapped[int] = mapped_column(Integer, nullable=False)
    to_users: Mapped[int | None] = mapped_column(Integer, nullable=True)  # NULL: open tier
    units: Mapped[int] = mapped_column(Integer, nullable=False)
    unit_price_cents: Mapped[int] = mapped_column(Integer, nullable=False)
    amount_cents: Mapped[int] = mapped_column(Integer, nullable=False)
