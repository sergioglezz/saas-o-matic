"""Create simulations and simulation_tiers (spec 004 RF-7; 00-spec-first 8.5; plan section 3).

Revision ID: 0003
Revises: 0002
Create Date: 2026-11-16
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0003"
down_revision: str | Sequence[str] | None = "0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


# The limits are written out instead of imported: a migration is frozen once created.
_SIMULATION_INTEGERS = (
    "customer_id",
    "active_users",
    "storage_gb",
    "api_calls_per_month",
    "subtotal_cents",
    "tax_rate_bp",
    "tax_cents",
    "total_cents",
)
_SIMULATION_CHECKS = (
    ("active_users", "BETWEEN 0 AND 100000", "ck_simulations_active_users"),
    ("storage_gb", "BETWEEN 0 AND 1000000", "ck_simulations_storage_gb"),
    ("api_calls_per_month", "BETWEEN 0 AND 1000000000", "ck_simulations_api_calls_per_month"),
    ("subtotal_cents", ">= 0", "ck_simulations_subtotal"),
    ("tax_rate_bp", "BETWEEN 0 AND 10000", "ck_simulations_tax_rate_bp"),
    ("tax_cents", ">= 0", "ck_simulations_tax"),
    ("total_cents", "= subtotal_cents + tax_cents", "ck_simulations_total"),
)
_TIER_CHECKS = (
    ("from_users", ">= 1", "ck_simulation_tiers_from_users"),
    ("units", ">= 0", "ck_simulation_tiers_units"),
    ("unit_price_cents", ">= 0", "ck_simulation_tiers_unit_price"),
    ("amount_cents", ">= 0", "ck_simulation_tiers_amount"),
)


def _integer(column: str, condition: str) -> str:
    # typeof() is needed because SQLite would otherwise store 1.5 in an INTEGER column (DT-12).
    return f"typeof({column}) = 'integer' AND {column} {condition}"


def _checks(checks: tuple[tuple[str, str, str], ...]) -> list[sa.CheckConstraint]:
    return [sa.CheckConstraint(_integer(column, rule), name=name) for column, rule, name in checks]


def upgrade() -> None:
    _create_simulations()
    op.create_index(
        "ix_simulations_customer_id_created_at", "simulations", ["customer_id", "created_at"]
    )
    _create_simulation_tiers()


def _create_simulations() -> None:
    op.create_table(
        "simulations",
        sa.Column("id", sa.Integer(), primary_key=True),
        *[sa.Column(name, sa.Integer(), nullable=False) for name in _SIMULATION_INTEGERS],
        sa.Column("created_at", sa.Text(), nullable=False),
        # No ON DELETE: a customer with simulations cannot be deleted (CA-7.3).
        sa.ForeignKeyConstraint(
            ["customer_id"], ["customers.id"], name="fk_simulations_customer_id"
        ),
        *_checks(_SIMULATION_CHECKS),
        # AUTOINCREMENT: an id is never reused, not even after deleting the last row (CA-1.2).
        sqlite_autoincrement=True,
    )


def _create_simulation_tiers() -> None:
    op.create_table(
        "simulation_tiers",
        sa.Column("simulation_id", sa.Integer(), nullable=False),
        sa.Column("tier", sa.Integer(), nullable=False),
        sa.Column("from_users", sa.Integer(), nullable=False),
        sa.Column("to_users", sa.Integer(), nullable=True),  # NULL: the open-ended last tier
        sa.Column("units", sa.Integer(), nullable=False),
        sa.Column("unit_price_cents", sa.Integer(), nullable=False),
        sa.Column("amount_cents", sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint("simulation_id", "tier", name="pk_simulation_tiers"),
        sa.ForeignKeyConstraint(
            ["simulation_id"], ["simulations.id"], name="fk_simulation_tiers_simulation_id"
        ),
        sa.CheckConstraint("tier BETWEEN 1 AND 3", name="ck_simulation_tiers_tier"),
        sa.CheckConstraint(
            "to_users IS NULL OR typeof(to_users) = 'integer'", name="ck_simulation_tiers_to_users"
        ),
        *_checks(_TIER_CHECKS),
    )


def downgrade() -> None:
    # Tiers first: they reference the simulations.
    op.drop_table("simulation_tiers")
    op.drop_index("ix_simulations_customer_id_created_at", table_name="simulations")
    op.drop_table("simulations")
