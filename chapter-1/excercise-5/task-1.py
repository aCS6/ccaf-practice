import json
import os
from datetime import datetime, timezone

import anthropic
from dotenv import load_dotenv

load_dotenv()

client = anthropic.Anthropic(
    auth_token=os.environ["ANTHROPIC_API_KEY"],
    base_url=os.environ.get("ANTHROPIC_BASE_URL"),
)
MODEL = "claude-opus-4-8"

STATUS_MAP = {
    "200": "active",
    "404": "not_found",
    "500": "error",
    "S":   "shipped",
    "P":   "pending",
    "C":   "cancelled",
}

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

# ----- PostToolUse Hook -----

def post_tool_use_hook(tool_name: str, raw_result: dict) -> dict:
    """
    Intercepts tool results before the model sees them.
    Normalises created_at → ISO 8601, status → human-readable English.
    """
    normalised = raw_result.copy()

    # Normalise date
    created_at = raw_result.get("created_at")
    if isinstance(created_at, int):
        # Unix timestamp → ISO 8601
        normalised["created_at"] = datetime.fromtimestamp(
            created_at, tz=timezone.utc
        ).strftime("%Y-%m-%dT%H:%M:%SZ")
        print(f"  [HOOK] {tool_name}: Unix {created_at} → {normalised['created_at']}")
    elif isinstance(created_at, str) and "/" in created_at:
        # DD/MM/YYYY → ISO 8601
        dt = datetime.strptime(created_at, "%d/%m/%Y")
        normalised["created_at"] = dt.strftime("%Y-%m-%dT00:00:00Z")
        print(f"  [HOOK] {tool_name}: DD/MM/YYYY {created_at} → {normalised['created_at']}")

    # Normalise status
    status_key = str(raw_result.get("status", ""))
    if status_key in STATUS_MAP:
        normalised["status"] = STATUS_MAP[status_key]
        print(f"  [HOOK] {tool_name}: status {status_key!r} → {normalised['status']!r}")

    return normalised

# ----- Agent Runner -----

MAX_ITERATIONS = 20

def run_agent(user_message: str) -> str:
    print(f"\n{'='*60}")
    print(f"USER: {user_message}")
    print(f"{'='*60}")

    messages: list[anthropic.types.MessageParam] = [
        {"role": "user", "content": user_message}
    ]

    for _ in range(MAX_ITERATIONS):
        response = client.messages.create(
            model=MODEL,
            max_tokens=1024,
            tools=tools,
            messages=messages,
        )

        if response.stop_reason == "tool_use":
            tool_results: list[anthropic.types.ToolResultBlockParam] = []
            for block in response.content:
                if block.type == "tool_use":
                    print(f"\n  [TOOL CALL] {block.name}({json.dumps(block.input)})")
                    raw = json.loads(execute_tool(block.name, block.input))

                    # PostToolUse hook — normalise before model sees it
                    normalised = post_tool_use_hook(block.name, raw)

                    print(f"  [TOOL RESULT] {json.dumps(normalised)}")
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": json.dumps(normalised),
                    })

            messages.append({"role": "assistant", "content": response.content})
            messages.append({"role": "user", "content": tool_results})  # type: ignore[arg-type]

        else:
            final_text = next(
                (block.text for block in response.content if block.type == "text"),
                ""
            )
            print(f"\nASSISTANT: {final_text}")
            return final_text

    return "Stopped: safety cap reached"

# ----- Smoke Test: PostToolUse Hook -----

if __name__ == "__main__":

    # Verify: model সব normalized data দেখছে কিনা
    print("\n" + "="*60)
    run_agent(
        "Look up customer C-001, find their order ORD-42, "
        "and check shipment SHP-7 status. "
        "Summarise the dates and statuses you find."
    )

