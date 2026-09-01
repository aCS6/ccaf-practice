import os

import anthropic
from dotenv import load_dotenv

load_dotenv()

client = anthropic.Anthropic(
    auth_token=os.environ["ANTHROPIC_API_KEY"],
    base_url=os.environ.get("ANTHROPIC_BASE_URL"),
)
MODEL = "claude-opus-4-8"

# ----- Step-1: Ambiguous Tool Definitions -----
# Intentionally vague — no input formats, no examples, no boundaries

AMBIGUOUS_TOOLS: list[anthropic.types.ToolParam] = [
    {
        "name": "get_customer",
        "description": "Retrieves customer information.",
        "input_schema": {
            "type": "object",
            "properties": {
                "identifier": {"type": "string"}
            },
            "required": ["identifier"],
        },
    },
    {
        "name": "lookup_order",
        "description": "Retrieves order details.",
        "input_schema": {
            "type": "object",
            "properties": {
                "identifier": {"type": "string"}
            },
            "required": ["identifier"],
        },
    },
]

# ----- Mock Handlers -----

def handle_tool(name: str, identifier: str) -> str:
    if name == "get_customer":
        return f"Customer profile for: {identifier}"
    if name == "lookup_order":
        return f"Order details for: {identifier}"
    return "Unknown tool"

# ----- Step-2: Test Harness -----

# Expected correct tool for each query
QUERIES: list[tuple[str, str]] = [
    ("What is the status of order #12345?",          "lookup_order"),
    ("Look up customer john@example.com",             "get_customer"),
    ("Check my order tracking",                       "lookup_order"),
    ("Find the account for phone 555-0123",           "get_customer"),
    ("Where is my package?",                          "lookup_order"),
    ("Is order #67890 eligible for a refund?",        "lookup_order"),
    ("What loyalty tier is this customer?",           "get_customer"),
    ("I need details on order #11111",                "lookup_order"),
    ("Verify the customer account status",            "get_customer"),
    ("When will order #99999 arrive?",                "lookup_order"),
]

def run_query(query: str, tools: list[anthropic.types.ToolParam]) -> str | None:
    """Send a single query and return the tool name selected by the model."""
    response = client.messages.create(
        model=MODEL,
        max_tokens=1024,
        tools=tools,
        tool_choice={"type": "any"},  # force model to pick a tool
        messages=[{"role": "user", "content": query}],
    )
    for block in response.content:
        if block.type == "tool_use":
            return block.name
    return None

def test_tool_selection(
    tools: list[anthropic.types.ToolParam],
    label: str,
) -> list[dict]:
    """Run all 10 queries and log results. Returns result dicts for comparison."""
    print(f"\n{'='*65}")
    print(f"{label}")
    print(f"{'='*65}")
    print(f"  {'RESULT':<8} {'SELECTED':<16} {'EXPECTED':<16} QUERY")
    print(f"  {'-'*60}")

    results = []
    correct = 0
    for query, expected in QUERIES:
        selected = run_query(query, tools)
        is_correct = selected == expected
        if is_correct:
            correct += 1
        status = "✅" if is_correct else "❌"
        print(f"  {status:<8} {(selected or 'none'):<16} {expected:<16} {query}")
        results.append({
            "query":    query,
            "expected": expected,
            "selected": selected,
            "correct":  is_correct,
        })

    print(f"\n  Accuracy: {correct}/{len(QUERIES)} ({correct/len(QUERIES)*100:.0f}%)")
    return results


# ----- Step-3: Improved Tool Definitions -----
# Purpose, input formats, examples, edge cases, explicit boundaries

IMPROVED_TOOLS: list[anthropic.types.ToolParam] = [
    {
        "name": "get_customer",
        "description": (
            "Looks up a customer account by email address, phone number, or customer ID. "
            "Returns customer profile including name, contact details, account status, and loyalty tier. "
            "Use this when the query is about WHO the customer is — verifying identity, checking account standing, "
            "or retrieving profile details. "
            "Accepted formats: email (e.g. john@example.com), phone (e.g. 555-0123), or customer ID (e.g. CUST-001). "
            "Do NOT use for order-specific queries such as tracking, delivery status, or refund eligibility — "
            "use lookup_order for those."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "identifier": {
                    "type": "string",
                    "description": "Customer email, phone number, or customer ID",
                }
            },
            "required": ["identifier"],
        },
    },
    {
        "name": "lookup_order",
        "description": (
            "Looks up an order by order number and returns order details including status, items, "
            "delivery estimate, tracking information, and refund eligibility. "
            "Use this when the query is about a specific order — tracking a package, checking delivery, "
            "asking about refunds, or getting order status. "
            "Accepted formats: order number with or without hash (e.g. #12345 or 12345). "
            "Do NOT use for customer account or profile queries — use get_customer for those."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "identifier": {
                    "type": "string",
                    "description": "Order number, e.g. #12345 or 12345",
                }
            },
            "required": ["identifier"],
        },
    },
]


if __name__ == "__main__":
    # Step-2: test with ambiguous descriptions
    ambiguous_results = test_tool_selection(AMBIGUOUS_TOOLS, "STEP-2: AMBIGUOUS DESCRIPTIONS")

    # Step-4: re-run with improved descriptions and compare
    improved_results = test_tool_selection(IMPROVED_TOOLS, "STEP-4: IMPROVED DESCRIPTIONS")

    # Before / After comparison table
    print(f"\n{'='*65}")
    print("STEP-4: BEFORE vs AFTER COMPARISON")
    print(f"{'='*65}")
    print(f"  {'BEFORE':<10} {'AFTER':<10} QUERY")
    print(f"  {'-'*60}")
    for before, after in zip(ambiguous_results, improved_results):
        b = "✅" if before["correct"] else f"❌ {before['selected'] or 'none'}"
        a = "✅" if after["correct"] else f"❌ {after['selected'] or 'none'}"
        print(f"  {b:<10} {a:<10} {before['query']}")

    before_acc = sum(r["correct"] for r in ambiguous_results)
    after_acc  = sum(r["correct"] for r in improved_results)
    print(f"\n  Accuracy before: {before_acc}/10 ({before_acc*10}%)")
    print(f"  Accuracy after:  {after_acc}/10  ({after_acc*10}%)")
    print(f"  Improvement:     +{after_acc - before_acc} queries correct")
