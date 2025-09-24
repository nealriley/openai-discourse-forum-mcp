"""MCP tool implementations for interacting with the OpenAI Community Discourse API."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

import httpx

BASE_URL = "https://community.openai.com"
USER_AGENT = "openai-community-mcp/0.1.0"
SUMMARY_CHAR_LIMIT = 500


class DiscourseClient:
    """Thin wrapper around httpx for calling the OpenAI Community JSON endpoints."""

    def __init__(self, base_url: str = BASE_URL) -> None:
        # Normalize the base URL once to avoid double slashes when composing endpoints.
        self._base_url = base_url.rstrip("/")

    async def get_latest_topics(self, page: int = 0) -> Dict[str, Any]:
        params = {"page": page} if page else None
        return await self._get_json("/latest.json", params=params)

    async def get_top_topics(self, period: str, page: Optional[int] = None) -> Dict[str, Any]:
        params: Dict[str, Any] = {"period": period}
        if page is not None:
            params["page"] = page
        return await self._get_json("/top.json", params=params)

    async def get_topic(self, topic_id: int, print_mode: bool = False) -> Dict[str, Any]:
        params = {"print": "true"} if print_mode else None
        return await self._get_json(f"/t/{topic_id}.json", params=params)

    async def search(self, query: str, page: Optional[int] = None) -> Dict[str, Any]:
        params: Dict[str, Any] = {"q": query}
        if page is not None:
            params["page"] = page
        return await self._get_json("/search.json", params=params)

    async def list_categories(self) -> Dict[str, Any]:
        return await self._get_json("/categories.json")

    async def list_tags(self) -> Dict[str, Any]:
        return await self._get_json("/tags.json")

    async def get_site_info(self) -> Dict[str, Any]:
        return await self._get_json("/site.json")

    async def _get_json(self, path: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        # Create a short-lived AsyncClient per call to keep things simple and avoid shared state.
        async with httpx.AsyncClient(
            base_url=self._base_url,
            headers={"User-Agent": USER_AGENT},
            timeout=httpx.Timeout(10.0),
        ) as client:
            response = await client.get(path, params=params)
            response.raise_for_status()
            return response.json()


def format_topics(topics: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Normalize topic payloads into a compact structure for MCP responses."""

    formatted: List[Dict[str, Any]] = []
    for topic in topics:
        formatted.append(
            {
                "id": topic.get("id"),
                "title": topic.get("fancy_title") or topic.get("title"),
                "slug": topic.get("slug"),
                "created_at": topic.get("created_at"),
                "last_posted_at": topic.get("last_posted_at"),
                "posts_count": topic.get("posts_count"),
                "reply_count": topic.get("reply_count"),
                "bumped_at": topic.get("bumped_at"),
                "url": f"https://community.openai.com/t/{topic.get('slug')}/{topic.get('id')}" if topic.get("id") else None,
                "last_poster_username": topic.get("last_poster_username"),
                "tags": topic.get("tags", []),
                "views": topic.get("views"),
                "excerpt": _truncate(topic.get("excerpt")),
            }
        )
    return formatted


def format_posts(posts: List[Dict[str, Any]], *, limit: int = 10) -> List[Dict[str, Any]]:
    """Return trimmed post metadata to keep tool output concise."""

    summary: List[Dict[str, Any]] = []
    # Only include the first `limit` posts to keep tool responses compact.
    for post in posts[:limit]:
        summary.append(
            {
                "id": post.get("id"),
                "post_number": post.get("post_number"),
                "username": post.get("username"),
                "created_at": post.get("created_at"),
                "updated_at": post.get("updated_at"),
                "excerpt": _truncate(post.get("cooked")),
            }
        )
    return summary


def format_search_results(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Summarize search results into topics and posts."""

    topics = format_topics(payload.get("topics", []))
    posts_summary: List[Dict[str, Any]] = []
    # Discourse search returns posts and topics separately; we normalize both shapes.
    for post in payload.get("posts", [])[:10]:
        posts_summary.append(
            {
                "id": post.get("id"),
                "topic_id": post.get("topic_id"),
                "post_number": post.get("post_number"),
                "username": post.get("username"),
                "created_at": post.get("created_at"),
                "blurb": _truncate(post.get("blurb")),
                "like_count": post.get("like_count"),
                "url": f"https://community.openai.com/t/{post.get('topic_id')}/{post.get('post_number')}"
                if post.get("topic_id") and post.get("post_number")
                else None,
            }
        )

    return {
        "topics": topics,
        "posts": posts_summary,
        "tags": payload.get("tags", []),
        "categories": payload.get("categories", []),
    }


def _truncate(value: Optional[str], *, limit: int = SUMMARY_CHAR_LIMIT) -> Optional[str]:
    if not value:
        return value
    value = value.strip()
    if len(value) <= limit:
        return value
    # Trim the string and append an ellipsis to signal truncation.
    return value[: limit - 1] + "\u2026"

