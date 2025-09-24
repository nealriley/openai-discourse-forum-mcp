# Agent: OpenAI Community Forum MCP Server

## Purpose

Expose the public JSON endpoints of the OpenAI Community (Discourse) forum as Model Context Protocol (MCP) tools and resources using the Streamable HTTP transport.

## Transport & Runtime

- **Transport:** Streamable HTTP (`/mcp` path) served via `FastMCP.streamable_http_app()`
- **Server:** Starlette app with CORS enabled (exposes `Mcp-Session-Id` header)
- **Port:** `3000` (adjust `DEFAULT_PORT` in `server.py` if needed)
- **Entry point:** `python -m uvicorn server:app --host 0.0.0.0 --port 3000`

## Tools

| Tool | Description | Key Params |
| --- | --- | --- |
| `list_latest_topics` | Recent topics from `/latest.json` | `page` (int, default 1) |
| `list_top_topics` | Ranked topics from `/top.json` | `period` (enum: daily, weekly, monthly, quarterly, yearly, all), `page` (int?) |
| `get_topic` | Topic details + posts | `topic_id` (int), `print_posts` (bool) |
| `search_forum` | `/search.json` results | `q` (str), `page` (int?) |
| `list_categories` | Categories snapshot | `include_subcategories` (bool) |
| `list_tags` | Tag metadata | — |
| `get_site_info` | Site metadata | — |

Each tool trims and formats responses (topic summaries, post excerpts limited to 500 chars) for agent-friendly consumption.

## Resources

- `resource://openai-community/categories`
- `resource://openai-community/tags`
- `resource://openai-community/site`

Resources return JSON payloads that clients can cache for context browsing.

## System Prompt Template

```
You are an MCP agent exposing the OpenAI Community forum (Discourse) API.
Tools:
- list_latest_topics(page)
- list_top_topics(period, page)
- get_topic(topic_id, print_posts)
- search_forum(q, page)
- list_categories(include_subcategories)
- list_tags()
- get_site_info()
Rules:
- Always hit the `.json` endpoints.
- Summarize outputs with titles, URLs, timestamps, authors.
- Avoid dumping full JSON unless explicitly requested.
- Support Discourse search operators like `in:title`, `category:slug`, `after:YYYY-MM-DD`.
- Link topics as `/t/<slug>/<id>`.
```

## Project Layout

```
pyproject.toml
server.py
README.md
resources/
  categories.py
  site.py
  tags.py
tools/
  discourse.py
AGENT.md
TASKS.md
```

## Testing & Debugging

1. `python -m uvicorn server:app --host 0.0.0.0 --port 3000`
2. Connect MCP Inspector to `http://localhost:3000/mcp`
3. Invoke tools (`list_latest_topics`, `search_forum`, etc.) and inspect resource snapshots.

## Operational Guardrails

- Outbound requests limited to `https://community.openai.com/*`
- No local filesystem writes from tools/resources
- CORS exposes `Mcp-Session-Id` for browser-based clients
- No special approvals needed; endpoints are public GETs

