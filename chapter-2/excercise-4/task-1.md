নিচের exercise-টার মূল বিষয় হলো: **MCP Servers কোথায় configure করবে, কীভাবে credentials secure রাখবে, personal vs team configuration কীভাবে আলাদা করবে, resources expose করে unnecessary tool calls কমাবে, আর MCP tools-এর description কীভাবে strong করবে।**

---

## 1. প্রথমে বুঝি: `MCP Server` configure করার দরকার কী?

তোমার Claude/agent যদি বাইরের কোনো system-এর সাথে কাজ করতে চায়—যেমন GitHub, Atlassian, database, internal documentation—তাহলে MCP Server সেই external capability expose করে।

এই exercise-এ মূলত তুমি শিখবে:

* কোন MCP server team-এর জন্য shared হবে
* কোনটা শুধু তোমার personal testing-এর জন্য থাকবে
* credentials কীভাবে `.mcp.json`-এ hardcode না করে environment variable দিয়ে দেবে
* MCP resources দিয়ে agent-কে available data সম্পর্কে আগেই জানাবে
* আর MCP tool descriptions এমনভাবে লিখবে যাতে agent built-in tools-এর বদলে তোমার MCP tool ব্যবহার করতে আগ্রহী হয়

---

# 2. Project-level MCP Server: `.mcp.json`

ধরো, তোমার পুরো team GitHub ব্যবহার করে। তোমরা চাও Claude project-এর code নিয়ে কাজ করার সময় GitHub-এর সাথে interact করতে পারুক।

এক্ষেত্রে MCP configuration রাখা উচিত:

```text
project-root/
├── .mcp.json
├── src/
├── package.json
└── ...
```

অর্থাৎ project root-এ `.mcp.json`।

এর basic structure এমন হতে পারে:

```json
{
  "mcpServers": {
    "github": {
      "type": "http",
      "url": "..."
    }
  }
}
```

এখানে top-level key অবশ্যই:

```text
mcpServers
```

হতে হবে।

### কেন `.mcp.json`?

কারণ এটা project-level configuration।

মানে:

* তুমি repository-তে commit করতে পারবে
* অন্য developer repository clone করলে একই configuration পাবে
* পুরো team একই MCP server ব্যবহার করতে পারবে

ধরো তোমার team-এর সবাইকে GitHub integration দরকার। তাহলে প্রত্যেকে আলাদা করে manually setup করার চেয়ে `.mcp.json` repository-তে রাখাই better।

Exercise-এর একটা important exam point হলো:

> **Team-wide MCP servers → `.mcp.json`**

আর personal server হলে অন্য জায়গা।

---

# 3. Remote MCP Server আর Local MCP Server-এর পার্থক্য

সব MCP server একইভাবে configure হয় না।

## Remote server

Official integration server যেমন GitHub বা Atlassian এখন অনেক ক্ষেত্রে remote HTTP endpoint হিসেবে থাকে।

সেক্ষেত্রে configuration-এ থাকবে:

```json
{
  "type": "http",
  "url": "https://..."
}
```

এখানে একটা important ব্যাপার:

```text
url আছে কিন্তু type নেই
```

এটা configuration error হতে পারে।

মানে remote HTTP server হলে শুধু `url` দিলেই হবে না, exercise অনুযায়ী:

```json
"type": "http"
```

ও declare করতে হবে।

---

## Local server

যদি তোমার MCP server locally কোনো command চালিয়ে start হয়, তাহলে structure হবে command-based।

যেমন conceptually:

```json
{
  "command": "node",
  "args": ["server.js"]
}
```

অর্থাৎ:

* **Remote MCP server** → `type` + `url`
* **Local MCP server** → `command` + `args`

Exercise-এর Nudge-এ বলা হয়েছে, valid configuration structure maintain করা খুব important।

---

# 4. সবচেয়ে important অংশ: Credentials hardcode করবে না

ধরো GitHub API access করার জন্য তোমার একটা token লাগবে।

সবচেয়ে dangerous কাজ হবে:

```json
{
  "headers": {
    "Authorization": "Bearer ghp_actual_secret_token_here"
  }
}
```

কারণ `.mcp.json` যদি Git-এ commit হয়ে যায়, তাহলে তোমার secret repository history-তে চলে যেতে পারে।

একবার Git history-তে secret চলে গেলে পরে file থেকে delete করলেও problem পুরোপুরি শেষ হয় না।

তাই use করবে:

```text
${GITHUB_TOKEN}
```

যেমন:

```json
{
  "headers": {
    "Authorization": "Bearer ${GITHUB_TOKEN}"
  }
}
```

এখানে `.mcp.json`-এ actual token নেই।

Runtime-এ environment variable expand হবে।

অর্থাৎ:

```text
${GITHUB_TOKEN}
```

দেখে system environment থেকে actual value নিয়ে নেবে।

### প্রত্যেক developer নিজের token locally রাখবে

উদাহরণ:

```bash
export GITHUB_TOKEN=ghp_xxx
```

এটা shell profile-এ রাখতে পারো, যেমন:

```text
~/.zshrc
```

অথবা local `.env` file-এ রাখতে পারো।

কিন্তু `.env` হলে অবশ্যই নিশ্চিত করতে হবে যে এটা:

```text
.gitignore
```

এর মধ্যে আছে।

---

## এখানে exam mindset কী?

দেখো:

❌ Wrong:

```text
GitHub token সরাসরি .mcp.json-এ
```

❌ Wrong:

```text
Team repository-তে actual secret commit করা
```

✅ Correct:

```text
${GITHUB_TOKEN}
```

এবং প্রত্যেক developer নিজের machine-এ নিজের credential configure করবে।

Exercise-এ specifically বলা হয়েছে:

> `git diff` check করে confirm করো কোনো secret staged for commit হয়নি।

এটা practical habit হিসেবেও useful।

---

# 5. Project-level vs User-level MCP configuration

এটা exercise-এর সবচেয়ে গুরুত্বপূর্ণ conceptual অংশগুলোর একটা।

দুইটা scope আছে।

## Project-level

Location:

```text
.mcp.json
```

Scope:

```text
Current project / team
```

Use করবে যখন:

* পুরো team একই MCP server ব্যবহার করবে
* integration project-এর অংশ
* version control-এ রাখা দরকার

Example:

```text
GitHub
Atlassian
Shared internal database integration
Company documentation server
```

---

## User-level

Location:

```text
~/.claude.json
```

এটা তোমার home directory-তে থাকে।

```text
~
└── .claude.json
```

এটা project repository-এর অংশ না।

Use করবে:

* personal MCP server
* experimental integration
* কোনো নতুন server test করার জন্য
* এমন tool যেটা শুধু তুমি ব্যবহার করো

ধরো তুমি একটা experimental MCP server নিয়ে test করছো।

এখনও তুমি নিশ্চিত না এটা পুরো team ব্যবহার করবে কিনা।

তাহলে:

```text
~/.claude.json
```

এ রাখবে।

সব ঠিকঠাক কাজ করলে পরে team-wide করার জন্য `.mcp.json`-এ move করতে পারো।

---

## সহজভাবে মনে রাখো

| Configuration | Location         | কার জন্য?                 | Git-এ যাবে?   |
| ------------- | ---------------- | ------------------------- | ------------- |
| Project-level | `.mcp.json`      | পুরো team                 | সাধারণত হ্যাঁ |
| User-level    | `~/.claude.json` | শুধু তোমার personal setup | না            |

সবচেয়ে সহজ mnemonic:

```text
Team = .mcp.json
Me = ~/.claude.json
```

---

# 6. দুই জায়গার MCP servers একসাথে available হতে পারে

ধরো:

`.mcp.json`-এ আছে:

```text
github
atlassian
```

আর `~/.claude.json`-এ আছে:

```text
my-experimental-server
```

Connection time-এ system দুই জায়গার configuration discover করতে পারে।

তাহলে agent-এর কাছে একই সাথে available হতে পারে:

```text
github tools
atlassian tools
my-experimental-server tools
```

এটাই scoping hierarchy বোঝার একটা important অংশ।

---

# 7. MCP Resources কেন দরকার?

এখানে একটা interesting concept আছে: **Tools** আর **Resources** এক জিনিস না।

ধরো agent database নিয়ে কাজ করছে।

Database-এ আছে:

```text
users
orders
payments
products
```

Agent জানে না database-এ কী কী table আছে।

তাহলে agent হয়তো করবে:

```text
list_tables
```

তারপর:

```text
describe_table(users)
describe_table(orders)
describe_table(payments)
describe_table(products)
```

মানে শুধু database structure বোঝার জন্যই অনেকগুলো tool call।

এটাকে বলা যায় unnecessary exploratory tool calls।

---

## এর alternative: MCP Resource

তুমি আগে থেকেই একটা resource expose করতে পারো:

```text
db://schema/main
```

এই resource-এ থাকতে পারে:

```text
users
  - id: UUID
  - name: TEXT
  - email: TEXT

orders
  - id: UUID
  - user_id: UUID
  - total: DECIMAL
```

এখন agent শুরুতেই বুঝতে পারবে:

* কী data available
* কোন table আছে
* কোন column আছে
* কোন data type আছে

তারপর agent যখন actual কাজ করতে চাইবে, তখন tool use করবে।

---

# 8. Resources আর Tools-এর difference

এটা খুব important।

ভাবো:

### Resource বলে:

> "আমার কাছে কী কী information available আছে?"

আর Tool বলে:

> "এই information ব্যবহার করে আমি কী action নিতে পারি?"

Example:

### Resource

```text
db://schema/main
```

এটা database structure দেখায়।

এটা basically একটা **read-only data catalogue**।

---

### Tool

```text
query_database
```

এটা actual SQL query execute করতে পারে।

তাহলে:

```text
Resource → visibility / discovery
Tool → action
```

আরেকভাবে:

```text
Resources = What's available?
Tools = What can I do?
```

এই distinction exercise-এর core concept।

---

# 9. Resource definition-এ কী কী থাকবে?

Exercise অনুযায়ী resource-এ থাকতে পারে:

* URI
* name
* description
* mimeType

Example concept:

```text
URI:
db://schema/main

Name:
Main Database Schema

Description:
Contains all database tables and their column definitions.

mimeType:
application/json
```

MCP SDK-তে resource define করার জন্য exercise অনুযায়ী use করা যেতে পারে:

```text
server.resource()
```

এর মধ্যে generally থাকবে:

* URI template
* name
* handler

Handler structured content return করবে।

মানে resource static file হওয়া বাধ্যতামূলক না। প্রয়োজন অনুযায়ী dynamically generate-ও হতে পারে।

---

# 10. কেন MCP Tool Description এত important?

এটাই exercise-এর সবচেয়ে interesting অংশগুলোর একটা।

ধরো তোমার একটা MCP tool আছে:

```text
search_codebase
```

কিন্তু description:

```text
Searches the codebase.
```

এটা খুব weak।

Agent ভাবতে পারে:

> "আমার তো built-in `Grep` আছে। এটা search করতে পারে। আমি Grep-ই use করি।"

কিন্তু তোমার MCP tool হয়তো actually অনেক better।

ধরো এটা:

* semantic search করে
* related files খুঁজে দেয়
* symbol relationship বোঝে
* ranking দেয়

কিন্তু description-এ তুমি এগুলো বলোনি।

Agent capability guess করে না সবসময়। Tool description অনেক বড় role play করে।

---

# 11. Built-in `Grep` কেন তোমার MCP tool-কে হারিয়ে দিতে পারে?

Built-in tools সাধারণত rich description নিয়ে আসে।

যেমন `Grep` সম্পর্কে agent জানে:

* এটা কী করে
* input কী
* output কী
* কখন use করতে হবে
* limitations কী

কিন্তু তোমার MCP tool-এর description যদি হয়:

```text
Search the codebase.
```

তাহলে agent-এর কাছে built-in `Grep` বেশি clear এবং reliable মনে হতে পারে।

যদিও তোমার MCP tool technically বেশি powerful।

তাই MCP tool-এর description strong করতে হবে।

---

# 12. একটা ভালো MCP Tool Description-এ 4টা জিনিস থাকবে

Exercise অনুযায়ী include করবে:

### 1. What the tool does

Tool আসলে কী করে?

Example:

```text
Performs semantic and structural searches across the repository.
```

---

### 2. What it returns

Output-এ কী পাওয়া যাবে?

Example:

```text
Returns matching files, code snippets, symbol names, relevance scores, and repository paths.
```

---

### 3. When to use it

কখন এই tool use করবে?

Example:

```text
Use this when searching for concepts, related implementations, or functionality whose exact text is unknown.
```

---

### 4. When to use the built-in alternative instead

সবসময় নিজের tool use করতে বললে description ভালো হয় না।

Clear boundary দিতে হবে।

Example:

```text
Use built-in Grep instead when you need a fast exact-text or regular-expression search.
```

এতে agent বুঝতে পারে কোন পরিস্থিতিতে কোনটা better।

---

# 13. Weak vs Enhanced Description

### Weak description

```text
Search the codebase.
```

Agent-এর কাছে প্রায় কোনো useful information নেই।

---

### Enhanced description

ধরো:

```text
Searches the codebase using semantic and structural analysis rather than only exact text matching. Returns ranked matches including file paths, relevant code snippets, symbol names, and relevance scores. Use this tool when you need to find functionality based on meaning or when the exact implementation name is unknown. For simple exact-text or regular-expression searches, use the built-in Grep tool instead.
```

এখানে clearly বলা হয়েছে:

* tool কী করে
* কীভাবে built-in search থেকে different
* output কী
* কখন use করবে
* কখন `Grep` use করবে

এটাই exercise-এর expected direction।

---

# 14. কেন description 3–5 sentences হওয়া উচিত?

কারণ:

```text
Too short → Agent বুঝবে না
Too vague → Built-in tool prefer করবে
Too long → Important signal হারিয়ে যেতে পারে
```

তাই roughly 3–5 meaningful sentence একটা ভালো balance।

প্রতিটা sentence ideally নতুন useful information দেবে।

শুধু marketing type:

```text
This is an amazing and powerful search tool.
```

এগুলো কোনো কাজের না।

বরং capability এবং boundary explain করতে হবে।

---

# পুরো Exercise-টার Practical Flow

Exercise শেষ করতে তুমি roughly এই flow follow করতে পারো:

### Step 1

Project root-এ create করো:

```text
.mcp.json
```

---

### Step 2

এর মধ্যে:

```text
mcpServers
```

define করো।

Official remote MCP server হলে:

```text
type: "http"
url: "..."
```

ব্যবহার করবে।

Local server হলে:

```text
command
args
```

ব্যবহার করবে।

---

### Step 3

Credential hardcode করবে না।

Use করবে:

```text
${GITHUB_TOKEN}
```

---

### Step 4

নিজের machine-এ token configure করবে:

```bash
export GITHUB_TOKEN=ghp_xxx
```

অথবা ignored `.env` file ব্যবহার করবে।

---

### Step 5

Personal বা experimental MCP server add করবে:

```text
~/.claude.json
```

এ।

---

### Step 6

একটা MCP resource expose করবে।

যেমন:

```text
db://schema/main
```

যেটা agent-কে database structure শুরুতেই দেখাবে।

---

### Step 7

MCP tools-এর description improve করবে।

প্রতিটা description-এ থাকবে:

```text
What it does
What it returns
When to use it
When NOT to use it / use built-in alternative
```

---

# শেষের Cheat Sheet

```text
Team-wide MCP Server
        ↓
.mcp.json

Personal / Experimental MCP Server
        ↓
~/.claude.json

Remote MCP Server
        ↓
"type": "http" + "url"

Local MCP Server
        ↓
"command" + "args"

Secret / Token
        ↓
${GITHUB_TOKEN}

Never
        ↓
Hardcode actual token in .mcp.json

Resource
        ↓
"What data is available?"

Tool
        ↓
"What action can I perform?"

Weak Tool Description
        ↓
Agent may prefer built-in tools

Enhanced Tool Description
        ↓
Explain:
1. What it does
2. What it returns
3. When to use
4. When built-in alternative is better
```

সব মিলিয়ে exercise-এর আসল lesson হলো: **MCP configure করা শুধু server connect করা না। Configuration-এর scope ঠিক রাখা, secrets safe রাখা, agent-কে resources দিয়ে context দেওয়া, এবং tool descriptions ভালোভাবে লেখা—এই চারটা জিনিসই production-quality MCP setup-এর গুরুত্বপূর্ণ অংশ।**
