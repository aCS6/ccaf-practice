# Per-Step Flow — chapter-2/excercise-3

---

## Step-1: Three Agent Roles with Scoped Tools

```
Define tool lists
    │
    ├── WEB_SEARCH_TOOLS      → search_web, fetch_page, extract_links, save_snippet
    ├── DOCUMENT_ANALYSIS_TOOLS → extract_metadata, extract_data_points,
    │                              summarise_content, verify_claim
    └── SYNTHESIS_TOOLS       → compile_report, format_citation, assess_coverage
            │
            ▼
    AGENT_TOOLSETS registry
    { web_search, document_analysis, synthesis }
            │
            ▼
    Verify no tool appears in more than one agent
    → ✅ clean scoping
```

**Why:** Tool overload degrades selection reliability. Each agent gets 4-5 tools
scoped to its specific role only.

---

## Step-2: Scoped Cross-Role Tool (verify_fact → synthesis)

```
SCOPED_VERIFY_FACT defined
    │
    ├── description explicitly limits scope:
    │     "single-source simple lookups only"
    │     "escalate to coordinator for multi-source"
    │
    └── appended to SYNTHESIS_TOOLS only
            │
            ▼
    synthesis agent now has 4 tools
    verify_fact NOT in web_search or document_analysis
```

**Why:** Routing every fact check through the coordinator adds 2-3 round trips.
Scoped tool handles the 85% simple case locally.

---

## Step-3: Forced tool_choice on Document Analysis Agent

```
user_query + document_id
        │
        ▼
  Turn-1: tool_choice = { type: "tool", name: "extract_metadata" }
        │
        ▼
  Claude API call  ──►  Claude MUST call extract_metadata (no choice)
        │
        ▼
  mock_tool_result("extract_metadata") → fake metadata JSON
        │
        ▼
  is_first_turn = False
        │
        ▼
  Turn-2+: tool_choice = { type: "auto" }
        │
        ▼
  Claude API call  ──►  Claude freely picks next tool
        │                 (extract_data_points / summarise_content / verify_claim)
        ▼
  mock_tool_result(chosen_tool) → fake result
        │
        ▼
  loop until stop_reason == "end_turn"
```

**Why:** Forced selection enforces mandatory workflow ordering. `extract_metadata`
must always run first — programmatic enforcement, not prompt guidance.

---

## Step-4: Constrained load_document (Least Privilege)

```
load_document_handler(url)
        │
        ▼
  validate_document_url(url)
        │
        ├── check extension ∈ { .pdf, .docx, .md, .txt, .html }
        │       └── ❌ fail → return structured error
        │
        ├── check hostname ∈ trusted_domains
        │       └── ❌ fail → return structured error
        │
        └── ✅ both pass → return mock document content

fetch_page (generic, fetches anything)
        │
        ▼  replaced by
load_document (constrained, validates URL first)
        │
        ▼
WEB_SEARCH_TOOLS updated in-place
```

**Why:** Principle of least privilege. A generic fetch_url can access any URL.
`load_document` enforces boundaries — agent cannot fetch arbitrary resources.

---

## Step-5: End-to-End Multi-Agent Test

```
QUERY: "Research the latest MCP specification changes..."
        │
        ├── web_search agent
        │     tools: search_web, load_document, extract_links, save_snippet
        │     tool_choice: auto  (model decides when to stop — prevents runaway loops)
        │     max_iterations: 5  (safety cap)
        │     Claude API → tool calls → mock results → loop → end_turn
        │     log: [{ agent: "web_search", tool: "search_web" }, ...]
        │
        ├── document_analysis agent
        │     → run_document_analysis_agent() (Step-3 flow with forced first turn)
        │     log: [{ agent: "document_analysis", tool: "extract_metadata" }, ...]
        │
        └── synthesis agent
              tools: compile_report, format_citation, assess_coverage, verify_fact
              tool_choice: auto
              max_iterations: 5
              Claude API → tool calls → mock results → loop → end_turn
              log: [{ agent: "synthesis", tool: "compile_report" }, ...]
                    │
                    ▼
        full_log = all three logs combined
                    │
                    ▼
        Cross-role violation check:
            for each entry in full_log:
                tool ∈ allowed_tools[agent] ?
                    ✅ VALID
                    ❌ CROSS-ROLE VIOLATION
                    │
                    ▼
        Print summary: total calls, violations count
```

**Why:** Verifies that tool scoping works in practice. Each agent can only call
its own tools — cross-role misuse is caught programmatically, not by trust.

**Note:** `tool_choice: "any"` was intentionally avoided here — it forces the model
to always call a tool, causing infinite loops when mock results give no reason to stop.
`tool_choice: "auto"` lets the model decide when it has enough information to respond.

**Note on max_iterations:** `max_iterations = 5` is a safety cap only — it prevents
infinite loops but does NOT guarantee correctness. The primary stopping mechanism is
`tool_choice: "auto"` + `stop_reason == "end_turn"`. If the cap is what stops the loop,
it means the model never got a satisfying result from the mock responses — the root cause
is that mock results don't give the model enough signal to know when it's done.
