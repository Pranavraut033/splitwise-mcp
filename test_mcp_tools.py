#!/usr/bin/env python
"""Manual live smoke test for Splitwise MCP Server tools.

Requires real Splitwise credentials in .env (see SETUP.md) -- this hits the
live API, unlike tests/ which use httpx.MockTransport and run in CI. Not
part of the pytest suite; run directly:

    python test_mcp_tools.py
"""

import asyncio
from fastmcp import Client
from splitwise_mcp_server.server import create_server


async def test_tools():
    """Call a handful of read-only tools through a real in-process client."""
    print("=" * 70)
    print("Testing Splitwise MCP Server Tools (live API)")
    print("=" * 70)
    print()

    server = create_server()
    async with Client(server) as client:
        print("1. Testing get_current_user tool...")
        result = await client.call_tool("get_current_user", {})
        print(f"   Success: user id={result.data.get('user', {}).get('id')}")
        print()

        print("2. Testing get_friends tool...")
        result = await client.call_tool("get_friends", {})
        print(f"   Success: {len(result.data.get('friends', []))} friends")
        print()

        print("3. Testing get_groups tool...")
        result = await client.call_tool("get_groups", {})
        print(f"   Success: {len(result.data.get('groups', []))} groups")
        print()

        print("4. Testing get_categories tool...")
        result = await client.call_tool("get_categories", {})
        print(f"   Success: {len(result.data.get('categories', []))} categories")
        print()

        print("5. Testing get_currencies tool...")
        result = await client.call_tool("get_currencies", {})
        print(f"   Success: {len(result.data.get('currencies', []))} currencies")
        print()

        print("6. Testing resolve_category tool (fuzzy matching)...")
        result = await client.call_tool("resolve_category", {"query": "food"})
        print(f"   Success: {len(result.data)} matches")
        print()

    print("=" * 70)
    print("All MCP tool smoke tests passed!")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(test_tools())
