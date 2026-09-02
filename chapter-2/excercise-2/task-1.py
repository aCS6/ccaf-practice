import json
import os
from typing import Literal

import anthropic
from dotenv import load_dotenv

load_dotenv()

client = anthropic.Anthropic(
    auth_token=os.environ["ANTHROPIC_API_KEY"],
    base_url=os.environ.get("ANTHROPIC_BASE_URL"),
)
MODEL = "claude-opus-4-8"

# ----- Step-1: Tool Definition -----

FailureMode = Literal["success", "not_found", "timeout", "invalid", "business", "permission"]

CUSTOMER_LOOKUP_TOOL: anthropic.types.ToolParam = {
    "name": "customer_lookup",
    "description": (
        "Looks up a customer by email or customer ID (format: CUST-NNNNN). "
        "Returns customer profile on success. "
        "Use the mode parameter to simulate specific failure conditions during testing."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "identifier": {
                "type": "string",
                "description": "Customer email (user@domain.com) or ID (CUST-NNNNN)",
            },
            "mode": {
                "type": "string",
                "enum": ["success", "not_found", "timeout", "invalid", "business", "permission"],
                "description": "Failure mode to simulate. Defaults to success.",
                "default": "success",
            },
        },
        "required": ["identifier"],
    },
}

# ----- Step-3: Structured Metadata Helper -----

def build_error_response(category: str, retryable: bool, description: str) -> dict:
    """
    Builds a consistent error response with all three required metadata fields:
    errorCategory, isRetryable, description.
    Guarantees no field is missing across all error types.
    """
    return {
        "isError":       True,
        "errorCategory": category,
        "isRetryable":   retryable,
        "description":   description,
    }

# ----- Step-2: Error Mode Handlers -----

def handle_timeout() -> dict:
    return build_error_response(
        category="transient",
        retryable=True,
        description=(
            "Customer database timed out after 5 seconds. "
            "The request is valid and should succeed on retry."
        ),
    )

def handle_invalid(identifier: str) -> dict:
    return build_error_response(
        category="validation",
        retryable=False,
        description=(
            f"Invalid identifier format: '{identifier}'. "
            "Expected email (user@domain.com) or customer ID (CUST-NNNNN). "
            "Correct the format and call again."
        ),
    )

def handle_business() -> dict:
    return build_error_response(
        category="business",
        retryable=False,
        description=(
            "Refund of $750 exceeds the $500 automatic limit. "
            "Escalate to a manager with the refund details."
        ),
    )

def handle_permission() -> dict:
    return build_error_response(
        category="permission",
        retryable=False,
        description=(
            "Current service account lacks access to financial records. "
            "Escalate to a senior agent with elevated credentials."
        ),
    )

# ----- customer_lookup: Dictionary Dispatch -----

def customer_lookup(identifier: str, mode: FailureMode = "success") -> dict:
    """Mock customer database lookup with simulated failure modes."""
    default_response = lambda: {"isError": False, "identifier": identifier, "mode": mode}

    mode_mapper = {
        "timeout":    handle_timeout,
        "invalid":    lambda: handle_invalid(identifier),
        "business":   handle_business,
        "permission": handle_permission,
    }

    return mode_mapper.get(mode, default_response)()

# ----- Smoke Test -----

if __name__ == "__main__":
    print("=== Step-3: Structured Metadata Helper ===\n")
    modes: list[FailureMode] = ["timeout", "invalid", "business", "permission"]
    for mode in modes:
        result = customer_lookup("john@example.com", mode)
        print(f"[{mode}]")
        print(json.dumps(result, indent=2))
        # verify all three required fields are present
        assert "errorCategory" in result, f"Missing errorCategory in {mode}"
        assert "isRetryable"   in result, f"Missing isRetryable in {mode}"
        assert "description"   in result, f"Missing description in {mode}"
        print("  ✅ all metadata fields present\n")
