class ProviderError(RuntimeError):
    """Base error for restaurant-provider requests."""


class CuisineNotFoundError(ProviderError):
    """Raised when a cuisine cannot be matched to a provider food type."""


class AddressNotFoundError(ProviderError):
    """Raised when a delivery address cannot be located by a provider."""
