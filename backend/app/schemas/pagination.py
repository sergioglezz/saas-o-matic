"""Page parameters shared by the lists of the API (spec 003 CA-5.6, CA-5.8; spec 004 CA-5.3).

Moved out of the customer list so the simulation history uses the same rules and messages
(plan 004 DT-9). They arrive as text and are validated here (plan 003 DT-7).
"""

import re

from pydantic import BaseModel, field_validator

LIMIT_INVALID_MESSAGE = "Debe ser un número entero entre 1 y 100"
OFFSET_INVALID_MESSAGE = "Debe ser un número entero entre 0 y 1000000"
PAGE_INVALID_MESSAGES = {"limit": LIMIT_INVALID_MESSAGE, "offset": OFFSET_INVALID_MESSAGE}

DEFAULT_LIMIT, MAX_LIMIT = 50, 100
# SQLite cannot take an arbitrarily large OFFSET; beyond this the request is a mistake (003 D-9).
MAX_OFFSET = 1_000_000

# [0-9] and not \d or str.isdigit(): those also accept digits of other alphabets (003 LP-9).
_DIGITS = re.compile(r"[0-9]+")


def _integer_in_range(value: object, minimum: int, maximum: int) -> int:
    """A query value written with digits only and inside the range (003 CA-5.8)."""
    if not isinstance(value, str) or not _DIGITS.fullmatch(value):
        raise ValueError("not written with digits only")
    number = int(value)
    if not minimum <= number <= maximum:
        raise ValueError("out of range")
    return number


class PageQuery(BaseModel):
    """``limit`` and ``offset`` of a list, validated from the texts that arrive.

    Unknown parameters are ignored (003 CA-5.10).
    """

    limit: int = DEFAULT_LIMIT
    offset: int = 0

    @field_validator("limit", mode="before")
    @classmethod
    def _parse_limit(cls, value: object) -> int:
        return _integer_in_range(value, 1, MAX_LIMIT)

    @field_validator("offset", mode="before")
    @classmethod
    def _parse_offset(cls, value: object) -> int:
        return _integer_in_range(value, 0, MAX_OFFSET)
