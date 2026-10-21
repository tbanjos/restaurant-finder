"""Composition helper for the configured restaurant provider adapter."""

from __future__ import annotations

from ...application.ports import RestaurantProvider
from .glovo_client import GlovoClient


def build_provider(
    *,
    city_code: str | None = None,
    city_name: str | None = None,
    country_code: str | None = None,
    language: str | None = None,
    address: str | None = None,
    timeout: float | None = None,
) -> RestaurantProvider:
    """Create the configured provider adapter."""
    return GlovoClient(
        city_code=city_code,
        city_name=city_name,
        country_code=country_code,
        language=language,
        address=address,
        timeout=timeout,
    )
