"""Timestamps (level U), spec 003 CA-1.3: ISO 8601 UTC text with seconds and the Z suffix."""

from datetime import UTC, datetime, timedelta, timezone

from app.core.clock import to_timestamp, utc_now


def test_timestamp_has_seconds_precision_and_the_z_suffix() -> None:
    """CA-1.3: fractions of a second are dropped, never rounded up."""
    moment = datetime(2026, 11, 13, 10, 0, 0, 999_999, tzinfo=UTC)

    assert to_timestamp(moment) == "2026-11-13T10:00:00Z"


def test_timestamp_is_always_expressed_in_utc() -> None:
    """CA-1.3: an instant given in another zone is the same instant in UTC."""
    madrid_winter = timezone(timedelta(hours=1))
    moment = datetime(2026, 11, 13, 11, 0, 0, tzinfo=madrid_winter)

    assert to_timestamp(moment) == "2026-11-13T10:00:00Z"


def test_timestamps_sort_like_time() -> None:
    """Plan section 3: the text order is the chronological order."""
    earlier = to_timestamp(datetime(2026, 9, 30, 23, 59, 59, tzinfo=UTC))
    later = to_timestamp(datetime(2026, 10, 1, 0, 0, 0, tzinfo=UTC))

    assert earlier < later


def test_utc_now_is_aware_and_in_utc() -> None:
    """CA-1.3: the clock never returns a naive datetime."""
    assert utc_now().utcoffset() == timedelta(0)
