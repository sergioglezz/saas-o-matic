"""The customer id of a route, shared by the detail and the history (plan 004 DT-10).

Declared as text in the routes: what is not an id names no customer, so it is the same 404 as
an unknown id and not a validation error (spec 003 CA-6.3 and D-3, spec 004 CA-5.5).
"""

import re

from app.core.errors import not_found
from app.domain.customers import MAX_CUSTOMER_ID

# A customer id as the API writes it: digits only, no sign and no leading zeros.
_CUSTOMER_ID = re.compile(r"[1-9][0-9]{0,18}")


def parse_customer_id(text: str) -> int:
    """The id written in ``text``. Raises the 404 ApiError if it is not one."""
    if not _CUSTOMER_ID.fullmatch(text) or int(text) > MAX_CUSTOMER_ID:
        raise not_found()
    return int(text)
