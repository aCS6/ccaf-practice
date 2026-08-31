এই exercise-টা আগেরটার সাথে closely related, কিন্তু এখানে **Agent SDK Hooks** নিয়ে কাজ করা হচ্ছে। মূল focus হলো—**কোন কাজ tool execute হওয়ার আগে করতে হবে আর কোন কাজ tool execute হওয়ার পরে করতে হবে।**

সবচেয়ে আগে এই দুইটা মাথায় ঢুকিয়ে নাও:

> **PostToolUse = কাজ হয়ে গেছে → result/data modify/normalise করো**
> **PreToolUse = কাজ হওয়ার আগেই → policy check করে দরকার হলে block করো**

---

# Implement Agent SDK Hooks for Normalisation and Policy Enforcement

### Difficulty

**60 minutes**

এই exercise-এ তুমি এমন একটা Agent বানাবে যার multiple MCP tools থেকে data আসবে, কিন্তু প্রত্যেকটা tool data আলাদা format-এ return করবে।

তারপর:

* **PostToolUse hook** → data-কে standard format-এ convert করবে
* **PreToolUse hook** → dangerous/unauthorized tool call execute হওয়ার আগেই block করবে

---

# প্রথমে পুরো conceptটা

ধরো তিনটা MCP tool আছে:

```text
Tool A → Unix timestamp + numeric status
Tool B → ISO 8601 + string status
Tool C → DD/MM/YYYY + character status
```

তাহলে model-এর সামনে data আসছে:

```text
Tool A:
created_at = 1756502400
status = 200

Tool B:
created_at = "2026-08-30T10:00:00Z"
status = "active"

Tool C:
created_at = "30/08/2026"
status = "A"
```

Model-কে যদি এগুলো নিজে interpret করতে দাও, তাহলে ambiguity তৈরি হতে পারে।

তাই **PostToolUse hook** মাঝখানে দাঁড়িয়ে সবকিছুকে একটা common format-এ convert করবে।

---

# সবচেয়ে important distinction

## PostToolUse

```text
Tool executes
      ↓
Tool returns result
      ↓
PostToolUse Hook
      ↓
Normalise / Transform
      ↓
Model receives result
```

অর্থাৎ:

> **After execution → transform the result**

---

## PreToolUse

```text
Agent wants to call tool
          ↓
PreToolUse Hook
          ↓
Policy check
      ↙        ↘
   BLOCK      ALLOW
     ↓          ↓
  Nothing    Tool executes
```

অর্থাৎ:

> **Before execution → enforce policy**

---

# Step 1 — তিনটা MCP Tools তৈরি করা

তিনটা mock MCP tool বানাতে হবে।

প্রত্যেকটা tool-এর অন্তত:

```text
created_at
status
```

field থাকবে।

কিন্তু প্রত্যেকটার format আলাদা হবে।

---

## Tool A

Tool A return করবে:

* Date → **Unix timestamp / epoch seconds**
* Status → **numeric code**

Example:

```json
{
  "created_at": 1756502400,
  "status": 200
}
```

এখানে:

```text
1756502400 → Unix timestamp
200 → numeric status code
```

---

## Tool B

Tool B return করবে:

* Date → **ISO 8601**
* Status → **English string**

Example:

```json
{
  "created_at": "2026-08-30T10:00:00Z",
  "status": "active"
}
```

এটা already relatively clean format।

---

## Tool C

Tool C return করবে:

* Date → **DD/MM/YYYY**
* Status → **single-character code**

Example:

```json
{
  "created_at": "30/08/2026",
  "status": "S"
}
```

যেখানে:

```text
S = shipped
P = pending
```

---

# কেন এই format chaos তৈরি করা হচ্ছে?

কারণ বাস্তবে multiple MCP/API/tool-এর data format একরকম নাও হতে পারে।

ধরো:

```text
Tool A → 1756502400
Tool B → 2026-08-30T10:00:00Z
Tool C → 30/08/2026
```

তিনটাই একই date represent করছে।

কিন্তু model-কে যদি raw data দেওয়া হয়, তাকে প্রত্যেকবার format বুঝতে হবে।

এখানে **normalisation** দরকার।

---

# Step 2 — PostToolUse Hook

এখন একটি **PostToolUse hook** তৈরি করবে।

এর কাজ:

> Tool execution শেষ হওয়ার পর result intercept করা এবং model-এর কাছে পাঠানোর আগে data standardise করা।

Flow:

```text
MCP Tool
   ↓
Raw result
   ↓
PostToolUse
   ↓
Normalize
   ↓
Model
```

---

# Date Normalisation

Target format হবে:

> **ISO 8601**

তাই:

### Unix timestamp

```text
1756502400
```

কে convert করবে:

```text
2025-08-29T...
```

এরকম ISO 8601 format-এ।

### DD/MM/YYYY

```text
30/08/2026
```

কে convert করবে:

```text
2026-08-30
```

বা প্রয়োজন অনুযায়ী full ISO 8601 representation।

### Already ISO 8601

```text
2026-08-30T10:00:00Z
```

ISO 8601 format already ঠিক আছে, তাই কোনো পরিবর্তন না করে সেভাবেই থাকবে।

---

# Status Normalisation

এখানেও একই idea।

ধরো:

```text
Tool A:
200
```

এটা হতে পারে:

```text
active
```

Tool C:

```text
S
```

হবে:

```text
shipped
```

আর:

```text
P
```

হবে:

```text
pending
```

অর্থাৎ raw status:

```text
200
S
P
```

শেষে model-এর কাছে যাবে:

```text
active
shipped
pending
```

---

# Normalisation-এর পর

তিনটা tool-এর raw output:

```text
Tool A
created_at = 1756502400
status = 200

Tool B
created_at = "2026-08-30T10:00:00Z"
status = "active"

Tool C
created_at = "30/08/2026"
status = "S"
```

PostToolUse-এর পর model দেখতে পারে:

```text
Tool A
created_at = "2025-08-29T..."
status = "active"

Tool B
created_at = "2026-08-30T10:00:00Z"
status = "active"

Tool C
created_at = "2026-08-30"
status = "shipped"
```

এখন model-এর কাজ অনেক সহজ।

**সব tool-এর output একই convention follow করছে।**

---

# Step 3 — Verify Normalisation

এখন এমন একটা query দিতে হবে যাতে Agent-কে **তিনটা tool-ই call করতে হয়**।

যেমন customer সম্পর্কে:

* Customer information
* Order information
* Shipment status

সব একসাথে জানতে চাইবে।

তখন:

```text
Agent
 ├── Tool A
 ├── Tool B
 └── Tool C
```

তিনটা result আসবে।

প্রত্যেকটার উপর:

```text
PostToolUse
```

run করবে।

শেষে model-এর কাছে raw data যাবে না।

বরং সব normalised data যাবে।

---

# এখানে একটা subtle কিন্তু important point

PostToolUse **tool execution আটকাতে পারে না**।

কারণ:

```text
Tool executes
    ↓
Result আসে
    ↓
PostToolUse
```

Tool already execute হয়ে গেছে।

তাই PostToolUse দিয়ে:

> "এই refund execute হতে দেওয়া যাবে না"

এটা enforce করা যাবে না।

সেটার জন্য দরকার **PreToolUse**।

---

# Step 4 — PreToolUse: $500 Refund Policy

এখন `process_refund` নামে একটি tool ধরো।

Policy:

> **Refund amount > $500 হলে refund process করা যাবে না।**

এখানে **PreToolUse hook** ব্যবহার করতে হবে।

Flow:

```text
Agent
  ↓
process_refund(amount=1000)
  ↓
PreToolUse Hook
  ↓
amount > 500 ?
  ↓
YES
  ↓
BLOCK
```

সবচেয়ে important:

**`process_refund` execute-ই করবে না।**

---

## Example

Agent:

```text
process_refund(customer_id="C123", amount=1000)
```

PreToolUse দেখে:

```text
amount = 1000
1000 > 500
```

তারপর:

```text
BLOCK
→ Redirect to human escalation workflow
```

Refund tool-এর ভিতরের code পর্যন্ত call যাবে না।

---

# কেন PostToolUse এখানে ভুল?

যদি তুমি করো:

```text
process_refund()
      ↓
Refund happens
      ↓
PostToolUse
      ↓
"Oh, amount was > $500"
      ↓
BLOCK
```

তাহলে অনেক দেরি হয়ে গেছে।

**Refund already processed.**

তাই policy enforcement-এর জন্য:

> **PreToolUse = correct**

---

# Step 5 — AML prerequisite gate

এখন আরও serious policy।

দুইটা tool ধরো:

```text
aml_check
transfer_funds
```

Rule:

> **AML check pass না করলে `transfer_funds` execute করা যাবে না।**

এটা financial/compliance scenario।

---

# কীভাবে কাজ করবে?

Session-level state রাখবে।

শুরুতে:

```text
aml_passed = false
```

Agent যখন:

```text
aml_check()
```

call করে এবং result হয়:

```text
PASS
```

তখন:

```text
aml_passed = true
```

এখন:

```text
transfer_funds()
```

call করা যাবে।

---

# কিন্তু AML pass না করলে?

Agent যদি সরাসরি বলে:

```text
transfer_funds(amount=5000)
```

তাহলে:

```text
transfer_funds
      ↓
PreToolUse
      ↓
aml_passed?
      ↓
NO
      ↓
BLOCK
```

Transfer execute হবে না।

---

# Session-scoped state কেন?

আগের exercise-এর prerequisite gate-এর মতোই।

ধরো:

```text
Session A
─────────
aml_check → PASS
aml_passed = true
transfer_funds → allowed
```

কিন্তু নতুন session:

```text
Session B
─────────
aml_passed = false
```

Session A-এর AML approval Session B-তে automatically carry করা যাবে না।

---

# Step 6 — দুটো Hook Test করা

এখন দুই ধরনের test করতে হবে:

## Negative test — blocked

### Refund

```text
process_refund(amount=1000)
```

Expected:

```text
BLOCKED
```

এবং সবচেয়ে important:

```text
process_refund NEVER EXECUTED
```

---

### Transfer

AML check না করেই:

```text
transfer_funds()
```

Expected:

```text
BLOCKED
```

এবং:

```text
transfer_funds NEVER EXECUTED
```

---

# Positive test — allowed

প্রথমে refund amount কমাও:

```text
process_refund(amount=300)
```

Expected:

```text
PreToolUse
   ↓
300 <= 500
   ↓
ALLOW
   ↓
process_refund executes
```

---

AML-এর ক্ষেত্রে:

```text
aml_check()
      ↓
PASS
      ↓
aml_passed = true
      ↓
transfer_funds()
      ↓
ALLOW
      ↓
EXECUTE
```

---

# Test করার সময় সবচেয়ে important জিনিস

শুধু এটা check করলে হবে না:

```text
"Blocked message দেখাচ্ছে"
```

Check করতে হবে:

> **Underlying tool actually execute করেছে কি না।**

কারণ requirement হলো:

**Blocked tool-এর কোনো side effect থাকা যাবে না।**

যেমন refund-এর ক্ষেত্রে:

```text
❌ Refund record created
❌ Money refunded
❌ Transaction executed
```

এর কোনোটাই হওয়া উচিত না।

---

# পুরো Architecture একসাথে

```text
                    AGENT
                      │
             Wants to call a tool
                      │
                      ↓
               PreToolUse Hook
                      │
             ┌────────┴────────┐
             │                 │
          Policy OK?         Policy FAIL?
             │                 │
            YES                ↓
             │              BLOCK
             ↓
         Tool executes
             │
             ↓
         Tool Result
             │
             ↓
        PostToolUse Hook
             │
             ↓
       Normalise Data
             │
             ↓
           Model
```

এই diagram-টাই exercise-এর heart।

---

# PreToolUse বনাম PostToolUse

| বিষয়                      | PreToolUse            | PostToolUse           |
| ------------------------- | --------------------- | --------------------- |
| কখন চলে?                  | Tool execution-এর আগে | Tool execution-এর পরে |
| Main purpose              | Policy enforcement    | Data transformation   |
| Tool block করতে পারে?     | **YES**               | **NO**                |
| Data normalise?           | সাধারণত না            | **YES**               |
| Threshold check?          | **YES**               | না                    |
| Prerequisite check?       | **YES**               | না                    |
| Refund > $500 block       | **YES**               | ❌                     |
| AML prerequisite          | **YES**               | ❌                     |
| Date format normalisation | ❌                     | **YES**               |
| Status normalisation      | ❌                     | **YES**               |

---

# Exam-এর জন্য আসল decision framework

এটাই সবচেয়ে important part।

## Requirement যদি 100% mandatory হয়

যেমন:

```text
Refund must never exceed $500
AML must pass before transfer
Customer must be verified before refund
```

→ **Hook**

কারণ এখানে:

> **100% enforcement required**

Prompt-এর উপর depend করা যাবে না।

---

## Requirement যদি preference হয়

যেমন:

```text
Prefer concise responses
Prefer formal language
Usually show newest orders first
Try to answer politely
```

→ **Prompt**

কারণ এগুলো hard safety/compliance requirement না।

---

# সহজ একটা rule

মনে রাখো:

> **"Must" → Hook**
> **"Prefer" → Prompt**

আর hooks-এর ক্ষেত্রে:

> **Before action → PreToolUse**
> **After action/result → PostToolUse**

---

# Exam Mental Model

Question-এ যদি দেখো:

### "Block", "prevent", "must not execute", "before execution"

সরাসরি ভাববে:

**PreToolUse**

---

### "Transform", "normalise", "modify result", "after tool execution"

সরাসরি ভাববে:

**PostToolUse**

---

### "100% compliance", "regulatory requirement", "financial transaction"

ভাববে:

**Programmatic enforcement / Hook**

Prompt না।

---

## এক লাইনের cheat sheet

```text
PreToolUse  = STOP / ALLOW
PostToolUse = CLEAN / TRANSFORM
Prompt      = PREFERENCE / GUIDANCE
Hook        = DETERMINISTIC REQUIREMENT
```

এই exercise-এর পুরো উদ্দেশ্য basically এটুকুই: **LLM-কে শুধু instruction দিলে সেটা guidance; কিন্তু Hook দিয়ে tool execution-এর boundary-তে rule বসালে সেটা deterministic enforcement।**
