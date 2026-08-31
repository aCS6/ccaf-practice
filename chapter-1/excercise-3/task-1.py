from dataclasses import dataclass

from claude_agent_sdk import AgentDefinition, ClaudeAgentOptions, query


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
        "document_analysis_agent": document_analysis_agent
    }
)