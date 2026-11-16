"""Simulation data shared by the level U and level I tests of spec 004.

Table 6.3 (SV) is written once here: the schema test decodes each body and the HTTP test sends
it as it is (entry 20 of ai-review-log.md).
"""

import pytest

OBL = "Campo obligatorio"
CID = "Debe ser un número entero positivo"
CNS = "El país del cliente no está soportado"
USR = "Debe ser un número entero entre 0 y 100000"
STO = "Debe ser un número entero entre 0 y 1000000"
APC = "Debe ser un número entero entre 0 y 1000000000"
NPE = "Campo no permitido"
BODY = "El cuerpo debe ser un objeto JSON"

FIELDS = ("customer_id", "active_users", "storage_gb", "api_calls_per_month")
CUSTOMER, USERS, STORAGE, CALLS = FIELDS
# SI-1 as JSON literals, so a case can change a field to any JSON text (1.0, 1e0, true...).
SI_1_JSON = {CUSTOMER: "1", USERS: "15", STORAGE: "200", CALLS: "50000"}

# Table 6.3, SV-1 to SV-16: changes over SI-1 (None removes the field) and expected details.
SV_CASES = [
    pytest.param({key: None for key in SI_1_JSON}, {(field, OBL) for field in FIELDS}, id="SV-1"),
    pytest.param({CUSTOMER: '"1"'}, {(CUSTOMER, CID)}, id="SV-2"),
    pytest.param({CUSTOMER: "0"}, {(CUSTOMER, CID)}, id="SV-3-zero"),
    pytest.param({CUSTOMER: "-1"}, {(CUSTOMER, CID)}, id="SV-3-negative"),
    *[
        pytest.param({CUSTOMER: raw}, {(CUSTOMER, CID)}, id=f"SV-4-{raw}")
        for raw in ("1.0", "1e0", "true", "null")
    ],
    pytest.param({CUSTOMER: "9223372036854775808"}, {(CUSTOMER, CID)}, id="SV-5"),
    pytest.param({USERS: "100001"}, {(USERS, USR)}, id="SV-6-above"),
    pytest.param({USERS: "-1"}, {(USERS, USR)}, id="SV-6-negative"),
    *[
        pytest.param({USERS: raw}, {(USERS, USR)}, id=f"SV-7-{raw}")
        for raw in ("15.5", "1e1", '"15"', "null")
    ],
    pytest.param({STORAGE: "-1"}, {(STORAGE, STO)}, id="SV-8-negative"),
    pytest.param({STORAGE: "1000001"}, {(STORAGE, STO)}, id="SV-8-above"),
    *[
        pytest.param({STORAGE: raw}, {(STORAGE, STO)}, id=f"SV-9-{raw}")
        for raw in ("1.5", '"200"', "false")
    ],
    pytest.param({CALLS: "-1"}, {(CALLS, APC)}, id="SV-10-negative"),
    pytest.param({CALLS: "1000000001"}, {(CALLS, APC)}, id="SV-10-above"),
    *[pytest.param({CALLS: raw}, {(CALLS, APC)}, id=f"SV-11-{raw}") for raw in ("2.0", "[]")],
    pytest.param({USERS: None, "users": "15"}, {("users", NPE), (USERS, OBL)}, id="SV-12"),
    pytest.param(
        {"total_cents": "0", "country": '"ES"'},
        {("total_cents", NPE), ("country", NPE)},
        id="SV-13",
    ),
    pytest.param({"id": "7", "created_at": '"x"'}, {("id", NPE), ("created_at", NPE)}, id="SV-14"),
    pytest.param(
        {USERS: None, "Active_Users": "15"}, {("Active_Users", NPE), (USERS, OBL)}, id="SV-15"
    ),
    pytest.param(
        {CUSTOMER: '"x"', USERS: "-1", STORAGE: "-1", CALLS: "-1"},
        {(CUSTOMER, CID), (USERS, USR), (STORAGE, STO), (CALLS, APC)},
        id="SV-16",
    ),
]


def raw_body(changes: dict[str, str | None]) -> str:
    """SI-1 as JSON text with fields changed to raw JSON, added, or removed (``None``)."""
    literals = {**SI_1_JSON, **changes}
    pairs = ", ".join(f'"{key}": {value}' for key, value in literals.items() if value is not None)
    return "{" + pairs + "}"
