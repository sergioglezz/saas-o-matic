"""Access to simulations and simulation_tiers: the only module that reads or writes them.

Spec 004 RNF-1. Like the customer repository, ``add`` commits by itself: the API must know
whether the save succeeded before it answers (plan 004 DT-4, plan 003 DT-5).
"""

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.db.models import SimulationRecord, SimulationTierRecord
from app.domain.pricing import BASE_CURRENCY, PriceQuote, TierLine
from app.domain.simulations import NewSimulation, Simulation, SimulationPage


class SimulationRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, new: NewSimulation, price: PriceQuote, created_at: str) -> Simulation:
        """Save ``new`` with the snapshot ``price`` and return it with its id (CA-1.2, CA-4.2).

        The simulation and its tiers go in a single commit: if any row fails, the transaction
        is rolled back and the error raised, so nothing is left (CA-1.5).
        """
        record = SimulationRecord(
            customer_id=new.customer_id,
            active_users=new.active_users,
            storage_gb=new.storage_gb,
            api_calls_per_month=new.api_calls_per_month,
            subtotal_cents=price.subtotal_cents,
            tax_rate_bp=price.tax_rate_bp,
            tax_cents=price.tax_cents,
            total_cents=price.total_cents,
            created_at=created_at,
            tiers=[_to_tier_record(line) for line in price.tiers],
        )
        self._session.add(record)
        try:
            self._session.commit()
        except Exception:
            self._session.rollback()
            raise
        return _to_simulation(record)

    def list_for_customer(self, customer_id: int, limit: int, offset: int) -> SimulationPage:
        """One page of the customer's simulations, newest first and by id within the same
        second (CA-5.2), and how many it has in total (CA-5.3).

        The tiers come in one extra query for the whole page (plan DT-15).
        """
        of_customer = SimulationRecord.customer_id == customer_id
        count = select(func.count()).select_from(SimulationRecord).where(of_customer)
        page = (
            select(SimulationRecord)
            .where(of_customer)
            .order_by(SimulationRecord.created_at.desc(), SimulationRecord.id.desc())
            .options(selectinload(SimulationRecord.tiers))
            .limit(limit)
            .offset(offset)
        )
        records = self._session.scalars(page).all()
        return SimulationPage(
            items=tuple(_to_simulation(record) for record in records),
            total=self._session.scalar(count) or 0,
        )


def _to_tier_record(line: TierLine) -> SimulationTierRecord:
    return SimulationTierRecord(
        tier=line.tier,
        from_users=line.from_users,
        to_users=line.to_users,
        units=line.units,
        unit_price_cents=line.unit_price_cents,
        amount_cents=line.amount_cents,
    )


def _to_simulation(record: SimulationRecord) -> Simulation:
    """Rebuild the snapshot from the stored rows, never from the calculation (CA-4.5)."""
    return Simulation(
        id=record.id,
        customer_id=record.customer_id,
        active_users=record.active_users,
        storage_gb=record.storage_gb,
        api_calls_per_month=record.api_calls_per_month,
        currency=BASE_CURRENCY,  # every amount is stored in euros (constitution, principle 4)
        tiers=tuple(
            TierLine(
                tier=tier.tier,
                from_users=tier.from_users,
                to_users=tier.to_users,
                units=tier.units,
                unit_price_cents=tier.unit_price_cents,
                amount_cents=tier.amount_cents,
            )
            for tier in record.tiers
        ),
        subtotal_cents=record.subtotal_cents,
        tax_rate_bp=record.tax_rate_bp,
        tax_cents=record.tax_cents,
        total_cents=record.total_cents,
        created_at=record.created_at,
    )
