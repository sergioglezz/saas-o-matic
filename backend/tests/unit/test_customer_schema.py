"""Customer schemas without a server (level U), spec 003 task T-11.

Covers RF-2 (CA-2.1 to CA-2.7, CA-2.9), RF-3 (CA-3.3, CA-3.7, CA-3.9) and RF-5 (CA-5.8 to
CA-5.10) with the already decoded data of tables 6.4 and 6.7. The rows that need the database
(country without a rate, VA-17, VA-26 and VA-27) are tested over HTTP in T-13.
"""

import pytest
from pydantic import BaseModel, ValidationError

from app.api.validation import field_errors
from app.domain.customers import Customer
from app.schemas.customers import (
    CUSTOMER_INVALID_MESSAGES,
    CUSTOMER_REQUEST_EXAMPLE,
    CUSTOMER_RESPONSE_EXAMPLE,
    LIST_INVALID_MESSAGES,
    CustomerCreate,
    CustomerListQuery,
    CustomerResponse,
)

OBL = "Campo obligatorio"
NOM = "Debe tener entre 1 y 120 caracteres"
TID = "Debe tener entre 5 y 20 letras o dígitos"
ESP = "El DNI/NIF/CIF no es válido"
KLM = "Tipo de identificador no soportado"
EML = "Debe ser un email válido"
FMT = "Debe ser un código de país de 2 letras"
PLN = "Debe ser starter, business o enterprise"
NPE = "Campo no permitido"
LIM = "Debe ser un número entero entre 1 y 100"
OFF = "Debe ser un número entero entre 0 y 1000000"
QLN = "Debe tener como máximo 120 caracteres"

AL_1: dict[str, object] = {
    "company_name": "Acme Telecom S.L.",
    "tax_id": "B12345674",
    "contact_email": "compras@acme.example",
    "country": "ES",
    "plan": "business",
}
# 64 characters before the @ and 189 after it: 254 in total, every part at its own limit.
DOMAIN_189 = ".".join(["d" * 63, "d" * 63, "d" * 58, "es"])
EMAIL_254 = "l" * 64 + "@" + DOMAIN_189
EMAIL_255 = "l" * 64 + "@" + ".".join(["d" * 63, "d" * 63, "d" * 59, "es"])

Details = set[tuple[str, str]]


def _details(
    model: type[BaseModel], payload: dict[str, object], messages: dict[str, str]
) -> Details:
    """The (field, message) pairs the API would report, or an empty set when it is valid."""
    try:
        model.model_validate(payload)
    except ValidationError as error:
        details = field_errors(error, messages)
        assert len(details) == len({detail.field for detail in details})  # one per field
        return {(detail.field, detail.message) for detail in details}
    return set()


def _without(*fields: str, **changes: object) -> dict[str, object]:
    return {key: value for key, value in {**AL_1, **changes}.items() if key not in fields}


# (case id, decoded body, expected details)
TABLE_6_4: list[tuple[str, dict[str, object], Details]] = [
    (
        "VA-1",
        {},
        {(name, OBL) for name in ("company_name", "tax_id", "contact_email", "country", "plan")},
    ),
    ("VA-2", _without(company_name=""), {("company_name", NOM)}),
    ("VA-3", _without(company_name="   "), {("company_name", NOM)}),
    ("VA-4", _without(company_name="x" * 121), {("company_name", NOM)}),
    ("VA-5", _without(company_name=5), {("company_name", NOM)}),
    ("VA-6", _without(company_name="Acme" + chr(0)), {("company_name", NOM)}),
    ("VA-7", _without(tax_id="12345678A"), {("tax_id", ESP)}),
    ("VA-8", _without(tax_id="K1234567X"), {("tax_id", KLM)}),
    ("VA-9", _without(tax_id="1234", country="PT"), {("tax_id", TID)}),
    ("VA-10", _without(tax_id=None), {("tax_id", TID)}),
    ("VA-11", _without(tax_id="1234"), {("tax_id", TID)}),
    ("VA-12", _without(contact_email="sin-arroba"), {("contact_email", EML)}),
    ("VA-13", _without(contact_email="a@b"), {("contact_email", EML)}),
    ("VA-14", _without(contact_email=EMAIL_255), {("contact_email", EML)}),
    ("VA-15", _without(contact_email=7), {("contact_email", EML)}),
    ("VA-16-space", _without(contact_email="a b@c.es"), {("contact_email", EML)}),
    ("VA-16-two-at", _without(contact_email="a@@b.es"), {("contact_email", EML)}),
    ("VA-16-hyphen", _without(contact_email="a@-b.es"), {("contact_email", EML)}),
    ("VA-16-non-ascii", _without(contact_email="ñ@b.es"), {("contact_email", EML)}),
    ("VA-18", _without(country="ESP"), {("country", FMT)}),
    ("VA-19", _without("country", tax_id="12345678A"), {("country", OBL)}),
    ("VA-20", _without(plan="premium"), {("plan", PLN)}),
    ("VA-21", _without(plan="Business"), {("plan", PLN)}),
    ("VA-22", _without(plan=None), {("plan", PLN)}),
    ("VA-23", _without(id=7), {("id", NPE)}),
    (
        "VA-24",
        _without("company_name", Company_Name="Acme", created_at="2026-01-01T00:00:00Z"),
        {("Company_Name", NPE), ("created_at", NPE), ("company_name", OBL)},
    ),
    (
        "VA-25",
        _without(company_name="", tax_id="12345678A", contact_email="x", plan="x"),
        {("company_name", NOM), ("tax_id", ESP), ("contact_email", EML), ("plan", PLN)},
    ),
]


@pytest.mark.parametrize(
    ("payload", "expected"),
    [pytest.param(payload, expected, id=case_id) for case_id, payload, expected in TABLE_6_4],
)
def test_invalid_customers_give_the_details_of_table_6_4(
    payload: dict[str, object], expected: Details
) -> None:
    """CA-2.1 to CA-2.7, CA-2.9, CA-3.2, CA-3.3, CA-3.7, CA-3.9: one detail per invalid field."""
    assert _details(CustomerCreate, payload, CUSTOMER_INVALID_MESSAGES) == expected


def test_valid_customer_is_normalized_field_by_field() -> None:
    """CA-2.1 to CA-2.3, CA-3.1 (AL-2): spaces, case and separators are cleaned at the edge."""
    request = CustomerCreate.model_validate(
        {
            "company_name": "  Acme   Telecom \t S.L. ",
            "tax_id": "b-12.345.674",
            "contact_email": " compras@acme.example \n",
            "country": " es ",
            "plan": "business",
        }
    )

    assert request.model_dump() == AL_1


@pytest.mark.parametrize(
    "changes",
    [
        pytest.param({"company_name": "x" * 120}, id="AL-7-name-of-120-characters"),
        pytest.param({"contact_email": EMAIL_254}, id="AL-8-email-of-254-characters"),
        pytest.param(
            {"contact_email": "Nombre.Apellido+tag@Sub.Dominio.es"}, id="email-keeps-case"
        ),
        pytest.param({"country": "FR", "tax_id": "12345678A"}, id="CA-3.8-no-control-abroad"),
        pytest.param({"company_name": "Compañía Ñandú & Cía."}, id="name-with-non-ascii"),
    ],
)
def test_values_at_the_limits_are_accepted(changes: dict[str, object]) -> None:
    """CA-2.1, CA-2.2, CA-3.8: the limits themselves are valid and nothing is rewritten."""
    assert len(EMAIL_254) == 254 and len(EMAIL_255) == 255
    request = CustomerCreate.model_validate({**AL_1, **changes})

    assert request.model_dump() == {**AL_1, **changes}


def test_the_spanish_check_does_not_depend_on_the_order_of_the_json() -> None:
    """CA-3.3 (plan DT-1): tax_id may arrive before country and is still checked against it."""
    reordered = {"tax_id": "12345678A", **{k: v for k, v in AL_1.items() if k != "tax_id"}}

    assert _details(CustomerCreate, reordered, CUSTOMER_INVALID_MESSAGES) == {("tax_id", ESP)}


def test_response_serializes_exactly_the_example_of_spec_section_5() -> None:
    """CA-1.1: the 201 body, field for field."""
    customer = Customer(id=1, created_at="2026-11-13T10:00:00Z", **CUSTOMER_REQUEST_EXAMPLE)

    assert CUSTOMER_REQUEST_EXAMPLE == AL_1
    assert CustomerResponse.from_customer(customer).model_dump(mode="json") == {
        "id": 1,
        "company_name": "Acme Telecom S.L.",
        "tax_id": "B12345674",
        "contact_email": "compras@acme.example",
        "country": "ES",
        "plan": "business",
        "created_at": "2026-11-13T10:00:00Z",
    }
    assert CustomerResponse.from_customer(customer).model_dump(mode="json") == (
        CUSTOMER_RESPONSE_EXAMPLE
    )


# (case id, query parameters as the texts that arrive, expected details)
TABLE_6_7: list[tuple[str, dict[str, object], Details]] = [
    ("LP-1", {"limit": "0"}, {("limit", LIM)}),
    ("LP-2", {"limit": "101"}, {("limit", LIM)}),
    ("LP-3", {"limit": "abc"}, {("limit", LIM)}),
    ("LP-4", {"limit": "1.5"}, {("limit", LIM)}),
    ("LP-5", {"limit": "-1"}, {("limit", LIM)}),
    ("LP-6", {"limit": ""}, {("limit", LIM)}),
    ("LP-7", {"limit": "+5"}, {("limit", LIM)}),
    ("LP-8", {"limit": " 5"}, {("limit", LIM)}),
    ("LP-9", {"limit": chr(0x665)}, {("limit", LIM)}),  # ARABIC-INDIC DIGIT FIVE
    ("LP-10", {"offset": "-1"}, {("offset", OFF)}),
    ("LP-11", {"offset": "1000001"}, {("offset", OFF)}),
    ("LP-12", {"offset": "x"}, {("offset", OFF)}),
    ("LP-13", {"offset": "9" * 32}, {("offset", OFF)}),
    ("LP-14", {"limit": "0", "offset": "-1"}, {("limit", LIM), ("offset", OFF)}),
    ("LP-15", {"q": "q" * 121}, {("q", QLN)}),
]


@pytest.mark.parametrize(
    ("params", "expected"),
    [pytest.param(params, expected, id=case_id) for case_id, params, expected in TABLE_6_7],
)
def test_invalid_list_parameters_give_the_details_of_table_6_7(
    params: dict[str, object], expected: Details
) -> None:
    """CA-5.8, CA-5.9: digits 0-9 only and inside the range; q of at most 120 characters."""
    assert _details(CustomerListQuery, params, LIST_INVALID_MESSAGES) == expected


@pytest.mark.parametrize(
    ("params", "expected"),
    [
        pytest.param({}, ("", 50, 0), id="defaults"),
        pytest.param({"limit": "1", "offset": "0"}, ("", 1, 0), id="lowest-values"),
        pytest.param({"limit": "100", "offset": "1000000"}, ("", 100, 1_000_000), id="LI-20"),
        pytest.param({"limit": "007"}, ("", 7, 0), id="leading-zeros-are-digits"),
        pytest.param({"q": "  acme   telecom "}, ("acme telecom", 50, 0), id="LI-18"),
        pytest.param({"q": "   "}, ("", 50, 0), id="LI-6"),
        pytest.param({"q": "q" * 120}, ("q" * 120, 50, 0), id="q-of-120-characters"),
        pytest.param({"q": "x", "desconocido": "1"}, ("x", 50, 0), id="LI-16"),
        pytest.param({"offset": "9" * 5000}, None, id="number-too-long-to-parse"),
    ],
)
def test_valid_list_parameters(
    params: dict[str, object], expected: tuple[str, int, int] | None
) -> None:
    """CA-5.6, CA-5.8 to CA-5.10: defaults 50 and 0; unknown parameters are ignored."""
    if expected is None:
        assert _details(CustomerListQuery, params, LIST_INVALID_MESSAGES) == {("offset", OFF)}
        return
    query = CustomerListQuery.model_validate(params)

    assert (query.q, query.limit, query.offset) == expected
