# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Install (editable, with dev deps)
pip install -e ".[dev]"

# Run full test suite (coverage is enforced via pyproject.toml addopts)
pytest

# Run a single test file / test
pytest tests/test_client.py
pytest tests/test_client.py::TestRetryLogic::test_retries_on_500

# Manual live smoke test — hits the real Splitwise API, requires real
# credentials in .env (see SETUP.md). Not part of the pytest suite.
python test_mcp_tools.py

# Generate a fresh OAuth token interactively, writes to .env
python -m splitwise_mcp_server.oauth_setup

# Run the server directly (stdio transport, for local MCP clients)
python -m splitwise_mcp_server

# Run over HTTP instead (for remote hosting, e.g. Prefect Horizon)
FASTMCP_TRANSPORT=http python -m splitwise_mcp_server
```

There is no linter/formatter configured in this repo (no ruff/black/flake8 config) — don't invent one.

## Architecture

This is a FastMCP server exposing the Splitwise API as 27 MCP tools, structured as thin layers:

```
server.py (tool definitions, validation)
    -> client.py (SplitwiseClient: HTTP + auth + retry + error mapping)
    -> auth.py (OAuth2Handler / APIKeyHandler — both just build a Bearer header)
resolver.py (EntityResolver, fuzzy name->ID matching, sits alongside client.py)
cache.py (CacheManager, used only for categories/currencies)
config.py (env-var loading, SplitwiseConfig.from_env())
errors.py (ValidationError/RateLimitError/MCPError + all validate_* helpers)
```

**Global state and lifespan**: `server.py`'s `client` and `resolver` are module-level globals,
populated inside `lifespan()` (an `@asynccontextmanager` passed to `FastMCP(..., lifespan=lifespan)`).
They are `None` until the server's lifespan actually runs — calling a tool function directly
without going through a running server (or `fastmcp.Client`) will fail. `create_server()` builds
the `FastMCP` instance and registers tools but does not start the lifespan.

Two lifespan entrypoints exist for the same `create_server()`:
- `__main__.py` — CLI entrypoint; picks stdio (default) or HTTP transport based on
  `FASTMCP_TRANSPORT`/`--http`.
- `app.py` — module-level `mcp = create_server()`, the entrypoint Prefect Horizon (or anything
  expecting `app.py:mcp`) needs; configured via `fastmcp.json`.

**Splitwise's own quirks that shape the code**:
- The API returns `200 OK` even for failed writes — success/failure is only knowable from the
  response body (`errors` non-empty, or `success: false`). `client._validate_write_response()`
  is the single place this is checked; every `post()` call runs through it.
- `429` responses raise `RateLimitError` (with `retry_after` from the header) and are never
  auto-retried. Only `500`/`502`/`503` get one retry with a fixed 2s backoff
  (`RETRYABLE_STATUS_CODES`, `MAX_RETRIES` in `client.py`).
- Splitwise's write endpoints expect flattened form keys (`users__0__user_id`, not a nested
  `users` array) — `client._flatten_data()` handles this on every POST.
- An expense's `cost` is the **group total**, not any individual's share — a caller wanting
  "my spend" must find their own entry in the expense's `users[]` array and read `owed_share`
  (a numeric string, e.g. `"0.0"` — parse as `Decimal`, not `float`). `paid_share` is what was
  fronted, `net_balance` is owed minus paid; neither is "my spend."
- Expenses can carry `deleted_at` (soft-deleted) or `payment: true` (a settle-up, not a real
  expense) — both occur in ordinary `get_expenses` results and must be filtered by any consumer
  doing spend analysis, not just handled hypothetically.
- Splitwise's category taxonomy reuses the leaf name `"Other"` under every parent category
  (Utilities:Other, Transportation:Other, Life:Other, ...) — the expense payload only exposes
  the leaf name, not its parent, so disambiguating "Other" by parent isn't possible from a
  single expense record.

**Validation pattern**: every tool in `server.py` validates inputs via `errors.py`'s
`validate_*` helpers (e.g. `validate_currency_code`, `validate_user_split`) *before* calling
into `client.py`, and re-raises `ValidationError`/`RateLimitError` as-is while wrapping other
exceptions in logging. Follow this same validate-then-call pattern when adding a new tool.

**Caching**: only `get_categories`/`get_currencies` are cached (`CacheManager`, TTL from
`SPLITWISE_CACHE_TTL`, default 24h) — everything else hits the API live every call.
`EntityResolver` has its own separate in-memory cache for friends/groups lists (not the same
`CacheManager`), invalidated explicitly via `resolver.clear_cache()` whenever a tool mutates
friends or groups (see `create_group`, `delete_group`, `create_friend`, `delete_friend` in
`server.py`).

**Entity resolution** (`resolver.py`): fuzzy name matching (`rapidfuzz.fuzz.token_sort_ratio`)
over friends/groups/categories, used so an agent can pass "John" or "roommates" instead of a
numeric ID. `resolve_category` flattens categories+subcategories and matches on
`"{parent} - {subcategory}"` for subcategories — this is a *text-search* helper (name to
Splitwise ID), the reverse direction of mapping a Splitwise category onto some other fixed
taxonomy.

## Testing

`tests/` uses `httpx.MockTransport` to fake HTTP responses — no real network calls, no live
credentials needed. `test_mcp_tools.py` at the repo root is the opposite: a manual smoke test
that calls the real Splitwise API via `fastmcp.Client(create_server())`, requires real
credentials in `.env`, and is intentionally excluded from the pytest suite (`testpaths =
["tests"]` in `pyproject.toml`).
