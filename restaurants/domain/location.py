"""Delivery location data used for Glovo requests."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Location:
    """A delivery location and its resolved Glovo metadata."""

    city_code: str
    city_name: str
    country_code: str
    language: str
    address: str | None = None
    latitude: float | None = None
    longitude: float | None = None

    @property
    def has_coordinates(self) -> bool:
        """Whether the location has both latitude and longitude."""
        return self.latitude is not None and self.longitude is not None
