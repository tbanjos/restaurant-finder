"""Map raw Glovo entries to the restaurant domain model."""

from __future__ import annotations

from typing import Any

from ....domain import Location, Restaurant
from ....domain.helper import parse_rating, parse_votes
from .context import GlovoSearchContext


def restaurant_from_api(entry: dict[str, Any], location: Location) -> Restaurant:
    """Convert a Glovo store entry into a domain ``Restaurant``."""
    ratings = entry.get("ratings") or {}
    delivery_fee = entry.get("deliveryFee") or {}
    slug = entry.get("slug") or ""
    score = ratings.get("score")
    return Restaurant(
        name=entry.get("title") or slug,
        rating=parse_rating(score),
        votes=parse_votes(ratings.get("votes")),
        cuisine=entry.get("tag") or "",
        eta=entry.get("eta") or "",
        distance=entry.get("distance") or "",
        delivery_fee=delivery_fee.get("effectiveFee") or "",
        url=(
            f"https://glovoapp.com/{location.language}/{location.country_code}/"
            f"{location.city_name}/stores/{slug}"
        ),
        is_new=bool(entry.get("isNew")) or (score or "").strip().lower() == "new",
    )


class BuildRestaurantsStep:
    """Convert raw Glovo entries into the application's ``Restaurant`` model."""

    name = "build-restaurants"

    def run(self, context: GlovoSearchContext) -> None:
        location = context.client.location
        context.restaurants = [
            restaurant_from_api(entry, location) for entry in context.entries
        ]
