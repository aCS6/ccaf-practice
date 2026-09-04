# Step-3: Personal MCP Server — ~/.claude.json

## Concept

`~/.claude.json` is the **user-level** MCP configuration file.
It lives in your home directory and is NOT version-controlled.

| File | Scope | Who sees it |
|---|---|---|
| `.mcp.json` (project root) | Team | Everyone who clones the repo |
| `~/.claude.json` | Personal | Only you, on this machine |

## When to use ~/.claude.json

- Testing an experimental server before proposing it to the team
- Personal integrations (your own notes server, local DB, etc.)
- Servers with credentials that are yours alone

## What the entry looks like

Add an `mcpServers` key to `~/.claude.json`:

```json
{
  "mcpServers": {
    "experimental-search": {
      "command": "node",
      "args": ["/path/to/my/experimental-search-server.js"],
      "env": {
        "API_KEY": "${EXPERIMENTAL_API_KEY}"
      }
    }
  }
}
```

Note: local servers use `command` + `args` (not `type: "http"`).
The `env` block injects environment variables into the server process.

## Key rule

Never commit `~/.claude.json` to any repository.
It is personal — treat it like `~/.ssh/config`.
