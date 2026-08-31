import os

import anthropic
from dotenv import load_dotenv

load_dotenv()

client = anthropic.Anthropic(
    auth_token=os.environ["ANTHROPIC_API_KEY"],  # agentrouter key sent as Bearer token
    base_url=os.environ.get("ANTHROPIC_BASE_URL"),
)
MODEL = "claude-opus-4-8"
STOP_REASON_TOOL_USE = "tool_use"
STOP_REASON_END_TURN = "end_turn"

tools = [
    {
        "name": "calculator",
        "description": "Evaluate a math expression and return the numeric result.",
        "input_schema": {
            "type": "object",
            "properties": {
                "expression": {
                    "type": "string",
                    "description": "Math expression, e.g. '12 * (4 + 1)'"
                }
            },
            "required": ["expression"]
        }
    },
    {
        "name": "web_search",
        "description": "Search the web and return mock results for a query.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search query"
                }
            },
            "required": ["query"]
        }
    }
]


def run_calculator(expression: str) -> str:
    try:
        result = eval(expression, {"__builtins__": {}}, {})
        return str(result)
    except Exception as e:
        return f"Error: {e}"


def run_web_search(query: str) -> str:
    # Mock stub — replace with a real search call if needed
    return f"Mock search result for '{query}': the value is 42."


def execute_tool(name: str, tool_input: dict) -> str:
    if name == "calculator":
        return run_calculator(tool_input["expression"])
    if name == "web_search":
        return run_web_search(tool_input["query"])
    return f"Unknown tool: {name}"


MAX_ITERATIONS = 20  # safety net only, not the primary stopping mechanism


def run_agent(user_prompt: str) -> str:
    messages = [{"role": "user", "content": user_prompt}]
    counter = 0

    while True:
        counter += 1
        if counter >= MAX_ITERATIONS:
            print("WARNING: hit MAX_ITERATIONS safety cap")
            break

        response = client.messages.create(
            model=MODEL,
            max_tokens=1024,
            tools=tools,
            messages=messages,
        )

        # stop_reason is the authoritative signal — not content-type checks
        if response.stop_reason == STOP_REASON_TOOL_USE:
            messages.append({"role": "assistant", "content": response.content})

            tool_results = []
            for block in response.content:
                if block.type == STOP_REASON_TOOL_USE:
                    result = execute_tool(block.name, block.input)
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": result,
                    })

            messages.append({"role": "user", "content": tool_results})
            continue  # loop again, Claude will react to the tool result

        if response.stop_reason == "end_turn":
            for block in response.content:
                if block.type == "text":
                    return block.text
            return ""

        # any other stop_reason (max_tokens, stop_sequence, etc.)
        return f"Stopped early: {response.stop_reason}"

    return "Stopped: safety cap reached"


if __name__ == "__main__":
    prompt = "Search for 'the value' and then multiply that value by 3."
    print(run_agent(prompt))