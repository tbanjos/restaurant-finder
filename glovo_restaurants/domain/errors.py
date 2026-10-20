class GlovoError(RuntimeError):
    """Base error for Glovo requests."""


class CuisineNotFoundError(GlovoError):
    """Raised when a cuisine cannot be matched to a Glovo food type."""


class AddressNotFoundError(GlovoError):
    """Raised when a delivery address cannot be located by Glovo."""
