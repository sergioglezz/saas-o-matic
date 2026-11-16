"""Schemas of the customer routes (spec 003 RF-1, RF-2, RF-3 and RF-5).

Input rules live here, at the API edge (constitution principle 3). The tax id control itself
is domain code; this module only asks for it and words the answer.
"""

import dataclasses
import re
from typing import Self

from pydantic import BaseModel, ConfigDict, Field, ValidationInfo, field_validator

from app.core.errors import InvalidFieldError
from app.domain.customers import PLANS, Customer, CustomerPage, NewCustomer
from app.domain.errors import (
    InvalidSpanishTaxIdError,
    InvalidTaxIdFormatError,
    UnsupportedTaxIdTypeError,
)
from app.domain.tax_id import validate_tax_id
from app.schemas.pagination import PAGE_INVALID_MESSAGES, PageQuery
from app.schemas.pricing import COUNTRY_INVALID_MESSAGE, normalize_country

COMPANY_NAME_INVALID_MESSAGE = "Debe tener entre 1 y 120 caracteres"
TAX_ID_INVALID_MESSAGE = "Debe tener entre 5 y 20 letras o dígitos"
TAX_ID_SPANISH_MESSAGE = "El DNI/NIF/CIF no es válido"
TAX_ID_UNSUPPORTED_TYPE_MESSAGE = "Tipo de identificador no soportado"
TAX_ID_DUPLICATED_MESSAGE = "Ya existe un cliente con este identificador"
EMAIL_INVALID_MESSAGE = "Debe ser un email válido"
PLAN_INVALID_MESSAGE = "Debe ser starter, business o enterprise"
Q_TOO_LONG_MESSAGE = "Debe tener como máximo 120 caracteres"

# Message for a field that is present but invalid, unless its validator chose another one.
CUSTOMER_INVALID_MESSAGES = {
    "company_name": COMPANY_NAME_INVALID_MESSAGE,
    "tax_id": TAX_ID_INVALID_MESSAGE,
    "contact_email": EMAIL_INVALID_MESSAGE,
    "country": COUNTRY_INVALID_MESSAGE,
    "plan": PLAN_INVALID_MESSAGE,
}
LIST_INVALID_MESSAGES = {"q": Q_TOO_LONG_MESSAGE, **PAGE_INVALID_MESSAGES}

COMPANY_NAME_MAX_LENGTH = 120
EMAIL_MAX_LENGTH = 254
Q_MAX_LENGTH = 120

_EDGE_WHITESPACE = " \t\n\r"
# local@domain as HTML forms understand it, plus a dot in the domain (CA-2.2). Written by
# hand to avoid a new dependency for one field (spec decision D-1).
_LABEL = r"[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?"
_EMAIL = re.compile(rf"[A-Za-z0-9.!#$%&'*+/=?^_`{{|}}~-]{{1,64}}@{_LABEL}(?:\.{_LABEL})+")


def _compact_spaces(value: str) -> str:
    """No whitespace at the edges and a single space between words (CA-2.1)."""
    return " ".join(value.split())


class CustomerCreate(BaseModel):
    """Body of POST /customers: five text fields, case-sensitive names (RF-2)."""

    model_config = ConfigDict(strict=True, extra="forbid")

    company_name: str
    contact_email: str
    # Declared before tax_id on purpose: the tax id validator reads the validated country,
    # whatever the order of the JSON (plan 003 DT-1).
    country: str
    plan: str = Field(json_schema_extra={"enum": list(PLANS)})
    tax_id: str

    @field_validator("company_name")
    @classmethod
    def _clean_company_name(cls, value: str) -> str:
        name = _compact_spaces(value)
        if not 1 <= len(name) <= COMPANY_NAME_MAX_LENGTH or not name.isprintable():
            raise ValueError(COMPANY_NAME_INVALID_MESSAGE)
        return name

    @field_validator("contact_email")
    @classmethod
    def _clean_contact_email(cls, value: str) -> str:
        email = value.strip(_EDGE_WHITESPACE)
        if len(email) > EMAIL_MAX_LENGTH or not _EMAIL.fullmatch(email):
            raise ValueError(EMAIL_INVALID_MESSAGE)
        return email

    @field_validator("country")
    @classmethod
    def _normalize_country(cls, value: str) -> str:
        return normalize_country(value)

    @field_validator("plan")
    @classmethod
    def _known_plan(cls, value: str) -> str:
        if value not in PLANS:
            raise ValueError(PLAN_INVALID_MESSAGE)
        return value

    @field_validator("tax_id")
    @classmethod
    def _validate_tax_id(cls, value: str, info: ValidationInfo) -> str:
        # info.data holds only the fields that passed: without a valid country, the tax id
        # gets the basic format alone, so both fields are reported together (CA-3.9).
        try:
            return validate_tax_id(value, info.data.get("country"))
        except InvalidSpanishTaxIdError:
            raise InvalidFieldError(TAX_ID_SPANISH_MESSAGE) from None
        except UnsupportedTaxIdTypeError:
            raise InvalidFieldError(TAX_ID_UNSUPPORTED_TYPE_MESSAGE) from None
        except InvalidTaxIdFormatError:
            raise ValueError(TAX_ID_INVALID_MESSAGE) from None

    def to_new_customer(self) -> NewCustomer:
        return NewCustomer(**self.model_dump())


class CustomerListQuery(PageQuery):
    """Query string of GET /customers, validated from the texts that arrive (CA-5.8, CA-5.9).

    ``limit`` and ``offset`` come from PageQuery (plan 004 DT-9). Unknown parameters are
    ignored (CA-5.10).
    """

    q: str = ""

    @field_validator("q")
    @classmethod
    def _clean_q(cls, value: str) -> str:
        text = _compact_spaces(value)
        if len(text) > Q_MAX_LENGTH:
            raise ValueError(Q_TOO_LONG_MESSAGE)
        return text


class CustomerResponse(BaseModel):
    """A customer as the API returns it: the contract of spec 003 section 5."""

    id: int
    company_name: str
    tax_id: str
    contact_email: str
    country: str
    plan: str
    created_at: str

    @classmethod
    def from_customer(cls, customer: Customer) -> Self:
        # Customer already uses the contract's field names.
        return cls.model_validate(dataclasses.asdict(customer))


class CustomerListResponse(BaseModel):
    """200 body of GET /customers: one page and the number of matches (CA-5.1, CA-5.7)."""

    items: list[CustomerResponse]
    total: int

    @classmethod
    def from_page(cls, page: CustomerPage) -> Self:
        items = [CustomerResponse.from_customer(customer) for customer in page.items]
        return cls(items=items, total=page.total)


# Examples for the interactive docs (RNF-4): the ones of spec 003 section 5.
CUSTOMER_REQUEST_EXAMPLE: dict[str, str] = {
    "company_name": "Acme Telecom S.L.",
    "tax_id": "B12345674",
    "contact_email": "compras@acme.example",
    "country": "ES",
    "plan": "business",
}
CUSTOMER_RESPONSE_EXAMPLE: dict[str, object] = {
    "id": 1,
    **CUSTOMER_REQUEST_EXAMPLE,
    "created_at": "2026-11-13T10:00:00Z",
}
CUSTOMER_LIST_RESPONSE_EXAMPLE: dict[str, object] = {
    "items": [CUSTOMER_RESPONSE_EXAMPLE],
    "total": 1,
}
