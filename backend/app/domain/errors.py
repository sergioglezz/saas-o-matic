"""Domain errors for pricing, tax, customers and simulations.

They carry no user-facing text on purpose: the API layer maps each one to its Spanish message
in a single place (app.api.error_mapping).
"""


class PricingError(Exception):
    """Base class for every pricing rule violation."""


class InvalidUsersError(PricingError):
    """``users`` is not an integer between 0 and MAX_USERS (CA-3.3, CA-3.4)."""


class UnsupportedCountryError(PricingError):
    """The country has no configured tax rate (CA-4.6)."""

    def __init__(self, country: str) -> None:
        super().__init__(country)
        self.country = country


class InvalidTaxRateError(PricingError):
    """``rate_bp`` is not an integer between 0 and 10000 (CA-13.1)."""


class CustomerError(Exception):
    """Base class for every customer rule violation (spec 003)."""


class InvalidTaxIdFormatError(CustomerError):
    """The normalized tax id is not 5 to 20 letters A-Z or digits (003 CA-3.2)."""


class InvalidSpanishTaxIdError(CustomerError):
    """With country ES, the tax id is not a DNI, NIE or CIF with the right control (003 CA-3.3)."""


class UnsupportedTaxIdTypeError(CustomerError):
    """Spanish special NIF starting with K, L or M: no published control method (003 CA-3.7)."""


class DuplicateTaxIdError(CustomerError):
    """Another customer already has this normalized tax id (003 CA-4.1)."""


class CustomerNotFoundError(CustomerError):
    """No customer has this id (003 CA-6.2)."""


class SimulationError(Exception):
    """Base class for every simulation rule violation (spec 004)."""


class InvalidStorageError(SimulationError):
    """``storage_gb`` is not an integer between 0 and MAX_STORAGE_GB (004 CA-2.3)."""


class InvalidApiCallsError(SimulationError):
    """``api_calls_per_month`` is not an integer between 0 and its maximum (004 CA-2.4)."""


class UnsupportedCustomerCountryError(SimulationError):
    """The customer's country has no tax rate now, so nothing can be priced (004 CA-3.4).

    Not UnsupportedCountryError: that one is reported on a ``country`` field, which a
    simulation request does not have (plan 004 DT-3).
    """

    def __init__(self, customer_id: int) -> None:
        super().__init__(customer_id)
        self.customer_id = customer_id
