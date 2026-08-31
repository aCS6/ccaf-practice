import asyncio
import json
from typing import TypedDict

from claude_agent_sdk import (
    AgentDefinition,
    AssistantMessage,
    ClaudeAgentOptions,
    ToolUseBlock,
    query,
)
from claude_agent_sdk.types import ResultMessage

from helpers.logging import log as _log
from helpers.logging import log_message as _log_message
from helpers.logging import write_result_log

# --- Shape documentation (replaces the old @dataclass Finding) ---

class Finding(TypedDict):
    claim: str
    source_url: str | None
    document_name: str | None
    page_number: int | None
    confidence: float
    retrieved_by: str

class ReportItem(TypedDict):
    statement: str
    citation: str

# --- JSON schemas derived from the TypedDicts (used in output_format) ---

FINDINGS_OUTPUT_FORMAT = {
    "type": "json_schema",
    "schema": {
        "type": "object",
        "properties": {
            "findings": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "claim":         {"type": "string"},
                        "source_url":    {"type": ["string", "null"]},
                        "document_name": {"type": ["string", "null"]},
                        "page_number":   {"type": ["integer", "null"]},
                        "confidence":    {"type": "number"},
                        "retrieved_by":  {"type": "string"},
                    },
                    "required": ["claim", "source_url", "document_name", "page_number", "confidence", "retrieved_by"]
                }
            }
        },
        "required": ["findings"]
    }
}

REPORT_OUTPUT_FORMAT = {
    "type": "json_schema",
    "schema": {
        "type": "object",
        "properties": {
            "report": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "statement": {"type": "string"},
                        "citation":  {"type": "string"},
                    },
                    "required": ["statement", "citation"]
                }
            }
        },
        "required": ["report"]
    }
}
MODEL = "claude-opus-4-8"

# --- Agent definitions ---

synthesis_agent = AgentDefinition(
    description="Combines findings into a cited report",
    prompt=(
        "You are a synthesis agent. You receive a JSON list of findings, "
        "each with claim, source_url, document_name, page_number, confidence, retrieved_by. "
        "Return a JSON list of report items. Each item must have: "
        "statement (str) and citation (str, either source_url or 'document_name p.page_number'). "
        "Every statement must have a non-empty citation."
    ),
    tools=[],
    model=MODEL
)

web_search_agent = AgentDefinition(
    description="Searches the web and returns findings with source URLs and titles",
    prompt=(
        "You are a web research agent. "
        "First, try to use the WebSearch tool to find real sources. "
        "If WebSearch is unavailable or returns errors, fall back to your trained knowledge — "
        "do NOT return an empty list. "
        "Return findings as a JSON list. "
        "Each item must have: claim (a specific factual statement), "
        "source_url (a real URL to a credible published source — only include URLs you are confident exist), "
        "document_name (null), page_number (null), "
        "confidence (0.0-1.0), retrieved_by='web_search_agent'. "
        "Return at least 5 findings."
    ),
    tools=["WebSearch"],
    model=MODEL
)

document_analysis_agent = AgentDefinition(
    description="Analyzes documents and returns findings with page references",
    prompt=(
        "You are a document analysis agent. Return findings as a JSON list. "
        "Each item must have: claim, source_url (null), document_name, "
        "page_number, confidence, retrieved_by='document_analysis_agent'."
    ),
    tools=["Read", "Grep"],
    model=MODEL
)

# --- Options (two variants: coordinator uses FINDINGS schema, synthesis uses REPORT schema) ---

coordinator_options = ClaudeAgentOptions(
    model=MODEL,
    # Task spawns sub-agents; WebSearch/Read/Grep are needed so sub-agent
    # tool calls are not blocked by the parent session's permission rules.
    allowed_tools=["Task", "WebSearch", "Read", "Grep"],
    output_format=FINDINGS_OUTPUT_FORMAT,
    include_hook_events=True,
    agents={
        "web_search_agent": web_search_agent,
        "document_analysis_agent": document_analysis_agent,
    }
)

synthesis_options = ClaudeAgentOptions(
    model=MODEL,
    allowed_tools=["Task"],
    output_format=REPORT_OUTPUT_FORMAT,
    include_hook_events=True,
    agents={
        "synthesis_agent": synthesis_agent,
    }
)

# --- Helpers ---


def verify_citations(report_items: list[ReportItem]) -> list[ReportItem]:
    orphaned = [
        item for item in report_items
        if not item.get("citation")
    ]
    return orphaned  # empty list = fully attributed

def verify_parallel_spawn(messages: list) -> bool:
    for message in messages:
        if not isinstance(message, AssistantMessage):
            continue
        task_calls = [
            b for b in message.content
            if isinstance(b, ToolUseBlock) and b.name in ("Task", "Agent")
        ]
        if len(task_calls) >= 2:
            return True  # both spawned in one turn
    return False

# --- Pipeline stages ---

async def run_synthesis(all_findings: list[Finding]) -> list[ReportItem]:
    findings_json = json.dumps(all_findings)

    _log(f"synthesis: starting with {len(all_findings)} findings")
    result: list[ReportItem] = []
    async for message in query(
        prompt=f"Using synthesis_agent, return cited report items as JSON from these findings: {findings_json}",
        options=synthesis_options
    ):
        _log_message("synthesis", message)
        if isinstance(message, ResultMessage) and message.structured_output is not None:
            items = message.structured_output.get("report", [])
            if items:
                result = items
                _log(f"synthesis: got {len(result)} report items via structured_output")

    if not result:
        _log("synthesis: no structured_output received")
        return []

    orphaned = verify_citations(result)
    if orphaned:
        raise ValueError(f"{len(orphaned)} claims missing citation — metadata was likely stripped upstream")
    return result

async def run_coordinator(user_query: str) -> list[Finding]:
    _log("coordinator: starting sub-agent research")
    result: list[Finding] = []
    messages = []
    async for message in query(
        prompt=(
            f"Research this query: {user_query}\n"
            "Spawn web_search_agent and document_analysis_agent as separate Task calls "
            "in the same response, so they run in parallel. "
            "Wait until BOTH tasks have completed before calling StructuredOutput. "
            "Do not call StructuredOutput until you have received completion notifications "
            "for both tasks."
        ),
        options=coordinator_options
    ):
        _log_message("coordinator", message)
        messages.append(message)
        if isinstance(message, ResultMessage) and message.structured_output is not None:
            findings = message.structured_output.get("findings", [])
            if findings:
                result = findings
                _log(f"coordinator: got {len(result)} findings via structured_output")

    if verify_parallel_spawn(messages):
        _log("coordinator: ✔ parallel spawn verified — both agents spawned in one turn")
    else:
        _log("coordinator: ✘ parallel spawn NOT detected — agents may have been spawned sequentially")

    if not result:
        _log("coordinator: no structured_output received")
    return result

async def run_pipeline(user_query: str) -> list[ReportItem]:
    all_findings = await run_coordinator(user_query)
    report_items = await run_synthesis(all_findings)
    write_result_log(user_query, all_findings, report_items)
    return report_items

if __name__ == "__main__":
    result = asyncio.run(run_pipeline("What are the effects of sleep deprivation on memory?"))
    print(json.dumps(result, indent=2))
