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

# ----- Step-4: Valid Empty Result vs Access Failure -----

def handle_not_found(identifier: str) -> dict:
    """
    Valid empty result — query executed successfully but found no matches.
    isError: False  →  do NOT retry, do NOT escalate.
    """
    return {
        "isError":     False,
        "resultCount": 0,
        "message":     (
            f"No customer found matching '{identifier}'. "
            "The query executed successfully but returned no matches."
        ),
    }

def handle_success(identifier: str) -> dict:
    """Successful lookup — returns mock customer profile."""
    return {
        "isError":     False,
        "resultCount": 1,
        "customer": {
            "id":     "CUST-001",
            "email":  identifier,
            "name":   "John Doe",
            "status": "active",
            "tier":   "gold",
        },
    }

# ----- customer_lookup: Dictionary Dispatch -----

def customer_lookup(identifier: str, mode: FailureMode = "success") -> dict:
    """Mock customer database lookup with simulated failure modes."""
    mode_mapper = {
        "success":    lambda: handle_success(identifier),
        "not_found":  lambda: handle_not_found(identifier),
        "timeout":    handle_timeout,
        "invalid":    lambda: handle_invalid(identifier),
        "business":   handle_business,
        "permission": handle_permission,
    }
    return mode_mapper[mode]()

# ----- Smoke Test -----

if __name__ == "__main__":
    print("=== Step-4: Valid Empty Result vs Access Failure ===\n")

    not_found = customer_lookup("ghost@example.com", "not_found")
    timeout   = customer_lookup("ghost@example.com", "timeout")

    print("[not_found] — valid empty result (isError: False)")
    print(json.dumps(not_found, indent=2))
    print(f"  → isError: {not_found['isError']}  | should retry? NO\n")

    print("[timeout] — access failure (isError: True)")
    print(json.dumps(timeout, indent=2))
    print(f"  → isError: {timeout['isError']}  | should retry? {timeout['isRetryable']}\n")

    print("=== All modes ===\n")
    all_modes: list[FailureMode] = ["success", "not_found", "timeout", "invalid", "business", "permission"]
    for mode in all_modes:
        result = customer_lookup("john@example.com", mode)
        is_err = result["isError"]
        retryable = result.get("isRetryable", "n/a")
        category  = result.get("errorCategory", "—")
        print(f"  [{mode:<12}] isError={str(is_err):<5}  isRetryable={str(retryable):<5}  category={category}")
