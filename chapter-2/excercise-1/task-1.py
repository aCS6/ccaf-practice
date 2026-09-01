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
                "identifier": {
                    "type": "string",
                }
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
                "identifier": {
                    "type": "string",
                }
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


# ----- Smoke Test -----

if __name__ == "__main__":
    print("=== Ambiguous Tool Definitions ===\n")
    for tool in AMBIGUOUS_TOOLS:
        print(f"  Tool: {tool['name']}")
        print(f"  Description: {tool['description']}")
        print()
