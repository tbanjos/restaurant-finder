"""The restaurant domain model."""

from __future__ import annotations

from dataclasses import dataclass

from .helper.parsing import parse_distance, parse_eta


@dataclass(frozen=True)
class Restaurant:
    """A restaurant ready for ranking and CSV export."""

    name: str
    rating: float | None
    votes: int
    cuisine: str
    eta: str
    distance: str
    delivery_fee: str
    url: str
    is_new: bool = False

    @property
    def distance_meters(self) -> float | None:
        """Distance in meters, when Glovo provides a parseable value."""
        return parse_distance(self.distance)

    @property
    def eta_minutes(self) -> float | None:
        """Delivery estimate in minutes, when Glovo provides a parseable value."""
        return parse_eta(self.eta)
