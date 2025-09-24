Got it — you want a tailored **AGENT.md** that documents an MCP server which exposes the **OpenAI Community (Discourse) API** via MCP, following the same conventions as the Codex-style `agent.md` I drafted. Here’s a production-ready version you can drop into your MCP project repo.

---

# Agent: OpenAI Community Forum MCP Server

## Purpose

This MCP server exposes **public endpoints of the OpenAI Community (Discourse)** via the **Streamable HTTP transport**.
It allows an agent (or IDE) to query forum data (topics, posts, categories, tags, search results) as MCP tools and resources.

---

## Model & API

* **Transport:** Streamable HTTP (SHTTP) — `/mcp` endpoint served by `FastMCP` or the low-level `simple-streamablehttp` example.
* **Session:** Maintains session IDs via `Mcp-Session-Id` header. Clients must echo it on subsequent calls.
* **Spec:** JSON-RPC 2.0 over HTTP POST + optional SSE streaming.

---

## Tools (Discourse → MCP)

### `list_latest_topics`

* **Description:** Fetch recent topics from `/latest.json`.
* **Params:**

  * `page` (int, optional): page index (default 1).
* **Output:** JSON object with topic titles, URLs, authors, timestamps.

### `list_top_topics`

* **Description:** Fetch “Top” topics from `/top.json`.
* **Params:**

  * `period` (string, enum: daily|weekly|monthly|quarterly|yearly|all).
  * `page` (int, optional).
* **Output:** JSON with ranked topics.

### `get_topic`

* **Description:** Fetch full content of a topic by ID.
* **Params:**

  * `id` (int, required): topic ID.
  * `print` (bool, optional): include up to 1000 posts if true.
* **Output:** JSON with topic metadata and posts.

### `search_forum`

* **Description:** Search the forum via `/search.json`.
* **Params:**

  * `q` (string, required): query string (supports operators like `in:title`, `category:slug`, `after:YYYY-MM-DD`).
  * `page` (int, optional).
* **Output:** JSON array of matched topics and posts.

### `list_categories`

* **Description:** Fetch all categories.
* **Params:**

  * `include_subcategories` (bool, optional, default true).
* **Output:** JSON array of categories and subcategories.

### `list_tags`

* **Description:** List all tags from `/tags.json`.
* **Output:** JSON array of tags.

### `get_site_info`

* **Description:** Fetch site metadata from `/site.json`.
* **Output:** JSON with basic info (title, description, config).

---

## Resources

* **Categories Resource:** `categories.json` snapshot.
* **Tags Resource:** `tags.json` snapshot.
* **Site Metadata Resource:** `site.json`.

Resources can be fetched periodically and cached in the MCP client for browsing context.

---

## System Prompt (template)

Keep this short, following Codex-style minimalism:

```
You are an MCP agent exposing the OpenAI Community forum (Discourse) API.

Tools:
- list_latest_topics(page)
- list_top_topics(period, page)
- get_topic(id, print)
- search_forum(q, page)
- list_categories(include_subcategories)
- list_tags()
- get_site_info()

Rules:
- Always use JSON endpoints (append .json).
- Be concise in responses; summarize forum data as titles, URLs, authors, timestamps.
- Do not dump large JSON blobs unless explicitly requested.
- For searches, support Discourse operators like in:title, category:slug, after:YYYY-MM-DD.
- Reference topics with clickable `/t/<slug>/<id>` links.
```

---

## Sandboxing & Approvals

* **Filesystem:** server does not touch local FS.
* **Network:** outbound requests limited to `https://community.openai.com/*`.
* **Escalation:** not needed; all endpoints are public GETs.
* **Approval policy:** default `never` (no destructive actions possible).

---

## Output & UX

* Summarize results (e.g., topic title + URL + created\_at).
* Use short bullet lists (4–6 items) for scanability.
* File references are not applicable (no repo edits).
* Keep responses concise; provide next-step hints (e.g., “try `get_topic` to read full discussion”).

---

## Project structure

```
openai-community-mcp/
  pyproject.toml
  server.py              # FastMCP Streamable HTTP server
  tools/
    discourse.py         # implements list_latest_topics, search_forum, etc.
  resources/
    categories.py
    tags.py
    site.py
  AGENT.md               # this file
```

---

## Testing

1. Run server:

   ```bash
   uvicorn server:app --reload --port 8000
   ```
2. Connect with **MCP Inspector**:

   * Transport: Streamable HTTP
   * URL: `http://localhost:8000/mcp`
3. Call tools:

   * `list_latest_topics(page=1)`
   * `search_forum(q="prompting")`

---

## References

* **Discourse API (public JSON endpoints):** `/latest.json`, `/top.json`, `/search.json`, `/t/<id>.json`, `/categories.json`, `/tags.json`, `/site.json`.
* **MCP Python SDK:** `FastMCP`, `simple-streamablehttp` example.
* **Cookbook Prompting Guide:** for Codex-style minimal prompts and tool design.

---

Core MCP Frameworks & SDKs

modelcontextprotocol/python-sdk

Official Python SDK for MCP.

Provides FastMCP (declarative tool/resource definitions) and low-level transport primitives.

Includes the examples/servers/simple-streamablehttp reference implementation (your starting point).

FastMCP

High-level API in the SDK for declaring tools/resources quickly.

Can mount a Streamable HTTP app into any ASGI server (e.g., Starlette).

simple-streamablehttp example (GitHub repo)

Located at: examples/servers/simple-streamablehttp in the SDK repo.

Demonstrates a low-level SHTTP server (stateful and stateless variants).

Shows session management, request routing, SSE streaming.

Web Frameworks & Servers

Starlette

Lightweight ASGI framework for mounting the MCP app.

Used with FastMCP (mcp.streamable_http_app()).

Uvicorn

ASGI server for running Starlette apps.

Run with:

uvicorn server:app --reload --port 8000

HTTP Clients (for Discourse API access)

httpx (recommended)

Modern async HTTP client for Python.

Will be used inside your MCP tools to call Discourse endpoints (/latest.json, /search.json, etc.).

(Optional) requests

If you prefer sync calls, but httpx is better in async ASGI contexts.

Testing & Inspection

MCP Inspector

Official debugging tool for MCP servers.

Connects to your SHTTP endpoint (http://localhost:8000/mcp).

Lets you test tool calls and inspect JSON responses interactively.

Discourse API (target integration)

Public JSON endpoints you’ll wrap into MCP tools:

/latest.json

/top.json?period=weekly

/search.json?q=prompting

/t/<topic-id>.json

/categories.json

/tags.json

/site.json

Project Tooling

uv

Fast package/dependency manager (used in the SDK examples).

Example setup:

uv init mcp-streamable-demo
uv add "mcp[cli]" uvicorn starlette httpx


pytest (optional)

For testing your tool wrappers around Discourse endpoints.
