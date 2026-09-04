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


# ── Step-5: Tool with enhanced description ───────────────────────────────────
# Why enhanced descriptions matter:
# A sparse description ("Queries a table") gives the agent no reason to prefer
# this tool over built-in alternatives like Grep or Bash+sqlite3.
# An enhanced description explains WHAT it does, WHAT it returns, WHEN to use
# it, and HOW it compares to alternatives — giving the agent enough signal to
# make the right choice.

# BEFORE (sparse — agent will prefer built-in tools):
# description="Queries a database table"

# AFTER (enhanced — agent can make an informed choice):
@server.tool(
    name="query_table",
    description=(
        "Executes a read-only SQL SELECT query against the application database "
        "and returns results as a JSON array of row objects. "
        "Each row is a dict keyed by column name, preserving types (int, float, str). "
        "Use this instead of Bash+sqlite3 when you need structured, typed results "
        "you can filter or aggregate in subsequent steps — Bash+sqlite3 returns raw "
        "text that requires manual parsing. "
        "Always read the db://schema/main resource first to confirm table and column "
        "names before writing a query."
    ),
)
async def query_table(sql: str) -> str:
    """
    sql: A SELECT statement to execute. Only SELECT is allowed — writes are rejected.
    """
    # Mock implementation — returns fake rows for demonstration
    if "customers" in sql.lower():
        rows = [
            {"id": 1, "email": "alice@example.com", "name": "Alice", "tier": "pro"},
            {"id": 2, "email": "bob@example.com",   "name": "Bob",   "tier": "free"},
        ]
    elif "orders" in sql.lower():
        rows = [
            {"id": 101, "customer_id": 1, "status": "paid",    "total": 49.99},
            {"id": 102, "customer_id": 2, "status": "pending", "total": 12.50},
        ]
    elif "products" in sql.lower():
        rows = [
            {"id": 1, "sku": "PRD-001", "name": "Widget A", "price": 9.99,  "stock": 100},
            {"id": 2, "sku": "PRD-002", "name": "Widget B", "price": 24.99, "stock": 45},
        ]
    else:
        rows = []

    return json.dumps(rows, indent=2)


# ── Entry point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import asyncio
    asyncio.run(server.run_stdio_async())
