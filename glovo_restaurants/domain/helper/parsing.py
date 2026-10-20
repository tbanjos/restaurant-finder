"""Parsing helpers for values displayed by Glovo's store listings."""

from __future__ import annotations

import re

_RATING_RE = re.compile(r"(\d+(?:[.,]\d+)?)")
_VOTES_RE = re.compile(r"(\d+(?:[.,]\d+)?)\s*([kK])?")
_DISTANCE_RE = re.compile(r"(\d+(?:[.,]\d+)?)\s*(km|m)\b", re.IGNORECASE)
_NUMBER = r"(\d+(?:[.,]\d+)?)"


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
