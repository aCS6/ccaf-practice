"""
Real MCP client test — spawns server.py as a subprocess,
connects via stdio transport, and reads the db schema resource.

Run: uv run chapter-2/excercise-4/test-server.py
"""

import asyncio
import json
import sys
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

SERVER_PATH = Path(__file__).parent / "server.py"


async def test_step4_resource() -> None:
    print("=== Step-4: DB Schema Resource (real MCP connection) ===\n")

    server_params = StdioServerParameters(
        command=sys.executable,
        args=[str(SERVER_PATH)],
    )

    # stdio_client spawns server.py as a subprocess automatically —
    # no need to start server.py manually beforehand.
    # It communicates via stdin/stdout (MCP protocol) and kills the
    # subprocess when the context manager exits.
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            # MCP handshake — exchanges capabilities, negotiates version
            await session.initialize()
            print("  ✅ Connected to db-tools MCP server\n")

            # List available resources
            resources = await session.list_resources()
            print(f"  Resources available: {len(resources.resources)}")
            for r in resources.resources:
                print(f"    • {r.uri}  ({r.mime_type})")
                print(f"      {r.description}")

            # Read the schema resource
            print()
            result = await session.read_resource("db://schema/main")
            raw = result.contents[0].text  # type: ignore[union-attr]
            schema = json.loads(raw)

            print("  Schema tables:")
            for table in schema["tables"]:
                cols = [f"{c['name']}:{c['type']}" for c in table["columns"]]
                print(f"    {table['name']:12} → {', '.join(cols)}")

            print("\n  ✅ Resource read via MCP protocol — no direct import needed.")

            # ── Step-5: List tools and call query_table ───────────────────────
            print("\n=== Step-5: Enhanced Tool Description ===\n")

            tools = await session.list_tools()
            print(f"  Tools available: {len(tools.tools)}")
            for t in tools.tools:
                # Print full description so we can see it's rich, not sparse
                print(f"\n  Tool: {t.name}")
                print(f"  Description:\n    {t.description}")

            # Call query_table with a SELECT
            print("\n  Calling query_table('SELECT * FROM customers')...")
            result = await session.call_tool(
                "query_table",
                {"sql": "SELECT * FROM customers"},
            )
            rows = json.loads(result.content[0].text)  # type: ignore[union-attr]
            print(f"  Rows returned: {len(rows)}")
            for row in rows:
                print(f"    {row}")

            print("\n  ✅ Tool called via MCP protocol — structured JSON rows returned.")


asyncio.run(test_step4_resource())
