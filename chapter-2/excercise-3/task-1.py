import os

import anthropic
from dotenv import load_dotenv

load_dotenv()

client = anthropic.Anthropic(
    auth_token=os.environ["ANTHROPIC_API_KEY"],
    base_url=os.environ.get("ANTHROPIC_BASE_URL"),
)
MODEL = "claude-opus-4-8"

# ----- Step-1: Three Agent Roles with Scoped Tools -----
# Each agent gets exactly 4-5 tools scoped to its role.
# No tool appears in more than one agent (except scoped cross-role tools added later).

AgentToolset = dict[str, list[anthropic.types.ToolParam] | str]

WEB_SEARCH_TOOLS: list[anthropic.types.ToolParam] = [
    {
        "name": "search_web",
        "description": (
            "Searches the web for a query and returns ranked results with titles, "
            "URLs, and snippets. Use for discovering relevant sources on a topic."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query"},
                "max_results": {"type": "integer", "description": "Max results to return (default 10)"},
            },
            "required": ["query"],
        },
    },
    {
        "name": "fetch_page",
        "description": (
            "Fetches the full text content of a web page by URL. "
            "Use after search_web to read the full content of a result."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "url": {"type": "string", "description": "Full URL of the page to fetch"},
            },
            "required": ["url"],
        },
    },
    {
        "name": "extract_links",
        "description": (
            "Extracts all hyperlinks from a fetched web page. "
            "Use to discover referenced sources or follow a citation chain."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "url": {"type": "string", "description": "URL of the page to extract links from"},
            },
            "required": ["url"],
        },
    },
    {
        "name": "save_snippet",
        "description": (
            "Saves a text snippet with its source URL for later use by other agents. "
            "Use to preserve relevant excerpts found during web search."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "text":      {"type": "string", "description": "Text snippet to save"},
                "source_url": {"type": "string", "description": "URL where the snippet was found"},
                "topic":     {"type": "string", "description": "Topic label for retrieval"},
            },
            "required": ["text", "source_url"],
        },
    },
]

DOCUMENT_ANALYSIS_TOOLS: list[anthropic.types.ToolParam] = [
    {
        "name": "extract_metadata",
        "description": (
            "Extracts title, author, publication date, and document type from a document. "
            "Always run this as the FIRST step when analysing a new document."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "document_id": {"type": "string", "description": "ID or URL of the document"},
            },
            "required": ["document_id"],
        },
    },
    {
        "name": "extract_data_points",
        "description": (
            "Extracts structured data fields from a document: dates, amounts, names, "
            "statistics, and key entities. Use after extract_metadata."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "document_id": {"type": "string", "description": "ID or URL of the document"},
                "fields": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Specific field types to extract (e.g. dates, amounts, names)",
                },
            },
            "required": ["document_id"],
        },
    },
    {
        "name": "summarise_content",
        "description": (
            "Produces a concise summary of the key arguments and findings in a document. "
            "Do NOT use for web pages — use only for documents passed by the coordinator."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "document_id": {"type": "string", "description": "ID or URL of the document"},
                "max_words":   {"type": "integer", "description": "Target summary length in words"},
            },
            "required": ["document_id"],
        },
    },
    {
        "name": "verify_claim",
        "description": (
            "Checks whether a specific claim is supported, contradicted, or not mentioned "
            "in a source document. Use for deep document-level fact checking."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "claim":       {"type": "string", "description": "The claim to verify"},
                "document_id": {"type": "string", "description": "Document to check against"},
            },
            "required": ["claim", "document_id"],
        },
    },
]

SYNTHESIS_TOOLS: list[anthropic.types.ToolParam] = [
    {
        "name": "compile_report",
        "description": (
            "Assembles research findings from multiple sources into a structured report. "
            "Use as the final step after all sources have been analysed."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "title":    {"type": "string", "description": "Report title"},
                "sections": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Section headings to include",
                },
                "source_ids": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "IDs of sources to include",
                },
            },
            "required": ["title", "source_ids"],
        },
    },
    {
        "name": "format_citation",
        "description": (
            "Formats a source reference in a specified citation style (APA, MLA, Chicago). "
            "Use when adding references to a compiled report."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "source_id": {"type": "string", "description": "ID of the source to cite"},
                "style":     {"type": "string", "enum": ["APA", "MLA", "Chicago"], "description": "Citation style"},
            },
            "required": ["source_id", "style"],
        },
    },
    {
        "name": "assess_coverage",
        "description": (
            "Evaluates whether all research questions have been addressed by the collected sources. "
            "Use before compile_report to identify gaps."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "research_questions": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of research questions to check coverage for",
                },
                "source_ids": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "IDs of collected sources",
                },
            },
            "required": ["research_questions", "source_ids"],
        },
    },
]

# Agent registry — maps role name to tools and description
AGENT_TOOLSETS: dict[str, dict] = {
    "web_search": {
        "role":        "Finds and retrieves web content",
        "tools":       WEB_SEARCH_TOOLS,
    },
    "document_analysis": {
        "role":        "Analyses document structure and content",
        "tools":       DOCUMENT_ANALYSIS_TOOLS,
    },
    "synthesis": {
        "role":        "Compiles findings into reports",
        "tools":       SYNTHESIS_TOOLS,
    },
}


# ----- Step-2: Scoped verify_fact added to synthesis agent -----
# Handles simple single-source lookups during report compilation.
# Complex multi-source verifications → escalate to coordinator.

SCOPED_VERIFY_FACT: anthropic.types.ToolParam = {
    "name": "verify_fact",
    "description": (
        "Verifies a simple factual claim against a single source document. "
        "Use for quick checks during report compilation (e.g. confirming a date, name, or figure). "
        "Only handles single-source simple lookups — do NOT use for claims requiring "
        "cross-referencing multiple sources or deep analysis. "
        "For complex multi-source verifications, escalate to the coordinator."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "claim":     {"type": "string", "description": "The factual claim to verify"},
            "source_id": {"type": "string", "description": "ID of the single source document to check against"},
        },
        "required": ["claim", "source_id"],
    },
}

SYNTHESIS_TOOLS.append(SCOPED_VERIFY_FACT)
AGENT_TOOLSETS["synthesis"]["tools"] = SYNTHESIS_TOOLS


if __name__ == "__main__":
    print("=== Step-1 & 2: Agent Tool Scoping ===\n")
    for agent_name, config in AGENT_TOOLSETS.items():
        tools = config["tools"]
        names = [t["name"] for t in tools]
        print(f"[{agent_name}] — {config['role']}")
        for name in names:
            scope = " (scoped cross-role)" if name == "verify_fact" else ""
            print(f"  • {name}{scope}")
        print(f"  Total: {len(tools)} tools\n")

    # verify no unintended cross-role duplicates
    # (verify_fact is intentionally scoped to synthesis only)
    all_names: list[str] = [
        t["name"]
        for config in AGENT_TOOLSETS.values()
        for t in config["tools"]
        if t["name"] != "verify_fact"  # scoped tool is exempt
    ]
    duplicates = {n for n in all_names if all_names.count(n) > 1}
    if duplicates:
        print(f"⚠️  Unexpected cross-role duplicates: {duplicates}")
    else:
        print("✅ No unintended cross-role tool duplicates — scoping is clean.")
