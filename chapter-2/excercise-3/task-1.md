এই exercise-এর মূল কথা হলো **multi-agent system-এ কোন agent কোন tools ব্যবহার করবে সেটা খুব carefully design করা**। এখানে লক্ষ্য শুধু tools assign করা না—বরং এমনভাবে scope করা যাতে agent ভুল tool ব্যবহার না করে, unnecessary coordinator round-trip না হয়, আর workflow predictable থাকে।

সহজভাবে বললে:

> **একটা agent-কে সব tools দিয়ে দিও না। যে agent যে কাজের জন্য responsible, তাকে সেই কাজের দরকারি tools-ই দাও।**

---

# Configure Tool Distribution Across a Multi-Agent System

**Difficulty:** 45 minutes

এই exercise-এ তুমি তিনটা agent বানাবে:

1. **Web Search Agent** → web থেকে information collect করবে
2. **Document Analysis Agent** → documents analyse করবে
3. **Synthesis Agent** → collected information থেকে final report তৈরি করবে

প্রতিটা agent-এর জন্য সাধারণত **4–5টা scoped tools** থাকবে।

---

# 1. কেন Tool Distribution গুরুত্বপূর্ণ?

ধরো তোমার কাছে মোট 18টা tools আছে।

তুমি যদি সব 18টা tools এক agent-কে দিয়ে দাও:

```text
Agent
 ├── search_web
 ├── fetch_page
 ├── extract_links
 ├── save_snippet
 ├── extract_metadata
 ├── extract_data_points
 ├── summarise_content
 ├── verify_claim
 ├── compile_report
 ├── format_citation
 ├── assess_coverage
 ├── ...
```

তাহলে LLM-এর জন্য কোন tool কখন ব্যবহার করতে হবে সেটা determine করা কঠিন হয়ে যায়।

এতে **tool selection reliability** কমে যায় এবং **misrouting** হতে পারে।

Exercise-এর গুরুত্বপূর্ণ principle:

> **প্রতিটা agent-এর কাছে 4–5টার মতো role-specific tools রাখা ভালো।**

একটা agent-এর কাছে 18টা tools থাকা একটা **known anti-pattern**।

---

# 2. তিনটা Agent-এর জন্য Tools ভাগ করা

তোমাকে তিনটা role define করতে হবে।

### Web Search Agent

এই agent-এর কাজ হলো web থেকে information collect করা।

তাকে দেওয়া হবে:

```text
search_web
fetch_page
extract_links
save_snippet
```

অর্থাৎ মোট **4 tools**।

এখানে প্রতিটা tool-এর purpose পরিষ্কার:

* `search_web` → web search করা
* `fetch_page` → কোনো page-এর content আনা
* `extract_links` → page থেকে relevant links বের করা
* `save_snippet` → useful information/snippet save করা

---

### Document Analysis Agent

এই agent documents analyse করবে।

Tools:

```text
extract_metadata
extract_data_points
summarise_content
verify_claim
```

এখানেও **4 tools**।

যেমন:

* `extract_metadata` → document-এর metadata বের করা
* `extract_data_points` → গুরুত্বপূর্ণ data বের করা
* `summarise_content` → content summarize করা
* `verify_claim` → document-এর claim verify করা

---

### Synthesis Agent

এই agent-এর কাজ হলো অন্য agents-এর collected information নিয়ে final output তৈরি করা।

Tools:

```text
compile_report
format_citation
assess_coverage
```

এখানে **3 tools** আছে।

Exercise-এর overall guideline 4–5 tools হলেও guidance-এর initial example-এ Synthesis-এর 3টা tools দেওয়া হয়েছে। পরে `verify_fact` যোগ করলে এটা 4টা হবে।

---

# 3. Tool Overlap কেন Avoid করতে হবে?

প্রথম configuration-এ চেষ্টা করতে হবে যেন কোনো tool একাধিক agent-এর মধ্যে না থাকে।

অর্থাৎ:

```text
Web Search
    ├── search_web
    ├── fetch_page
    ├── extract_links
    └── save_snippet

Document Analysis
    ├── extract_metadata
    ├── extract_data_points
    ├── summarise_content
    └── verify_claim

Synthesis
    ├── compile_report
    ├── format_citation
    └── assess_coverage
```

এখানে প্রত্যেকটা tool-এর একটা নির্দিষ্ট owner আছে।

নিজেকে প্রত্যেক tool-এর জন্য প্রশ্ন করতে হবে:

> **"এই tool কি web search, document analysis, নাকি synthesis-এর কাজ?"**

যদি মনে হয় একটা tool দুইটা role-এই ব্যবহার করা যায়, তাহলে সম্ভবত tool-টা **split বা scope** করা দরকার।

---

# 4. Scoped Cross-Role Tool

এখন exercise-এর একটা important concept আসে।

ধরো **Synthesis Agent** report বানাচ্ছে।

তার একটা claim verify করতে হবে।

সাধারণ approach হতে পারে:

```text
Synthesis Agent
      ↓
Coordinator
      ↓
Web Search Agent
      ↓
search_web
      ↓
Coordinator
      ↓
Synthesis Agent
```

এখানে অনেকগুলো round trip হচ্ছে।

এটা unnecessary latency তৈরি করে।

Exercise বলছে, simple fact verification-এর ক্ষেত্রে এই pattern avoid করতে হবে।

---

# 5. `verify_fact` কেন Synthesis Agent-কে দেওয়া হচ্ছে?

Synthesis Agent-কে একটা **scoped `verify_fact` tool** দিতে হবে।

তাহলে:

```text
Synthesis Agent
      ↓
verify_fact
```

সরাসরি simple verification হয়ে যাবে।

এতে coordinator-এর কাছে ঘুরে যেতে হবে না।

Exercise অনুযায়ী, প্রায় **85% simple cases** এই scoped tool handle করতে পারে।

শুধু complex case হলে coordinator-এর কাছে escalate করবে।

---

# 6. `verify_fact`-এর Boundary খুব গুরুত্বপূর্ণ

এখানে তুমি একটা generic verification tool বানাবে না।

Tool-এর description-এই boundary specify করতে হবে।

যেমন conceptually:

```text
verify_fact

Input:
- claim
- source

Purpose:
Verify a simple claim against a single source.

Boundary:
Only handles simple single-source lookups.
Complex multi-source verification must be escalated to the coordinator.
```

অর্থাৎ:

### এটা করতে পারবে:

```text
Claim:
"The MCP specification version is X"

Source:
specific document/page
```

একটা source দেখে answer দিতে পারবে।

### কিন্তু এটা করবে না:

```text
Compare 5 different sources
Resolve conflicting claims
Perform complex cross-source research
```

সেক্ষেত্রে:

```text
Synthesis Agent
      ↓
Coordinator
      ↓
Complex verification workflow
```

এটাই **scoped cross-role tool pattern**।

---

# 7. `tool_choice` — তিনটা Mode

Exercise-এর আরেকটা বড় concept হলো:

```text
tool_choice
```

এখানে তিনটা important mode বুঝতে হবে:

### `auto`

LLM নিজে decide করবে কোন tool ব্যবহার করবে।

```text
tool_choice:
{
    "type": "auto"
}
```

মানে:

> "তোমার প্রয়োজন অনুযায়ী tool choose করো।"

এটা normal workflow-এর জন্য useful।

---

### `any`

এটা guarantee করে যে model একটা tool call করবে।

মানে model শুধু text response দিয়ে বের হয়ে যেতে পারবে না।

Conceptually:

```text
tool_choice:
{
    "type": "any"
}
```

মানে:

> "কোনো একটা tool অবশ্যই call করো।"

কোন specific tool সেটা model choose করবে।

---

### Forced Selection

এখানে specific একটা tool force করে দেওয়া হয়।

যেমন:

```text
{
    "type": "tool",
    "name": "extract_metadata"
}
```

মানে:

> **এই turn-এ `extract_metadata` tool-টাই call করতে হবে।**

---

# 8. Document Analysis Agent-এ Forced Selection

এখানে একটা mandatory workflow আছে।

Document Analysis শুরু করার সময় প্রথমেই:

```text
extract_metadata
```

run করতে হবে।

কারণ metadata আগে না বের করলে পরবর্তী analysis unreliable হতে পারে।

তাই প্রথম API call-এ:

```text
tool_choice = {
    "type": "tool",
    "name": "extract_metadata"
}
```

দিতে হবে।

Flow হবে:

```text
User Request
     ↓
Document Analysis Agent
     ↓
FORCED: extract_metadata
     ↓
Metadata received
     ↓
tool_choice = auto
     ↓
extract_data_points / summarise_content / verify_claim
```

---

# 9. Forced Selection শুধু First Turn-এর জন্য

এখানে একটা subtle কিন্তু খুব important point আছে।

তুমি পুরো workflow-তে `extract_metadata` force করবে না।

শুধু **first turn**-এ force করবে।

প্রথম turn:

```text
tool_choice = {
    "type": "tool",
    "name": "extract_metadata"
}
```

তারপর metadata পাওয়া গেলে:

```text
tool_choice = {
    "type": "auto"
}
```

কারণ এরপর model-এর freedom দরকার।

সে decide করবে:

```text
extract_data_points
```

নাকি

```text
summarise_content
```

নাকি

```text
verify_claim
```

ব্যবহার করবে।

---

# 10. Generic `fetch_url` কেন Bad Design?

ধরো তোমার কাছে একটা tool আছে:

```text
fetch_url
```

এটা যেকোনো URL fetch করতে পারে।

যেমন:

```text
https://example.com
https://some-site.com/file.pdf
https://random-site.com/api
```

Problem হলো agent-এর কাছে অনেক বেশি capability চলে যাচ্ছে।

Agent document load করার জন্য tool পেয়েছে, কিন্তু technically সেটা arbitrary resource fetch করতে পারছে।

এটা **least-privilege** principle-এর বিরুদ্ধে যায়।

---

# 11. `fetch_url` → `load_document`

তাই generic:

```text
fetch_url
```

replace করে:

```text
load_document
```

করতে হবে।

এখানে tool শুধু **document URLs** accept করবে।

যেমন allowed হতে পারে:

```text
.pdf
.docx
.md
```

অথবা trusted document domains:

```text
docs.example.com
files.example.com
```

---

# 12. URL Validation

`load_document` call করার আগে URL validate করবে।

Conceptually:

```text
URL
 ↓
Is it a document URL?
 ↓
YES → Load document
NO  → Reject
```

উদাহরণ:

```text
https://example.com/report.pdf
```

→ accepted

কিন্তু:

```text
https://example.com/random-page
```

→ rejected

আর rejection-টা clear/structured হওয়া উচিত।

যেমন conceptually:

```text
{
    "isError": true,
    "errorCategory": "INVALID_DOCUMENT_URL",
    "description": "URL is not a supported document URL."
}
```

এখানে মূল principle হলো:

> **Tool যতটা capability দরকার, ঠিক ততটাই capability দেবে।**

এটাই **least-privilege tool design**।

---

# 13. পুরো Tool Distribution

শেষে তোমার architecture মোটামুটি এমন হবে:

```text
                    Coordinator
                         │
          ┌──────────────┼──────────────┐
          ↓              ↓              ↓
   Web Search       Document         Synthesis
      Agent          Analysis          Agent
                      Agent
          │              │              │
   search_web      extract_metadata  compile_report
   fetch_page      extract_data_points format_citation
   extract_links   summarise_content  assess_coverage
   save_snippet    verify_claim       verify_fact
```

এখানে:

* Web Search Agent → web-related কাজ
* Document Analysis Agent → document-related কাজ
* Synthesis Agent → final synthesis
* `verify_fact` → Synthesis-এর জন্য **scoped cross-role capability**
* complex verification → coordinator-এ escalate

---

# 14. শেষ Task: End-to-End Test

শেষে এমন একটা query দিয়ে পুরো system test করতে হবে যেটার জন্য তিনটা agent-ই দরকার।

Exercise-এর example:

> **"Research the latest MCP specification changes and compile a summary report."**

এখানে naturally তিনটা role লাগবে।

### Step 1 — Web Search Agent

সে করবে:

```text
search_web
fetch_page
extract_links
save_snippet
```

Latest MCP specification changes খুঁজবে।

---

### Step 2 — Document Analysis Agent

Relevant documents পেলে:

প্রথমে বাধ্যতামূলকভাবে:

```text
extract_metadata
```

তারপর প্রয়োজন অনুযায়ী:

```text
extract_data_points
summarise_content
verify_claim
```

---

### Step 3 — Synthesis Agent

সব collected information নিয়ে:

```text
compile_report
format_citation
assess_coverage
```

ব্যবহার করবে।

কোনো simple fact check দরকার হলে:

```text
verify_fact
```

ব্যবহার করবে।

---

# 15. Cross-Role Misuse Check

Test-এর সময় **প্রতিটা tool call log করতে হবে**।

Format হতে পারে:

```text
Agent: Web Search
Tool: search_web

Agent: Web Search
Tool: fetch_page

Agent: Document Analysis
Tool: extract_metadata

Agent: Document Analysis
Tool: summarise_content

Agent: Synthesis
Tool: verify_fact

Agent: Synthesis
Tool: compile_report
```

তারপর check করবে:

```text
Web Search Agent
→ শুধু Web Search tools?

Document Analysis Agent
→ প্রথমেই extract_metadata?

Synthesis Agent
→ শুধু নিজের scoped tools?

কোনো agent অন্য role-এর tool call করেছে?
→ NO
```

যদি এমন কিছু দেখো:

```text
Synthesis Agent → search_web
```

তাহলে problem আছে।

কারণ Synthesis Agent-এর web search করার কথা না। তার কাছে প্রয়োজনীয় search results coordinator/other agent থেকে আসার কথা।

---

# এই Exercise-এর আসল শেখার বিষয়

এই exercise-টা আসলে **tool quantity-এর চেয়ে tool boundaries** নিয়ে বেশি।

মনে রাখার মতো core rules:

| Concept                    | কী মনে রাখবে                                      |
| -------------------------- | ------------------------------------------------- |
| **4–5 tools per agent**    | Tool overload কমায়                                |
| **Role-based scoping**     | যে agent যে কাজ করে, সেই কাজের tools              |
| **Scoped cross-role tool** | common/simple কাজ agent নিজেই করবে                |
| **Coordinator escalation** | complex case coordinator-এর কাছে যাবে             |
| **`auto`**                 | model freely tool choose করে                      |
| **`any`**                  | কোনো একটা tool call করতেই হবে                     |
| **forced**                 | নির্দিষ্ট tool call করতেই হবে                     |
| **Forced first turn**      | mandatory workflow step enforce করতে              |
| **Least privilege**        | generic capability না দিয়ে constrained capability |
| **URL validation**         | `load_document` শুধু valid document URL নেবে      |
| **End-to-end testing**     | কোনো cross-role tool misuse হচ্ছে কিনা verify করা |

### এক লাইনে পুরো exercise

> **প্রতিটা agent-কে তার role অনুযায়ী অল্প কয়েকটা scoped tools দাও, mandatory step-এ forced `tool_choice` ব্যবহার করো, simple cross-role কাজের জন্য constrained tool দাও, আর generic powerful tools-এর বদলে least-privilege alternatives ব্যবহার করো।**
