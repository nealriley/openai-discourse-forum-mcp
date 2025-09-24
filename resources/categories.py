"""Resource helpers for categories."""

from __future__ import annotations

from typing import Any, Dict

from tools.discourse import DiscourseClient


async def fetch_categories(client: DiscourseClient | None = None) -> Dict[str, Any]:
    """Return categories JSON payload from Discourse."""

    # Allow callers to inject a prepared client, but default to a fresh instance otherwise.
    client = client or DiscourseClient()
    return await client.list_categories()

