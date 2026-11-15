"""Schemas of POST /pricing/quote (spec 002 RF-2 to RF-5).

Input rules live here, at the API edge (constitution principle 3): the calculation of spec 001
only ever receives values that already passed them.
"""

import re

COUNTRY_INVALID_MESSAGE = "Debe ser un código de país de 2 letras"

# Only these four are trimmed (CA-3.1). A bare str.strip() would also remove the
# non-breaking space that case E-23 must reject (plan 002 DT-3).
_EDGE_WHITESPACE = " \t\n\r"
# ASCII-only uppercasing: str.upper() turns "ß" into "SS", a valid-looking code (plan DT-3).
_ASCII_UPPERCASE = str.maketrans("abcdefghijklmnopqrstuvwxyz", "ABCDEFGHIJKLMNOPQRSTUVWXYZ")
_COUNTRY_CODE = re.compile(r"[A-Z]{2}")


def normalize_country(value: str) -> str:
    """Trim the edges and uppercase a-z; the result must be exactly 2 letters A-Z (RF-3).

    Raises ValueError otherwise.
    """
    code = value.strip(_EDGE_WHITESPACE).translate(_ASCII_UPPERCASE)
    if not _COUNTRY_CODE.fullmatch(code):
        raise ValueError(COUNTRY_INVALID_MESSAGE)
    return code
