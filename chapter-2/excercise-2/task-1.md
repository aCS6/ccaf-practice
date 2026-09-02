এই exercise-এর মূল উদ্দেশ্য হলো **MCP tool-এর error response এমনভাবে structured করা**, যাতে Agent শুধু “error হয়েছে” বুঝে থেমে না যায়—বরং **কী ধরনের error, retry করা উচিত কি না, এবং কীভাবে recover করতে হবে** সেটা বুঝতে পারে।

এখানে সবচেয়ে গুরুত্বপূর্ণ তিনটা metadata:

* `errorCategory`
* `isRetryable`
* `description`

আর একটা খুব গুরুত্বপূর্ণ distinction হলো:

> **Valid empty result ≠ Error**

---

# Build Structured Error Responses for All Four Categories

**Difficulty: 45 minutes**

## What you'll learn

এই exercise শেষে তুমি পারবে:

1. `errorCategory`, `isRetryable`, `description` metadata সহ structured error response তৈরি করতে।
2. `isError: true` থাকা **access failure** আর `isError: false` থাকা **valid empty result** আলাদা করতে।
3. Tool failure-কে চার category-তে ভাগ করতে:

   * `transient`
   * `validation`
   * `business`
   * `permission`
4. Error metadata দেখে Agent-কে আলাদা recovery action নিতে দিতে।

---

# প্রথমে পুরো concept-টা বুঝি

ধরো Agent একটা `customer_lookup` MCP tool call করল।

সাধারণভাবে tool যদি শুধু বলে:

```text
Error: request failed
```

তাহলে Agent জানে না:

* আবার retry করবে?
* input ঠিক করবে?
* human-এর কাছে escalate করবে?
* নতুন credentials চাইবে?

এখানেই **structured error response** দরকার।

যেমন:

```json
{
  "errorCategory": "transient",
  "isRetryable": true,
  "description": "The request timed out. Retry the same request after a short delay."
}
```

এখন Agent খুব সহজেই বুঝতে পারবে:

> এটা `transient` error → retry করা যায় → একটু wait করে আবার একই request পাঠাও।

---

# Step 1 — MCP tool তৈরি করা

প্রথম কাজ হলো একটা MCP tool বানানো যেটা একটা mock customer database query করবে।

Tool-এর নাম হতে পারে:

```text
customer_lookup
```

এটা দুইটা parameter নেবে:

```text
identifier
failure_mode
```

### `identifier`

Customer-এর identifier।

যেমন:

```text
customer-123
```

### `failure_mode`

কোন failure simulate করতে হবে সেটা control করবে।

যেমন:

```text
none
timeout
invalid_input
refund_limit
access_denied
```

এভাবে তুমি ইচ্ছামতো বিভিন্ন failure trigger করতে পারবে।

### কেন এটা করা হচ্ছে?

Real production system-এ সব ধরনের error reliably reproduce করা কঠিন।

কিন্তু mock failure mode ব্যবহার করলে তুমি controlled environment-এ দেখতে পারবে:

> Agent একটা নির্দিষ্ট error পেলে কীভাবে behave করে?

এই exercise-এর exam angle-টাও এখানেই—**poorly structured errors Agent-কে unnecessary retry বা ভুল escalation করাতে পারে।**

### কী ব্যবহার করবে?

MCP SDK-এর:

```text
McpServer
```

ব্যবহার করে tool define করবে।

আর `failure_mode`-এর জন্য `enum` ব্যবহার করবে, যাতে নির্দিষ্ট failure scenario predictable ভাবে trigger করা যায়।

---

# Step 2 — Four ধরনের error implement করা

এখন চারটা error category তৈরি করতে হবে।

| Error                  | `errorCategory` | `isRetryable` | Agent-এর action            |
| ---------------------- | --------------- | ------------: | -------------------------- |
| Timeout                | `transient`     |        `true` | Retry                      |
| Invalid input          | `validation`    |       `false` | Input ঠিক করে আবার call    |
| Refund policy exceeded | `business`      |       `false` | Human-এর কাছে escalate     |
| Access denied          | `permission`    |       `false` | Credentials/request access |

---

## 1. Transient error

ধরো database request timeout করেছে।

এটা temporary problem হতে পারে। কিছুক্ষণ পর একই request আবার successful হতে পারে।

তাই:

```json
{
  "errorCategory": "transient",
  "isRetryable": true,
  "description": "The customer lookup timed out. Retry the same request after a short delay."
}
```

এখানে সবচেয়ে গুরুত্বপূর্ণ:

```text
isRetryable: true
```

কারণ **identical request আবার পাঠালে কাজ করার সম্ভাবনা আছে।**

---

## 2. Validation error

ধরো customer identifier-এর format ভুল।

যেমন expected:

```text
customer-123
```

কিন্তু দেওয়া হয়েছে:

```text
abc
```

এটা retry করে লাভ নেই।

একই ভুল input আবার পাঠালে আবার একই error হবে।

তাই:

```json
{
  "errorCategory": "validation",
  "isRetryable": false,
  "description": "The customer identifier has an invalid format. Correct the identifier and submit a new request."
}
```

খেয়াল করো:

`isRetryable: false`

কিন্তু এর মানে **Agent পুরোপুরি stop করবে না।**

Agent input ঠিক করে **fresh call** করতে পারে।

---

# 3. Business error

ধরো customer refund চাইছে, কিন্তু refund amount policy limit-এর বেশি।

যেমন policy maximum:

```text
$500
```

কিন্তু request:

```text
$1000
```

এটা technical failure না।

System perfectly কাজ করেছে, কিন্তু **business rule allow করছে না।**

তাই:

```json
{
  "errorCategory": "business",
  "isRetryable": false,
  "description": "The refund amount exceeds the policy limit. Escalate the request for human review."
}
```

এখানে একই request retry করলে কোনো লাভ নেই।

তাই:

```text
business → don't retry → escalate
```

---

# 4. Permission error

ধরো Agent-এর customer data access করার permission নেই।

তাহলে:

```json
{
  "errorCategory": "permission",
  "isRetryable": false,
  "description": "Access to customer data was denied. Request elevated credentials or appropriate access before retrying."
}
```

এখানেও identical request retry করলে কাজ করবে না।

আগে **credentials/access** ঠিক করতে হবে।

---

# Step 3 — Structured metadata consistent রাখা

এখানে exercise-এর একটা খুব গুরুত্বপূর্ণ requirement আছে।

প্রতিটা error response-এ অবশ্যই এই তিনটা field থাকতে হবে:

```text
errorCategory
isRetryable
description
```

অর্থাৎ response structure consistent হবে।

### `errorCategory`

চারটার যেকোনো একটা:

```text
transient
validation
business
permission
```

### `isRetryable`

শুধু:

```text
true
```

অথবা:

```text
false
```

### `description`

Human-readable explanation + recovery guidance।

যেমন:

```text
The request timed out. Retry after a short delay.
```

---

## Helper function কেন দরকার?

প্রতিবার manually error response লিখলে একটা field বাদ পড়ে যেতে পারে।

তাই একটা helper function বানানো ভালো:

```text
buildErrorResponse(...)
```

যেটা নিশ্চিত করবে প্রত্যেকটা error-এর মধ্যে তিনটা field-ই আছে।

Conceptually:

```text
buildErrorResponse(
    category,
    retryable,
    description
)
```

তারপর:

```text
transient → buildErrorResponse(...)
validation → buildErrorResponse(...)
business → buildErrorResponse(...)
permission → buildErrorResponse(...)
```

এতে structure consistent থাকবে।

---

# JSON.parse() দিয়ে verify করা

Exercise বলছে response-গুলো `JSON.parse()` দিয়ে verify করতে।

কারণ যদি response এমন হয়:

```json
{
  "errorCategory": "transient",
  "isRetryable": "true",
  "description": "..."
}
```

তাহলে technically `"true"` একটা **string**, boolean না।

Expected:

```json
"isRetryable": true
```

অর্থাৎ type-ও ঠিক রাখতে হবে।

প্রতিটা response parse করে check করবে:

* `errorCategory` আছে?
* এটা string?
* `isRetryable` আছে?
* এটা boolean?
* `description` আছে?
* এটা string?

---

# Step 4 — Valid empty result বনাম Error

এটাই exercise-এর **সবচেয়ে গুরুত্বপূর্ণ অংশগুলোর একটা।**

ধরো Agent customer `customer-999` খুঁজল।

Database successfully query করেছে।

কিন্তু customer পাওয়া যায়নি।

এটা **error না**।

কারণ query successfully execute হয়েছে।

তাই response হতে পারে:

```json
{
  "isError": false,
  "resultCount": 0
}
```

মানে:

> Query successfully executed, but there were no matching results.

---

## অন্যদিকে Access failure

ধরো database-এ query চালাতেই পারল না কারণ temporary access problem হয়েছে।

তাহলে:

```json
{
  "isError": true,
  "errorCategory": "transient",
  "isRetryable": true
}
```

মানে:

> Query execute-ই হয়নি।

---

## Differenceটা মাথায় গেঁথে নাও

### Empty result

```text
Query executed
       ↓
No customer found
       ↓
isError: false
       ↓
Don't retry
```

### Access failure

```text
Query could not execute
       ↓
Error
       ↓
isError: true
       ↓
Check metadata
       ↓
Maybe retry
```

সবচেয়ে common mistake হবে:

> `resultCount: 0` দেখে Agent আবার retry করছে।

এটা unnecessary।

**Successful query + zero results = valid result.**

---

# Step 5 — Agent recovery loop

এখন পুরো concept-টা practical করতে Agent loop বানাতে হবে।

Agent প্রথমে tool call করবে।

যদি success হয়:

```text
return result
```

যদি error হয়:

```text
parse error metadata
        ↓
read errorCategory
        ↓
choose recovery action
```

---

## `transient`

যদি:

```text
errorCategory = transient
isRetryable = true
```

তাহলে retry করবে।

কিন্তু unlimited retry করবে না।

Exercise অনুযায়ী maximum:

```text
3 retries
```

এবং exponential backoff ব্যবহার করবে:

```text
1s
2s
4s
```

মানে:

```text
attempt 1 → wait 1s
attempt 2 → wait 2s
attempt 3 → wait 4s
```

এতে temporary outage হলে system বারবার immediately hammer করবে না।

---

# `validation`

যদি:

```text
errorCategory = validation
isRetryable = false
```

তাহলে একই request আবার পাঠাবে না।

বরং `description` দেখে input ঠিক করবে।

Flow:

```text
Invalid input
     ↓
Read description
     ↓
Fix arguments
     ↓
Fresh tool call
```

এখানে একটা subtle point:

> `isRetryable: false` মানেই “Agent stop করবে” না।

এটার অর্থ হলো:

> **identical request retry করা উচিত না।**

Validation-এর ক্ষেত্রে input পরিবর্তন করে নতুন request করা যায়।

---

# `business`

যদি:

```text
errorCategory = business
```

তাহলে:

```text
Don't retry
     ↓
Escalate to human
     ↓
Stop
```

কারণ business policy violation automatic retry দিয়ে solve হবে না।

যেমন:

```text
Refund = $1000
Policy limit = $500
```

একই $1000 refund request ১০ বার পাঠালেও policy limit magically change হবে না।

---

# `permission`

যদি:

```text
errorCategory = permission
```

তাহলে:

```text
Don't retry immediately
        ↓
Request elevated credentials/access
        ↓
Stop current flow
```

আগে permission ঠিক করতে হবে।

---

# পুরো recovery logic একসাথে

তোমার Agent-এর mental model এমন হবে:

```text
Tool call
   ↓
Success?
 ┌─┴───────────────┐
Yes                No
 ↓                  ↓
Return         Read metadata
result              ↓
              errorCategory
                   ↓
      ┌────────────┼────────────┬─────────────┐
      ↓            ↓            ↓             ↓
 transient     validation    business     permission
      ↓            ↓            ↓             ↓
   retry       fix input    escalate     request access
      ↓            ↓            ↓
  max 3        fresh call    stop
```

---

# এই exercise-এর আসল lesson

এখানে শুধু error handling শেখানো হচ্ছে না। মূল বিষয় হলো:

> **Agent-কে meaningful structured information দিলে Agent intelligent recovery করতে পারে।**

শুধু:

```text
Error occurred
```

দিলে Agent বুঝতে পারবে না কী করা উচিত।

কিন্তু:

```json
{
  "errorCategory": "validation",
  "isRetryable": false,
  "description": "Fix the customer identifier format and submit a new request."
}
```

দিলে Agent বুঝতে পারে:

```text
Not retry identical call
        ↓
Fix input
        ↓
Call again
```

---

# Exam-এর জন্য সবচেয়ে গুরুত্বপূর্ণ SIGNAL

এই চারটা mapping মনে রাখো:

| Category     |  Retry? | Recovery               |
| ------------ | ------: | ---------------------- |
| `transient`  | **Yes** | Retry with backoff     |
| `validation` |  **No** | Fix input → fresh call |
| `business`   |  **No** | Escalate               |
| `permission` |  **No** | Get credentials/access |

আর সবচেয়ে গুরুত্বপূর্ণ distinction:

```text
isError: false + resultCount: 0
        =
SUCCESSFUL query, but no result
```

অন্যদিকে:

```text
isError: true
        =
Tool execution failed
```

### এক লাইনে পুরো exercise:

**`errorCategory` বলে কী ধরনের সমস্যা, `isRetryable` বলে একই request আবার পাঠানো worth it কি না, আর `description` Agent-কে next recovery action বুঝতে সাহায্য করে।**
