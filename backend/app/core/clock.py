"""Current time and the single timestamp format of the API and the database.

Dates travel and are stored as ISO 8601 UTC text (00-spec-first 8.1 and 8.5). With seconds
precision and a fixed width, the text sorts exactly like time does.
"""

from datetime import UTC, datetime

_TIMESTAMP_FORMAT = "%Y-%m-%dT%H:%M:%SZ"


def utc_now() -> datetime:
    return datetime.now(UTC)


def to_timestamp(moment: datetime) -> str:
    """``moment`` in UTC as text, e.g. 2026-11-13T10:00:00Z (spec 003 CA-1.3)."""
    return moment.astimezone(UTC).strftime(_TIMESTAMP_FORMAT)
