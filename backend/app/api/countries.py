"""Validation error of a request that carries a country, shared by the quote and the customers.

Schema validation stops before the service runs, so a request with any invalid field would
never learn that its country is also unsupported. Checking it here reports both at once
(spec 002 E-35, spec 003 VA-26 and VA-27).
"""

from collections.abc import Mapping

from pydantic import ValidationError

from app.api.validation import field_errors, validation_error
from app.core.errors import ApiError, FieldError
from app.schemas.pricing import COUNTRY_UNSUPPORTED_MESSAGE, normalize_country
from app.services.pricing import TaxRateSource, country_is_supported


def invalid_request(
    error: ValidationError,
    invalid_messages: Mapping[str, str],
    payload: Mapping[str, object],
    rates: TaxRateSource,
) -> ApiError:
    """422 with one detail per invalid field, plus "País no soportado" when it applies."""
    details = field_errors(error, invalid_messages)
    country = payload.get("country")
    country_is_well_formed = isinstance(country, str) and all(d.field != "country" for d in details)
    if country_is_well_formed and not country_is_supported(normalize_country(str(country)), rates):
        details.append(FieldError(field="country", message=COUNTRY_UNSUPPORTED_MESSAGE))
    return validation_error(details)
