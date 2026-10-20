"""Fetch all store entries matching the current filters."""

from __future__ import annotations

from .context import GlovoSearchContext


class FetchStoreEntriesStep:
    """Fetch all store-wall entries matching the filters."""

    name = "fetch-store-entries"

    def run(self, context: GlovoSearchContext) -> None:
        context.entries = context.client.fetch_store_entries(context.filters)
