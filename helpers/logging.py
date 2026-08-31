import json
import os
from datetime import datetime

from claude_agent_sdk import AssistantMessage, ToolUseBlock
from claude_agent_sdk.types import (
    HookEventMessage,
    ResultMessage,
    SystemMessage,
    TaskNotificationMessage,
    TaskProgressMessage,
    TaskStartedMessage,
    TextBlock,
    ToolResultBlock,
)


def log(msg: str) -> None:
    print(f"[pipeline] {msg}", flush=True)


def snippet(text: str, n: int = 80) -> str:
    text = text.replace("\n", " ").strip()
    return text[:n] + "…" if len(text) > n else text


def log_message(stage: str, message) -> None:
    """Rich per-message logger — before/after tool calls and LLM turns."""

    # ── Hook events (PreToolUse / PostToolUse / PostToolUseFailure / Stop …) ──
    if isinstance(message, HookEventMessage):
        event = message.hook_event_name
        data  = message.data

        if event == "PreToolUse":
            tool  = data.get("tool_name", "?")
            inp   = data.get("tool_input", {})
            brief = snippet(json.dumps(inp))
            log(f"[{stage}] ▶ before_tool_call  tool={tool}  input={brief}")

        elif event == "PostToolUse":
            tool   = data.get("tool_name", "?")
            output = data.get("tool_response", "")
            brief  = snippet(str(output))
            log(f"[{stage}] ◀ after_tool_call   tool={tool}  output={brief}")

        elif event == "PostToolUseFailure":
            tool  = data.get("tool_name", "?")
            error = data.get("error", "?")
            log(f"[{stage}] ✗ tool_call_failed  tool={tool}  error={snippet(error)}")

        elif event == "Stop":
            log(f"[{stage}] ■ stop hook fired")

        else:
            log(f"[{stage}] hook:{event}")
        return

    # ── Task lifecycle (sub-agent started / progress / finished) ──
    if isinstance(message, TaskStartedMessage):
        log(f"[{stage}] ⚙  task_started   id={message.task_id[:8]}  desc={snippet(message.description)}")
        return

    if isinstance(message, TaskProgressMessage):
        tool = message.last_tool_name or "—"
        log(f"[{stage}] ⚙  task_progress  id={message.task_id[:8]}  last_tool={tool}  tokens={message.usage.get('total_tokens', '?')}")
        return

    if isinstance(message, TaskNotificationMessage):
        log(f"[{stage}] ⚙  task_done      id={message.task_id[:8]}  status={message.status}  summary={snippet(message.summary)}")
        return

    # ── Generic SystemMessage (everything else) ──
    if isinstance(message, SystemMessage):
        log(f"[{stage}] sys:{message.subtype}")
        return

    # ── AssistantMessage — LLM response ──
    if isinstance(message, AssistantMessage):
        texts = [b.text for b in message.content if isinstance(b, TextBlock)]
        tools = [b for b in message.content if isinstance(b, ToolUseBlock)]
        tool_results = [b for b in message.content if isinstance(b, ToolResultBlock)]

        if texts:
            log(f"[{stage}] ◉ after_llm_call  text={snippet(' '.join(texts))}")
        for t in tools:
            log(f"[{stage}] ▶ before_tool_call  tool={t.name}  input={snippet(json.dumps(t.input))}")
        for r in tool_results:
            content = r.content if isinstance(r.content, str) else json.dumps(r.content)
            log(f"[{stage}] ◀ after_tool_call   tool_use_id={r.tool_use_id[:8]}  output={snippet(content)}")
        return

    # ── ResultMessage ──
    if isinstance(message, ResultMessage):
        log(f"[{stage}] ✔ result  stop_reason={message.stop_reason}  is_error={message.is_error}  turns={message.num_turns}")


def write_result_log(query: str, findings: list, report: list, log_dir: str = "logs") -> str:
    """Write the full pipeline result to a timestamped .log file with human-readable entries."""
    os.makedirs(log_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = os.path.join(log_dir, f"pipeline_{timestamp}.log")

    sep = "-" * 80

    with open(path, "w", encoding="utf-8") as f:
        f.write(f"PIPELINE RUN — {datetime.now().isoformat()}\n")
        f.write(f"QUERY: {query}\n")
        f.write(f"{sep}\n\n")

        f.write(f"FINDINGS ({len(findings)} total)\n")
        f.write(f"{sep}\n")
        for i, finding in enumerate(findings, 1):
            f.write(f"[{i}] claim        : {finding.get('claim', '')}\n")
            f.write(f"     source_url   : {finding.get('source_url', '')}\n")
            f.write(f"     document_name: {finding.get('document_name', '')}\n")
            f.write(f"     page_number  : {finding.get('page_number', '')}\n")
            f.write(f"     confidence   : {finding.get('confidence', '')}\n")
            f.write(f"     retrieved_by : {finding.get('retrieved_by', '')}\n")
            f.write("\n")

        f.write(f"\nREPORT ({len(report)} items)\n")
        f.write(f"{sep}\n")
        for i, item in enumerate(report, 1):
            f.write(f"[{i}] statement: {item.get('statement', '')}\n")
            f.write(f"     citation : {item.get('citation', '')}\n")
            f.write("\n")

    log(f"result written to {path}")
    return path
