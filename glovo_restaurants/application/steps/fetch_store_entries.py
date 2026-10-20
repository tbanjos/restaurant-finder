"""Fetch all store entries matching the current filters."""

from __future__ import annotations

from ..search_context import SearchContext


class FetchStoreEntriesStep:
    """Fetch all store-wall entries matching the filters."""

    name = "fetch-store-entries"

    def run(self, context: SearchContext) -> None:
        context.entries = context.client.fetch_store_entries(context.filters)
