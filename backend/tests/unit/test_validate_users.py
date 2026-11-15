"""Range and type of the number of users, spec 001 RF-3.

Covers CA-3.1 to CA-3.4 and cases X-1, X-2 and X-3 of table 6.5.
"""

import pytest

from app.domain.errors import InvalidUsersError
from app.domain.pricing import MAX_USERS, validate_users


@pytest.mark.parametrize("users", [pytest.param(0, id="min-0"), pytest.param(100_000, id="max")])
def test_accepts_integers_at_both_ends_of_the_range(users: int) -> None:
    """CA-3.1, CA-3.2: 0 and 100000 are valid and are returned unchanged."""
    assert validate_users(users) == users


def test_max_users_is_one_hundred_thousand() -> None:
    """CA-3.1: the upper bound comes from RN-2."""
    assert MAX_USERS == 100_000


@pytest.mark.parametrize(
    "users",
    [pytest.param(-1, id="X-1"), pytest.param(100_001, id="X-2")],
)
def test_rejects_integers_out_of_range(users: int) -> None:
    """CA-3.3: below 0 or above 100000 raises InvalidUsersError."""
    with pytest.raises(InvalidUsersError):
        validate_users(users)


@pytest.mark.parametrize(
    "users",
    [
        pytest.param(True, id="X-3-true"),
        pytest.param(False, id="false"),
        pytest.param(15.0, id="float"),
        pytest.param("15", id="text"),
    ],
)
def test_rejects_values_that_are_not_plain_integers(users: object) -> None:
    """CA-3.4: booleans, floats and text raise InvalidUsersError, even if they look like 15."""
    with pytest.raises(InvalidUsersError):
        validate_users(users)  # type: ignore[arg-type]  # wrong type on purpose: runtime guard
