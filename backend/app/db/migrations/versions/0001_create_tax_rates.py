"""Create tax_rates with the default rates (spec 001 RF-4, RF-13; plan section 3).

Revision ID: 0001
Revises:
Create Date: 2026-11-15
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0001"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# Written out here instead of imported from the app: a migration is frozen once created and
# must keep producing the same result even if application code changes later (CA-4.3, D-5).
DEFAULT_RATES_BP = {"ES": 2100, "PT": 2300, "FR": 2000, "DE": 1900, "IT": 2200, "GB": 2000, "US": 0}


def upgrade() -> None:
    tax_rates = op.create_table(
        "tax_rates",
        sa.Column("country", sa.Text(), primary_key=True),
        sa.Column("rate_bp", sa.Integer(), nullable=False),
        sa.CheckConstraint("country GLOB '[A-Z][A-Z]'", name="ck_tax_rates_country_format"),
        # typeof() is needed because SQLite would otherwise store 21.5 in an INTEGER column.
        sa.CheckConstraint(
            "typeof(rate_bp) = 'integer' AND rate_bp BETWEEN 0 AND 10000",
            name="ck_tax_rates_rate_bp_range",
        ),
    )
    op.bulk_insert(
        tax_rates,
        [{"country": country, "rate_bp": rate_bp} for country, rate_bp in DEFAULT_RATES_BP.items()],
    )


def downgrade() -> None:
    op.drop_table("tax_rates")
