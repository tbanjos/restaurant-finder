"""The restaurant domain model."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .helper.parsing import parse_distance, parse_eta, parse_rating, parse_votes


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

    @classmethod
    def from_api(
        cls,
        entry: dict[str, Any],
        *,
        city: str = "barcelona",
        country: str = "es",
        language: str = "en",
    ) -> "Restaurant":
        ratings = entry.get("ratings") or {}
        delivery_fee = entry.get("deliveryFee") or {}
        slug = entry.get("slug") or ""
        score = ratings.get("score")
        return cls(
            name=entry.get("title") or slug,
            rating=parse_rating(score),
            votes=parse_votes(ratings.get("votes")),
            cuisine=entry.get("tag") or "",
            eta=entry.get("eta") or "",
            distance=entry.get("distance") or "",
            delivery_fee=delivery_fee.get("effectiveFee") or "",
            url=f"https://glovoapp.com/{language}/{country}/{city}/stores/{slug}",
            is_new=bool(entry.get("isNew")) or (score or "").strip().lower() == "new",
        )
