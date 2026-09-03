import os
from urllib.parse import urlparse

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


# ----- Step-3: Forced tool_choice on document analysis agent -----
# First turn: force extract_metadata as mandatory first step.
# Subsequent turns: auto so model picks appropriate analysis tool.

def mock_tool_result(name: str, tool_input: dict) -> str:
    """Return mock results for document analysis tools."""
    if name == "extract_metadata":
        return '{"title": "MCP Specification v2.1", "author": "MCP Working Group", "date": "2024-03-15", "type": "technical_spec"}'
    if name == "extract_data_points":
        return '{"versions": ["2.0", "2.1"], "release_date": "2024-03-15", "breaking_changes": 3}'
    if name == "summarise_content":
        return '{"summary": "MCP v2.1 introduces tool scoping, structured errors, and multi-agent coordination primitives."}'
    if name == "verify_claim":
        return '{"supported": true, "evidence": "Section 4.2 confirms tool scoping was added in v2.1"}'
    return '{"result": "ok"}'


def run_document_analysis_agent(document_id: str, user_query: str) -> list[dict]:
    """
    Document analysis agent loop with forced extract_metadata on first turn.
    Returns list of tool calls made during the session.
    """
    print(f"\n  Analysing document: {document_id}")
    tool_call_log: list[dict] = []

    messages: list[anthropic.types.MessageParam] = [
        {"role": "user", "content": f"{user_query}\n\nDocument ID: {document_id}"}
    ]

    is_first_turn = True

    while True:
        # First turn: force extract_metadata — mandatory workflow step
        # Subsequent turns: auto — model picks the right analysis tool
        tool_choice: anthropic.types.ToolChoiceParam = (
            {"type": "tool", "name": "extract_metadata"}
            if is_first_turn
            else {"type": "auto"}
        )

        response = client.messages.create(
            model=MODEL,
            max_tokens=1024,
            tools=DOCUMENT_ANALYSIS_TOOLS,
            tool_choice=tool_choice,
            messages=messages,
        )

        if response.stop_reason == "tool_use":
            is_first_turn = False
            tool_results: list[anthropic.types.ToolResultBlockParam] = []
            for block in response.content:
                if block.type == "tool_use":
                    result = mock_tool_result(block.name, block.input)
                    forced = " [FORCED]" if block.name == "extract_metadata" and len(tool_call_log) == 0 else ""
                    print(f"    [TOOL]{forced} {block.name}({block.input})")
                    tool_call_log.append({"agent": "document_analysis", "tool": block.name})
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": result,
                    })

            messages.append({"role": "assistant", "content": response.content})
            messages.append({"role": "user", "content": tool_results})  # type: ignore[arg-type]

        elif response.stop_reason == "end_turn":
            final = next((b.text for b in response.content if b.type == "text"), "")
            print(f"    [DONE] {final[:120]}")
            break
        else:
            print(f"    [WARN] stop_reason={response.stop_reason}")
            break

    return tool_call_log


# ----- Step-4: Constrained load_document (replaces generic fetch_page) -----
# Applies least privilege — only accepts validated document URLs.
# Rejects arbitrary URLs that don't match document patterns or trusted domains.

VALID_EXTENSIONS = {".pdf", ".docx", ".md", ".txt", ".html"}
TRUSTED_DOMAINS  = {"docs.internal.com", "wiki.company.com", "specs.example.org"}

def validate_document_url(url: str) -> tuple[bool, str]:
    """
    Returns (is_valid, error_message).
    Valid = URL has a document extension AND comes from a trusted domain.
    """
    try:
        parsed = urlparse(url)
        ext    = os.path.splitext(parsed.path)[1].lower()
        domain = parsed.hostname or ""

        if ext not in VALID_EXTENSIONS:
            return False, (
                f"Rejected: '{url}' has unsupported extension '{ext}'. "
                f"Allowed: {', '.join(sorted(VALID_EXTENSIONS))}."
            )
        if domain not in TRUSTED_DOMAINS:
            return False, (
                f"Rejected: '{domain}' is not a trusted domain. "
                f"Allowed: {', '.join(sorted(TRUSTED_DOMAINS))}."
            )
        return True, ""
    except Exception as e:
        return False, f"Invalid URL: {e}"


def load_document_handler(url: str) -> dict:
    """Mock handler for load_document — validates URL before fetching."""
    is_valid, error = validate_document_url(url)
    if not is_valid:
        return {"isError": True, "message": error}
    return {
        "isError":  False,
        "url":      url,
        "content":  f"[Mock document content from {url}]",
        "size_kb":  42,
    }


LOAD_DOCUMENT_TOOL: anthropic.types.ToolParam = {
    "name": "load_document",
    "description": (
        "Loads a document from a validated URL. "
        "Only accepts URLs ending in .pdf, .docx, .md, .txt, or .html "
        "from trusted domains (docs.internal.com, wiki.company.com, specs.example.org). "
        "Use instead of fetch_page for document retrieval. "
        "Rejects arbitrary or untrusted URLs with a clear error."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "url": {
                "type": "string",
                "description": "Document URL — must be a document file from a trusted domain",
            },
        },
        "required": ["url"],
    },
}

# Replace fetch_page with load_document in web_search agent
WEB_SEARCH_TOOLS[:] = [
    LOAD_DOCUMENT_TOOL if t["name"] == "fetch_page" else t
    for t in WEB_SEARCH_TOOLS
]
AGENT_TOOLSETS["web_search"]["tools"] = WEB_SEARCH_TOOLS


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

    all_names: list[str] = [
        t["name"]
        for config in AGENT_TOOLSETS.values()
        for t in config["tools"]
        if t["name"] != "verify_fact"
    ]
    duplicates = {n for n in all_names if all_names.count(n) > 1}
    if duplicates:
        print(f"⚠️  Unexpected cross-role duplicates: {duplicates}")
    else:
        print("✅ No unintended cross-role tool duplicates — scoping is clean.")

    print("\n=== Step-3: Forced extract_metadata on Document Analysis Agent ===")
    log = run_document_analysis_agent(
        document_id="doc-mcp-spec-v2",
        user_query="Analyse this document and extract key data points and a summary.",
    )
    first_tool = log[0]["tool"] if log else "none"
    print(f"\n  First tool called: {first_tool}")
    print(f"  {'✅' if first_tool == 'extract_metadata' else '❌'} extract_metadata was {'enforced' if first_tool == 'extract_metadata' else 'NOT enforced'} as first step.")

    print("\n=== Step-4: Constrained load_document URL Validation ===\n")
    test_urls = [
        "https://docs.internal.com/specs/mcp-v2.pdf",       # ✅ valid
        "https://wiki.company.com/guide.md",                 # ✅ valid
        "https://evil.com/malware.pdf",                      # ❌ untrusted domain
        "https://docs.internal.com/page",                    # ❌ no extension
        "https://docs.internal.com/data.csv",                # ❌ unsupported extension
    ]
    for url in test_urls:
        result = load_document_handler(url)
        status = "✅" if not result["isError"] else "❌"
        msg = result.get("content", result.get("message", ""))
        print(f"  {status} {url}\n     → {msg}\n")
