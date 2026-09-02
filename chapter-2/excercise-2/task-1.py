"""
এই exercise এ Claude API call নেই, শুধু tool mock করা হচ্ছে
"""
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

# ----- Step-5: Agent Loop with Recovery Branching -----

import time

MAX_RETRIES = 3

def execute_tool(name: str, tool_input: dict) -> str:
    """Dispatch tool call and return JSON string result."""
    if name == "customer_lookup":
        identifier = tool_input.get("identifier", "")
        mode: FailureMode = tool_input.get("mode", "success")
        return json.dumps(customer_lookup(identifier, mode))
    return json.dumps({"isError": True, "errorCategory": "validation",
                       "isRetryable": False, "description": f"Unknown tool: {name}"})


def handle_tool_result(result: dict, tool_input: dict, attempt: int) -> tuple[bool, dict | None]:
    """
    Parse error metadata and decide recovery action.
    Returns (should_continue, next_input_override).
    """
    if not result.get("isError", False):
        if result.get("resultCount", 1) == 0:
            print("  [AGENT] Valid empty result — no matches. Do NOT retry.")
        else:
            print(f"  [AGENT] ✅ Success: {result}")
        return False, None  # stop loop

    category  = result.get("errorCategory", "unknown")
    retryable = result.get("isRetryable", False)
    desc      = result.get("description", "")

    if category == "transient" and retryable and attempt < MAX_RETRIES:
        delay = 2 ** (attempt - 1)  # 1s, 2s, 4s
        print(f"  [AGENT] Transient error. Retrying in {delay}s... (attempt {attempt}/{MAX_RETRIES})")
        time.sleep(delay)
        return True, None  # retry with same input

    if category == "validation":
        print(f"  [AGENT] Validation error: {desc}")
        # fix: use a well-formed identifier
        fixed_input = {**tool_input, "identifier": "CUST-001", "mode": "success"}
        print(f"  [AGENT] Fixed input → {fixed_input}")
        return True, fixed_input

    if category == "business":
        print("  [AGENT] ⚠️  Business rule violation — escalating to human manager.")
        print(f"  [AGENT] Escalation details: {desc}")
        return False, None

    if category == "permission":
        print("  [AGENT] 🔒 Permission denied — requesting elevated credentials.")
        print(f"  [AGENT] Escalation details: {desc}")
        return False, None

    # transient exhausted
    print(f"  [AGENT] ❌ Transient error exceeded {MAX_RETRIES} retries. Giving up.")
    return False, None


def run_agent(user_message: str, initial_mode: FailureMode = "success") -> None:
    """
    Agent loop: calls customer_lookup, reads error metadata,
    branches on errorCategory for recovery.
    """
    print(f"\n{'='*60}")
    print(f"USER: {user_message}")
    print(f"MODE: {initial_mode}")
    print(f"{'='*60}")

    # seed the tool input for the first call
    current_input: dict = {"identifier": "john@example.com", "mode": initial_mode}
    attempt = 0

    while True:
        attempt += 1
        raw = execute_tool("customer_lookup", current_input)
        result = json.loads(raw)
        print(f"\n  [TOOL] customer_lookup({current_input}) →")
        print(f"         {raw}")

        should_continue, next_input = handle_tool_result(result, current_input, attempt)
        if not should_continue:
            break
        if next_input:
            current_input = next_input


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

    print("\n=== Step-5: Agent Loop Recovery Branching ===")
    run_agent("Look up customer john@example.com", initial_mode="success")
    run_agent("Look up customer john@example.com", initial_mode="not_found")
    run_agent("Look up customer john@example.com", initial_mode="timeout")
    run_agent("Look up customer bad-format!!",     initial_mode="invalid")
    run_agent("Process refund for customer",       initial_mode="business")
    run_agent("Access financial records",          initial_mode="permission")
