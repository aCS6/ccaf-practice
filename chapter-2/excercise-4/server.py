"""
MCP server — db-tools
Exposes a database schema as an MCP resource and a query tool.

Step-4: resource  → db://schema/main  (read-only catalogue)
Step-5: tool      → query_table        (enhanced description)
"""

import json

from mcp.server.mcpserver import MCPServer

# ── Server ────────────────────────────────────────────────────────────────────
server = MCPServer(
    name="db-tools",
    version="1.0.0",
    description="Exposes the application database schema and query tools.",
)

# ── Schema data ───────────────────────────────────────────────────────────────
DB_SCHEMA = {
    "tables": [
        {
            "name": "customers",
            "columns": [
                {"name": "id",    "type": "INTEGER", "primary_key": True},
                {"name": "email", "type": "TEXT",    "nullable": False},
                {"name": "name",  "type": "TEXT",    "nullable": False},
                {"name": "tier",  "type": "TEXT",    "nullable": True,
                 "values": ["free", "pro", "enterprise"]},
            ],
        },
        {
            "name": "orders",
            "columns": [
                {"name": "id",          "type": "INTEGER", "primary_key": True},
                {"name": "customer_id", "type": "INTEGER", "foreign_key": "customers.id"},
                {"name": "status",      "type": "TEXT",
                 "values": ["pending", "paid", "shipped", "cancelled"]},
                {"name": "total",       "type": "REAL",    "nullable": False},
                {"name": "created_at",  "type": "TEXT",    "nullable": False,
                 "format": "ISO8601"},
            ],
        },
        {
            "name": "products",
            "columns": [
                {"name": "id",       "type": "INTEGER", "primary_key": True},
                {"name": "sku",      "type": "TEXT",    "nullable": False},
                {"name": "name",     "type": "TEXT",    "nullable": False},
                {"name": "price",    "type": "REAL",    "nullable": False},
                {"name": "stock",    "type": "INTEGER", "nullable": False},
            ],
        },
    ]
}


# ── Step-4: Resource — exposes schema as a read-only catalogue ────────────────
# Why resources instead of tools?
# A resource is read-only structured data the agent can inspect *before*
# deciding which tools to call. Without this, an agent would have to call
# list_tables + describe_table for every table — wasting tool calls.
# With this resource, the agent sees the full schema in one read.

@server.resource(
    "db://schema/main",
    name="db-schema",
    description=(
        "Complete database schema: all tables, column names, types, "
        "constraints, foreign keys, and allowed enum values. "
        "Read this resource first to understand the data model before "
        "writing any queries."
    ),
    mime_type="application/json",
)
async def db_schema_resource() -> str:
    return json.dumps(DB_SCHEMA, indent=2)


# ── Entry point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import asyncio
    asyncio.run(server.run_stdio_async())
