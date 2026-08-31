import json
from dataclasses import dataclass

from claude_agent_sdk import (
    AgentDefinition,
    AssistantMessage,
    ClaudeAgentOptions,
    TextBlock,
    ToolResultBlock,
    UserMessage,
    query,
)

synthesis_agent = AgentDefinition(
    description="Combines findings into a cited report",
    prompt=(
        "You are a synthesis agent. You receive a JSON list of findings, "
        "each with claim, source_url, document_name, page_number, confidence, retrieved_by. "
        "Write a report where every claim is followed by a citation "
        "using source_url (if present) or document_name + page_number (if present). "
        "Do not include any claim without a citation."
    ),
    tools=[]
)

async def run_synthesis(all_findings: list) -> str:
    findings_json = json.dumps(all_findings)

    report_text = ""
    async for message in query(
        prompt=f"Using synthesis_agent, write a cited report from these findings: {findings_json}",
        options=options
    ):
        if not isinstance(message, AssistantMessage):
            continue
        for block in message.content:
            if not isinstance(block, TextBlock):
                continue
            report_text += block.text

    return report_text

async def run_coordinator(user_query: str) -> list[dict]:
    all_findings = []

    async for message in query(
        prompt=f"Research this using web_search_agent and document_analysis_agent: {user_query}",
        options=options
    ):
        if not isinstance(message, (AssistantMessage, UserMessage)):
            continue
        for block in message.content:
            if not isinstance(block, ToolResultBlock):
                continue
            if not isinstance(block.content, str):
                continue

            findings = json.loads(block.content)
            all_findings.extend(findings)

    return all_findings

@dataclass
class Finding:
    claim: str                      # content
    source_url: str | None       # metadata
    document_name: str | None    # metadata
    page_number: int | None     # metadata
    confidence: float               # metadata
    retrieved_by: str               # metadata - which subagent produced this

web_search_agent = AgentDefinition(
    description="Searches the web and returns findings with source URLs and titles",
    prompt=(
        "You are a web research agent. Return findings as a JSON list. "
        "Each item must have: claim, source_url, document_name (null), "
        "page_number (null), confidence, retrieved_by='web_search_agent'."
    ),
    tools=["WebSearch"]
)

document_analysis_agent = AgentDefinition(
    description="Analyzes documents and returns findings with page references",
    prompt=(
        "You are a document analysis agent. Return findings as a JSON list. "
        "Each item must have: claim, source_url (null), document_name, "
        "page_number, confidence, retrieved_by='document_analysis_agent'."
    ),
    tools=["Read", "Grep"]
)

options = ClaudeAgentOptions(
    allowed_tools=["Task"],
    agents={
        "web_search_agent": web_search_agent,
        "document_analysis_agent": document_analysis_agent,
        "synthesis_agent": synthesis_agent
    }
)