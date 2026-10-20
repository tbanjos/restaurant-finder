"""Keep only stores that are currently open for orders."""

from __future__ import annotations

from typing import Any

from ..search_context import SearchContext


class FilterOpenStep:
    """Drop entries that Glovo reports as unavailable for ordering."""

    name = "filter-open"

    def run(self, context: SearchContext) -> None:
        context.entries = [
            entry for entry in context.entries if store_is_open(entry)
        ]


def store_is_open(entry: dict[str, Any]) -> bool:
    """Return whether a store listing is currently open for orders.

    Glovo omits ``availability`` from some responses; in that case the store is
    treated as open so older/partial payloads keep working.
    """
    status = (entry.get("availability") or {}).get("status")
    return status is None or str(status).upper() == "OPEN"
