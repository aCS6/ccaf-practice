import json

import anthropic

client = anthropic.Anthropic()

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
    """Simulated customer lookup."""
    mock_customers = {
        "john@example.com": {"customer_id": "CUST-001", "name": "John Doe", "verified": True},
        "jane@example.com": {"customer_id": "CUST-002", "name": "Jane Smith", "verified": False},
        "john doe":          {"customer_id": "CUST-001", "name": "John Doe", "verified": True},
    }
    key = query.lower().strip()
    customer = mock_customers.get(key, {
        "customer_id": "CUST-999",
        "name": "Unknown",
        "verified": False
    })
    return customer

def lookup_order(order_id: str) -> dict:
    """Simulated order lookup."""
    mock_orders = {
        "ORD-12345": {"order_id": "ORD-12345", "item": "Laptop", "amount": 150.00, "status": "delivered"},
        "ORD-789":   {"order_id": "ORD-789",   "item": "Headphones", "amount": 45.00, "status": "delivered"},
    }
    order = mock_orders.get(order_id, {
        "order_id": order_id,
        "item": "Unknown",
        "amount": 0.0,
        "status": "not found"
    })
    return order

def process_refund(customer_id: str, amount: float) -> dict:
    """Simulated refund processing."""
    return {
        "status": "success",
        "refund_id": f"REF-{customer_id}-{int(amount)}",
        "customer_id": customer_id,
        "amount": amount,
        "message": f"Refund of ${amount} processed successfully for customer {customer_id}"
    }

# ----- Quick Smoke Test -----

if __name__ == "__main__":
    print("=== Tool Definitions ===")
    for tool in tools:
        print(f"  Tool: {tool['name']} — {tool['description']}")

    print("\n=== Mock Function Tests ===")
    print("get_customer:", json.dumps(get_customer("john@example.com"), indent=2))
    print("lookup_order:", json.dumps(lookup_order("ORD-12345"), indent=2))
    print("process_refund:", json.dumps(process_refund("CUST-001", 150.00), indent=2))
