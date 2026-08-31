from claude_agent_sdk import ClaudeAgentOptions, query

options = ClaudeAgentOptions(
    allowed_tools=["Task"],  # hard requirement to spawn subagents
    agents={}  # subagents added in next step
)