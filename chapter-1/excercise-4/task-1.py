import json
import os

import anthropic
from dotenv import load_dotenv

load_dotenv()

client = anthropic.Anthropic(
    auth_token=os.environ["ANTHROPIC_API_KEY"],  # agentrouter key sent as Bearer token
    base_url=os.environ.get("ANTHROPIC_BASE_URL"),
)
MODEL = "claude-opus-4-8"

# ----- Tool Definitions -----

tools = [
    {
        "name": "get_customer",
        "description": "Look up and verify a customer by name or email",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Customer name or email"
                }
            },
            "required": ["query"]
        }
    },
    {
        "name": "lookup_order",
        "description": "Look up order details by order ID",
        "input_schema": {
            "type": "object",
            "properties": {
                "order_id": {
                    "type": "string",
                    "description": "The order ID to look up"
                }
            },
            "required": ["order_id"]
        }
    },
    {
        "name": "process_refund",
        "description": "Process a refund for a verified customer",
        "input_schema": {
            "type": "object",
            "properties": {
                "customer_id": {
                    "type": "string",
                    "description": "The verified customer ID"
                },
                "amount": {
                    "type": "number",
                    "description": "The refund amount"
                }
            },
            "required": ["customer_id", "amount"]
        }
    }
]

# ----- Mock Tool Implementations -----

def get_customer(query: str) -> dict:
    mock_customers = {
        "john@example.com": {"customer_id": "CUST-001", "name": "John Doe", "verified": True},
        "jane@example.com": {"customer_id": "CUST-002", "name": "Jane Smith", "verified": False},
        "john doe":         {"customer_id": "CUST-001", "name": "John Doe", "verified": True},
    }
    key = query.lower().strip()
    return mock_customers.get(key, {
        "customer_id": "CUST-999",
        "name": "Unknown",
        "verified": False
    })

def lookup_order(order_id: str) -> dict:
    mock_orders = {
        "ORD-12345": {"order_id": "ORD-12345", "item": "Laptop",     "amount": 150.00, "status": "delivered"},
        "ORD-789":   {"order_id": "ORD-789",   "item": "Headphones", "amount":  45.00, "status": "delivered"},
    }
    return mock_orders.get(order_id, {
        "order_id": order_id, "item": "Unknown", "amount": 0.0, "status": "not found"
    })

def process_refund(customer_id: str, amount: float) -> dict:
    return {
        "status": "success",
        "refund_id": f"REF-{customer_id}-{int(amount)}",
        "customer_id": customer_id,
        "amount": amount,
        "message": f"Refund of ${amount} processed successfully for customer {customer_id}"
    }

# ----- Session State (Prerequisite Gate) -----

session_state = {
    "verified_customer_id": None  # None মানে এখনো verify হয়নি
}

def handle_tool_call(name: str, input_data: dict) -> str:
    """
    All tool calls pass through here.
    process_refund is BLOCKED unless get_customer has verified a customer first.
    """
    if name == "get_customer":
        customer = get_customer(input_data["query"])
        # Gate: শুধু verified হলেই session-এ store করো
        if customer["verified"]:
            session_state["verified_customer_id"] = customer["customer_id"]
            print(f"  [GATE] Customer verified and stored: {customer['customer_id']}")
        else:
            print(f"  [GATE] Customer found but NOT verified: {customer['customer_id']}")
        return json.dumps(customer)

    elif name == "lookup_order":
        order = lookup_order(input_data["order_id"])
        return json.dumps(order)

    elif name == "process_refund":
        # GATE: verified_customer_id না থাকলে block করো
        if not session_state["verified_customer_id"]:
            blocked_msg = (
                "BLOCKED: Cannot process refund. "
                "Customer identity not verified. "
                "Call get_customer first to verify the customer."
            )
            print(f"  [GATE] process_refund BLOCKED — no verified customer in session")
            return blocked_msg

        result = process_refund(
            session_state["verified_customer_id"],
            input_data["amount"]
        )
        print(f"  [GATE] process_refund ALLOWED for {session_state['verified_customer_id']}")
        return json.dumps(result)

    return json.dumps({"error": f"Unknown tool: {name}"})

# ----- Agent Runner -----

def run_agent(user_message: str) -> str:
    print(f"\n{'='*60}")
    print(f"USER: {user_message}")
    print(f"{'='*60}")

    messages = [{"role": "user", "content": user_message}]

    while True:
        response = client.messages.create(
            model=MODEL,
            max_tokens=1024,
            tools=tools,
            messages=messages
        )

        # Tool call আছে কিনা চেক করো
        if response.stop_reason == "tool_use":
            # সব tool call গুলো collect করো
            tool_results = []
            for block in response.content:
                if block.type == "tool_use":
                    print(f"\n  [TOOL CALL] {block.name}({json.dumps(block.input)})")
                    result = handle_tool_call(block.name, block.input)
                    print(f"  [TOOL RESULT] {result}")
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": result
                    })

            # Message history update করো
            messages.append({"role": "assistant", "content": response.content})
            messages.append({"role": "user", "content": tool_results})

        else:
            # Final text response
            final_text = next(
                (block.text for block in response.content if hasattr(block, "text")),
                ""
            )
            print(f"\nASSISTANT: {final_text}")
            return final_text

# ----- Smoke Test -----

if __name__ == "__main__":
    # Test: normal flow — get_customer আগে, তারপর process_refund
    session_state["verified_customer_id"] = None  # session reset
    run_agent("Look up customer john@example.com and process a refund of $150 for order ORD-12345.")
