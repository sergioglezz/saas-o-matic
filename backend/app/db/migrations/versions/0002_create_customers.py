"""Create customers (spec 003 RF-9; 00-spec-first 8.5; plan section 3).

Revision ID: 0002
Revises: 0001
Create Date: 2026-11-15
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0002"
down_revision: str | Sequence[str] | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "customers",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("company_name", sa.Text(), nullable=False),
        sa.Column("tax_id", sa.Text(), nullable=False),
        sa.Column("contact_email", sa.Text(), nullable=False),
        sa.Column("country", sa.Text(), nullable=False),
        sa.Column("plan", sa.Text(), nullable=False),
        sa.Column("created_at", sa.Text(), nullable=False),
        sa.UniqueConstraint("tax_id", name="uq_customers_tax_id"),
        sa.CheckConstraint(
            "length(company_name) BETWEEN 1 AND 120", name="ck_customers_company_name_length"
        ),
        sa.CheckConstraint("country GLOB '[A-Z][A-Z]'", name="ck_customers_country_format"),
        # Written out instead of imported: a migration is frozen once created (CA-9.1).
        sa.CheckConstraint(
            "plan IN ('starter', 'business', 'enterprise')", name="ck_customers_plan"
        ),
        # AUTOINCREMENT: an id is never reused, not even after deleting the last row (CA-1.3).
        sqlite_autoincrement=True,
    )
    op.create_index("ix_customers_company_name", "customers", ["company_name"])


def downgrade() -> None:
    op.drop_index("ix_customers_company_name", table_name="customers")
    op.drop_table("customers")
