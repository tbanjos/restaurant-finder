from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

_RATING_RE = re.compile(r"(\d+(?:[.,]\d+)?)")
_VOTES_RE = re.compile(r"(\d+(?:[.,]\d+)?)\s*([kK])?")


def parse_rating(value: str | None) -> float | None:
    """Parse a Glovo rating such as ``"96%"`` into ``96.0``."""
    if not value:
        return None
    match = _RATING_RE.search(value)
    if not match:
        return None
    return float(match.group(1).replace(",", "."))


def parse_votes(value: str | None) -> int:
    """Parse a vote count such as ``"(1k+)"`` or ``"(500+)"`` into an int."""
    if not value:
        return 0
    match = _VOTES_RE.search(value)
    if not match:
        return 0
    count = float(match.group(1).replace(",", "."))
    if match.group(2):
        count *= 1000
    return int(count)


@dataclass(frozen=True)
class Restaurant:
    name: str
    rating: float | None
    votes: int
    cuisine: str
    eta: str
    distance: str
    delivery_fee: str
    url: str
    is_new: bool = False

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


def sort_restaurants(restaurants: list[Restaurant]) -> list[Restaurant]:
    """Rank by rating descending, then votes descending, then name."""
    return sorted(
        restaurants,
        key=lambda item: (
            item.rating is None,
            -(item.rating or 0),
            -item.votes,
            item.name.casefold(),
        ),
    )
