"""Resource helpers for tags."""

from __future__ import annotations

from typing import Any, Dict

from tools.discourse import DiscourseClient


async def fetch_tags(client: DiscourseClient | None = None) -> Dict[str, Any]:
    """Return the tags payload from the forum."""

    # Allow callers to inject a prepared client, but default to a fresh instance otherwise.
    client = client or DiscourseClient()
    return await client.list_tags()

