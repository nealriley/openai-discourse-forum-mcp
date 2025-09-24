"""Resource helpers for site metadata."""

from __future__ import annotations

from typing import Any, Dict

from tools.discourse import DiscourseClient


async def fetch_site_info(client: DiscourseClient | None = None) -> Dict[str, Any]:
    """Return the site metadata payload from Discourse."""

    # Allow callers to inject a prepared client, but default to a fresh instance otherwise.
    client = client or DiscourseClient()
    return await client.get_site_info()

