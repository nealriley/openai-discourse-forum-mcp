"""FastMCP Streamable HTTP server exposing the OpenAI Community forum API."""

from __future__ import annotations

from collections.abc import Awaitable
from typing import Any, Dict, Optional

import httpx
from mcp.server.fastmcp import FastMCP
from starlette.applications import Starlette
from starlette.middleware.cors import CORSMiddleware

from tools.discourse import (
    DiscourseClient,
    format_posts,
    format_search_results,
    format_topics,
)

SERVER_NAME = "OpenAICommunityForumMCP"
STREAMABLE_HTTP_PATH = "/mcp"
DEFAULT_HOST = "0.0.0.0"
DEFAULT_PORT = 3000
VALID_PERIODS = {"daily", "weekly", "monthly", "quarterly", "yearly", "all"}

mcp = FastMCP(SERVER_NAME, stateless_http=True)
_discourse_client = DiscourseClient()


async def _safe_execute(coro: Awaitable[Dict[str, Any]]) -> Dict[str, Any]:
    # Surface HTTP failures with descriptive errors so MCP clients return actionable messages.
    try:
        return await coro
    except httpx.HTTPStatusError as exc:
        status = exc.response.status_code
        detail = exc.response.text[:200]
        raise RuntimeError(f"Discourse API returned HTTP {status}: {detail}") from exc
    except httpx.HTTPError as exc:
        raise RuntimeError(f"Failed to reach Discourse API: {exc}") from exc


def _normalize_page(page: int | None) -> Optional[int]:
    # Discourse uses zero-based pagination while MCP callers expect one-based indices.
    if page is None:
        return None
    if page < 1:
        raise ValueError("page must be >= 1")
    return page - 1


@mcp.tool("list_latest_topics", description="Fetch recent topics from /latest.json")
async def list_latest_topics(page: int = 1) -> Dict[str, Any]:
    api_page = _normalize_page(page)
    payload = await _safe_execute(_discourse_client.get_latest_topics(api_page or 0))
    topic_list = payload.get("topic_list", {})
    topics = format_topics(topic_list.get("topics", []))
    return {
        "page": page,
        "topic_count": len(topics),
        "topics": topics,
        "more_topics_url": topic_list.get("more_topics_url"),
        "top_tags": topic_list.get("top_tags", []),
    }


@mcp.tool("list_top_topics", description="Fetch ranked topics from /top.json")
async def list_top_topics(period: str, page: Optional[int] = None) -> Dict[str, Any]:
    period = period.lower()
    if period not in VALID_PERIODS:
        raise ValueError(f"Unsupported period '{period}'. Expected one of: {', '.join(sorted(VALID_PERIODS))}")

    # Only pass a page value when requested to let Discourse apply its own defaults otherwise.
    api_page = _normalize_page(page) if page is not None else None
    payload = await _safe_execute(_discourse_client.get_top_topics(period, api_page))
    topic_list = payload.get("topic_list", {})
    topics = format_topics(topic_list.get("topics", []))
    return {
        "period": period,
        "page": page,
        "topic_count": len(topics),
        "topics": topics,
        "top_tags": topic_list.get("top_tags", []),
    }


@mcp.tool("get_topic", description="Fetch topic metadata and posts by topic ID")
async def get_topic(topic_id: int, print_posts: bool = False) -> Dict[str, Any]:
    payload = await _safe_execute(_discourse_client.get_topic(topic_id, print_mode=print_posts))
    posts = payload.get("post_stream", {}).get("posts", [])
    return {
        "id": payload.get("id"),
        "title": payload.get("fancy_title") or payload.get("title"),
        "slug": payload.get("slug"),
        "created_at": payload.get("created_at"),
        "last_posted_at": payload.get("last_posted_at"),
        "posts_count": payload.get("posts_count"),
        "views": payload.get("views"),
        "reply_count": payload.get("reply_count"),
        "tags": payload.get("tags", []),
        "url": f"https://community.openai.com/t/{payload.get('slug')}/{payload.get('id')}" if payload.get("id") else None,
        "posts": format_posts(posts, limit=50 if print_posts else 10),
        "suggested_topics": format_topics(payload.get("suggested_topics", [])),
    }


@mcp.tool("search_forum", description="Search the forum via /search.json")
async def search_forum(q: str, page: Optional[int] = None) -> Dict[str, Any]:
    if not q:
        raise ValueError("Query string 'q' cannot be empty")
    api_page = _normalize_page(page) if page is not None else None
    # Search responses contain mixed topic/post arrays; helpers trim and structure them for MCP.
    payload = await _safe_execute(_discourse_client.search(q, api_page))
    return {
        "query": q,
        "page": page,
        "results": format_search_results(payload),
    }


@mcp.tool("list_categories", description="Fetch all categories from /categories.json")
async def list_categories(include_subcategories: bool = True) -> Dict[str, Any]:
    payload = await _safe_execute(_discourse_client.list_categories())
    categories = payload.get("category_list", {}).get("categories", [])
    if not include_subcategories:
        # Drop nested categories to keep the payload limited to top-level entries.
        categories = [c for c in categories if not c.get("parent_category_id")]
    return {
        "count": len(categories),
        "categories": categories,
    }


@mcp.tool("list_tags", description="Fetch tags from /tags.json")
async def list_tags() -> Dict[str, Any]:
    payload = await _safe_execute(_discourse_client.list_tags())
    tags = payload.get("tags", [])
    return {
        "count": len(tags),
        "tags": tags,
    }


@mcp.tool("get_site_info", description="Fetch site metadata from /site.json")
async def get_site_info() -> Dict[str, Any]:
    payload = await _safe_execute(_discourse_client.get_site_info())
    return {
        "title": payload.get("title"),
        "description": payload.get("description"),
        "contact_email": payload.get("contact_email"),
        "logo_url": payload.get("logo_url"),
        "topics": payload.get("topics_count"),
        "users": payload.get("user_count"),
        "groups": payload.get("group_count"),
    }


@mcp.resource("resource://openai-community/categories", title="OpenAI Community Categories")
async def categories_resource() -> Dict[str, Any]:
    return await list_categories()


@mcp.resource("resource://openai-community/tags", title="OpenAI Community Tags")
async def tags_resource() -> Dict[str, Any]:
    return await list_tags()


@mcp.resource("resource://openai-community/site", title="OpenAI Community Site Metadata")
async def site_resource() -> Dict[str, Any]:
    return await get_site_info()


app = mcp.streamable_http_app()
app.add_middleware(
    CORSMiddleware,
    # Allow cross-origin requests so IDE plug-ins and the MCP Inspector can connect during development.
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["Mcp-Session-Id"],
)


def main() -> None:
    import uvicorn

    uvicorn.run(
        "server:app",
        host=DEFAULT_HOST,
        port=DEFAULT_PORT,
        reload=False,
    )


if __name__ == "__main__":
    main()
