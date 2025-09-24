# OpenAI Community MCP Server

This repository provides a Model Context Protocol (MCP) server that wraps the public JSON endpoints of the OpenAI Community forum (Discourse). It exposes forum data as first-class MCP tools and resources so IDEs, agents, and other MCP-aware clients can browse topics, drill into discussions, and search the community directly from their workflows.

## Features

- Streamable HTTP (SHTTP) transport with per-session handling via `Mcp-Session-Id`.
- Async Discourse client built on `httpx` with friendly error surfacing.
- Seven MCP tools covering latest topics, top topics, topic detail, search, categories, tags, and site metadata.
- Resource endpoints for cached snapshots (`categories`, `tags`, `site`).
- Lightweight Starlette app with permissive CORS for local development and MCP Inspector.

## Requirements

- Python 3.10+
- Recommended dependencies: `mcp[cli]`, `uvicorn`, `starlette`, `httpx`

Install them with pip (or use `uv` if you prefer):

```bash
pip install "mcp[cli]" uvicorn starlette httpx
```

## Running the Server

Start the Streamable HTTP server on port 3000:

```bash
uvicorn server:app --host 0.0.0.0 --port 3000
```

The MCP endpoint will be available at `http://localhost:3000/mcp`.

### Connecting with MCP Inspector

1. Launch MCP Inspector.
2. Choose **Streamable HTTP** transport.
3. Set the URL to `http://localhost:3000/mcp`.
4. Invoke tools such as `list_latest_topics(page=1)` or `search_forum(q="prompting")`.

## MCP Tools

| Tool | Description | Key Parameters |
| ---- | ----------- | -------------- |
| `list_latest_topics` | Recent topics from `/latest.json`. | `page` (optional, 1-indexed). |
| `list_top_topics` | Ranked topics from `/top.json`. | `period` (`daily`, `weekly`, `monthly`, `quarterly`, `yearly`, `all`), `page` (optional). |
| `get_topic` | Topic metadata and posts. | `topic_id` (required), `print_posts` (bool, default `False`). |
| `search_forum` | Keyword or operator-based search via `/search.json`. | `q` (required), `page` (optional). |
| `list_categories` | Category listing from `/categories.json`. | `include_subcategories` (bool, default `True`). |
| `list_tags` | Forum tags via `/tags.json`. | _None_. |
| `get_site_info` | Forum metadata snapshot. | _None_. |

Each tool trims responses to concise structures (titles, URLs, authors, timestamps) so downstream agents get digestible context.

## MCP Resources

| Resource URI | Purpose |
| ------------ | ------- |
| `resource://openai-community/categories` | Cached categories payload. |
| `resource://openai-community/tags` | Cached tags payload. |
| `resource://openai-community/site` | Cached site metadata. |

## System Prompt Template

A minimal agent prompt lives in `AGENT.md` and can be adapted as needed. It enumerates the tools, enforces usage of `.json` endpoints, and keeps responses concise with clickable `/t/<slug>/<id>` links.

## Project Structure

```
openai-community-mcp/
  AGENT.md
  server.py
  tools/
    __init__.py
    discourse.py
  resources/
    __init__.py
    categories.py
    tags.py
    site.py
  pyproject.toml
```

## Development Notes

- Network access is restricted to `https://community.openai.com/*`; all endpoints are public GET requests.
- The server is stateless across requests but expects clients to echo the `Mcp-Session-Id` header when provided.
- Update `tools/discourse.py` if you add new forum endpoints or tweak formatting helpers.
- The codebase emphasizes succinct inline comments for non-obvious logic (pagination normalization, truncation, error handling).
- You can extend the server by adding more MCP tools/resources via `FastMCP` decorators in `server.py`.

## Testing

Basic smoke testing can be done by invoking tools through MCP Inspector. For automated checks you can add pytest cases that instantiate the `DiscourseClient` with mocked HTTP responses using `httpx.MockTransport`.

