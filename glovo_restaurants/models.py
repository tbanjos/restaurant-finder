"""Domain model and parsing/ranking helpers for Glovo store data."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

_RATING_RE = re.compile(r"(\d+(?:[.,]\d+)?)")
_VOTES_RE = re.compile(r"(\d+(?:[.,]\d+)?)\s*([kK])?")
_DISTANCE_RE = re.compile(r"(\d+(?:[.,]\d+)?)\s*(km|m)\b", re.IGNORECASE)
_NUMBER = r"(\d+(?:[.,]\d+)?)"

SORT_DISTANCE = "distance"
SORT_RATING = "rating"
SORT_DELIVERY_TIME = "delivery_time"
SORT_OPTIONS = (SORT_DISTANCE, SORT_RATING, SORT_DELIVERY_TIME)
DEFAULT_SORT = SORT_DISTANCE


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


def parse_distance(value: str | None) -> float | None:
    """Parse a Glovo distance such as ``"<100m"`` or ``"1.5km"`` into meters."""
    if not value:
        return None
    match = _DISTANCE_RE.search(value)
    if not match:
        return None
    amount = float(match.group(1).replace(",", "."))
    return amount * 1000 if match.group(2).casefold() == "km" else amount


def parse_eta(value: str | None) -> float | None:
    """Parse a delivery estimate such as ``"30-40 min"`` into minutes.

    Ranges use their midpoint, and combined values such as ``"1h 10 min"`` are
    added together.
    """
    if not value:
        return None
    text = value.casefold().replace(",", ".")
    minutes = 0.0

    hour_range = re.search(
        rf"{_NUMBER}\s*(?:-|–|to)\s*{_NUMBER}\s*h", text
    )
    hour = re.search(rf"{_NUMBER}\s*h", text)
    if hour_range:
        minutes = (
            float(hour_range.group(1)) + float(hour_range.group(2))
        ) / 2 * 60
        remainder = text[hour_range.end():]
    elif hour:
        minutes = float(hour.group(1)) * 60
        remainder = text[hour.end():]
    else:
        remainder = text

    minute_range = re.search(
        rf"{_NUMBER}\s*(?:-|–|to)\s*{_NUMBER}\s*min", remainder
    )
    minute = re.search(rf"{_NUMBER}\s*min", remainder)
    if minute_range:
        minutes += (
            float(minute_range.group(1)) + float(minute_range.group(2))
        ) / 2
    elif minute:
        minutes += float(minute.group(1))
    elif not hour and not hour_range:
        numbers = re.findall(r"\d+(?:\.\d+)?", text)
        if numbers:
            minutes = sum(float(item) for item in numbers) / len(numbers)

    return minutes or None


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


def sort_restaurants(
    restaurants: list[Restaurant], by: str = DEFAULT_SORT
) -> list[Restaurant]:
    """Rank restaurants by the requested strategy.

    ``distance`` (the default) puts the closest restaurants first. ``rating``
    ranks by rating, then votes. ``delivery_time`` ranks by the midpoint of the
    ETA range. Missing values always go last. Names break final ties.
    """
    option = str(by).casefold().replace("-", "_")

    if option in {"distance", "closest"}:
        key = lambda item: (
            item.distance_meters is None,
            item.distance_meters or 0,
            item.rating is None,
            -(item.rating or 0),
            -item.votes,
            item.name.casefold(),
        )
    elif option in {"rating", "ratings"}:
        key = lambda item: (
            item.rating is None,
            -(item.rating or 0),
            -item.votes,
            item.distance_meters is None,
            item.distance_meters or 0,
            item.name.casefold(),
        )
    elif option in {"delivery_time", "delivery", "eta", "time"}:
        key = lambda item: (
            item.eta_minutes is None,
            item.eta_minutes or 0,
            item.distance_meters is None,
            item.distance_meters or 0,
            item.rating is None,
            -(item.rating or 0),
            -item.votes,
            item.name.casefold(),
        )
    else:
        raise ValueError(
            f"Unknown sort option '{by}'. Choose from: {', '.join(SORT_OPTIONS)}"
        )

    return sorted(restaurants, key=key)
