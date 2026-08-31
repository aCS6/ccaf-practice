import json
import os

import anthropic
from dotenv import load_dotenv

load_dotenv()

client = anthropic.Anthropic(
    auth_token=os.environ["ANTHROPIC_API_KEY"],
    base_url=os.environ.get("ANTHROPIC_BASE_URL"),
)
MODEL = "claude-opus-4-8"

# ----- Tool Definitions -----

tools: list[anthropic.types.ToolParam] = [
    {
        "name": "get_customer",
        "description": "Get customer info by customer ID. Returns Unix timestamp and numeric status.",
        "input_schema": {
            "type": "object",
            "properties": {
                "customer_id": {"type": "string", "description": "Customer ID e.g. C-001"}
            },
            "required": ["customer_id"],
        },
    },
    {
        "name": "get_order",
        "description": "Get order details by order ID. Returns ISO 8601 date and string status.",
        "input_schema": {
            "type": "object",
            "properties": {
                "order_id": {"type": "string", "description": "Order ID e.g. ORD-42"}
            },
            "required": ["order_id"],
        },
    },
    {
        "name": "get_shipment",
        "description": "Get shipment status by shipment ID. Returns DD/MM/YYYY date and single-char status.",
        "input_schema": {
            "type": "object",
            "properties": {
                "shipment_id": {"type": "string", "description": "Shipment ID e.g. SHP-7"}
            },
            "required": ["shipment_id"],
        },
    },
]

# ----- Mock Tool Handlers (each uses a different format) -----

def fetch_customer(customer_id: str) -> dict:
    """Returns Unix timestamp + numeric status code."""
    return {
        "customer_id": customer_id,
        "name": "John Doe",
        "created_at": 1710489600,  # Unix timestamp
        "status": 200,             # numeric code
    }

def fetch_order(order_id: str) -> dict:
    """Returns ISO 8601 date + English string status."""
    return {
        "order_id": order_id,
        "item": "Laptop",
        "amount": 150.00,
        "created_at": "2024-03-15T12:00:00Z",  # ISO 8601
        "status": "active",                      # English string
    }

def fetch_shipment(shipment_id: str) -> dict:
    """Returns DD/MM/YYYY date + single-character status."""
    return {
        "shipment_id": shipment_id,
        "carrier": "FastShip",
        "created_at": "15/03/2024",  # DD/MM/YYYY
        "status": "S",               # single char: S=shipped
    }

def execute_tool(name: str, tool_input: dict) -> str:
    if name == "get_customer":
        return json.dumps(fetch_customer(tool_input["customer_id"]))
    if name == "get_order":
        return json.dumps(fetch_order(tool_input["order_id"]))
    if name == "get_shipment":
        return json.dumps(fetch_shipment(tool_input["shipment_id"]))
    return json.dumps({"error": f"Unknown tool: {name}"})

# ----- Smoke Test -----

if __name__ == "__main__":
    print("=== Raw Tool Outputs (before normalisation) ===\n")
    print("get_customer:")
    print(json.dumps(fetch_customer("C-001"), indent=2))
    print("\nget_order:")
    print(json.dumps(fetch_order("ORD-42"), indent=2))
    print("\nget_shipment:")
    print(json.dumps(fetch_shipment("SHP-7"), indent=2))
