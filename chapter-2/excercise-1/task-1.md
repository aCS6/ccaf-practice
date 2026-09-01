এই exercise-এর মূল বিষয় হলো **LLM কীভাবে একাধিক MCP tools-এর মধ্যে সঠিক tool নির্বাচন করে**, আর সেখানে **tool description** কতটা গুরুত্বপূর্ণ।

এখানে তুমি ইচ্ছা করে একটা **misrouting problem** তৈরি করবে, তারপর শুধু tool description ভালো করে লিখে দেখবে যে selection accuracy কীভাবে improve করে।

---

# Build Exercise: Design Tool Descriptions That Eliminate Misrouting

**Difficulty:** 30 minutes

## Exercise-এর মূল idea

ধরো তোমার কাছে দুইটা MCP tool আছে:

* `get_customer` → customer-এর information বের করে
* `lookup_order` → order-এর details বের করে

দুটোর description যদি এমন হয়:

```text
get_customer: Retrieves customer information.
lookup_order: Retrieves order details.
```

তাহলে LLM-এর জন্য সমস্যা হবে।

User যদি বলে:

> "Can you check my account?"

এখানে কোন tool ব্যবহার করবে?

`get_customer`?
`lookup_order`?

Description থেকে LLM যথেষ্ট signal পাচ্ছে না।

আবার user যদি বলে:

> "What is the status of my order?"

এটা clearly order-related হলেও যদি descriptions খুব generic হয়, model ভুল tool select করতে পারে।

এই exercise-এ তুমি প্রথমে এই ambiguity তৈরি করবে, তারপর description improve করে দেখবে **misrouting কমে যায় কিনা।**

---

# What you'll learn

এই exercise শেষে তোমার কয়েকটা important জিনিস clear হওয়া উচিত।

### 1. Tool descriptions are the primary mechanism for tool selection

LLM যখন available tools-এর মধ্যে কোনটা ব্যবহার করবে সেটা decide করে, তখন **tool description** তার সবচেয়ে গুরুত্বপূর্ণ signal-এর একটা।

মানে শুধু tool-এর নাম:

```text
get_customer
lookup_order
```

দিলেই যথেষ্ট না।

Description-এ clearly বলতে হবে:

* tool কী করে
* কী input নেয়
* কোন ধরনের query-এর জন্য
* কোন ক্ষেত্রে ব্যবহার করা যাবে না

---

### 2. Production-grade tool description কীভাবে লিখতে হয়

একটা ভালো description শুধু:

> "Retrieves customer information."

এরকম one-liner হবে না।

Production-grade description-এ ideally থাকবে:

1. **Purpose** — tool কী করে
2. **Inputs** — কী input নেয় এবং format কী
3. **Examples** — কোন ধরনের user query-এর জন্য
4. **Edge cases** — unusual/ambiguous cases কীভাবে handle করবে
5. **Boundaries** — কোন কাজের জন্য tool-টা ব্যবহার করা যাবে না

এই পাঁচটা এই exercise-এর সবচেয়ে important concept।

---

### 3. Ambiguous descriptions থেকে misrouting হয়

দুটো tool যদি প্রায় একই ধরনের generic description দেয়, তাহলে model-এর কাছে তাদের মধ্যে distinction করা কঠিন হয়ে যায়।

যেমন:

```text
get_customer: Retrieves customer information.
lookup_order: Retrieves order details.
```

এখানে:

> "Check my account"

এর মতো query-এর জন্য clear boundary নেই।

তাই model ভুল tool select করতে পারে।

---

### 4. System prompt-ও tool selection-এ interfere করতে পারে

এটা exercise-এর একটু subtle অংশ।

ধরো system prompt-এ লেখা আছে:

```text
Always check customer details when handling user requests.
```

এখন user বলল:

> "Where is my order?"

Tool descriptions ভালো হলেও system prompt-এর **"customer details"** instruction model-কে `get_customer`-এর দিকে push করতে পারে।

অর্থাৎ শুধু tool description ভালো হলেই সবসময় problem solve হবে না।

**System prompt + tool descriptions** দুটোই দেখতে হবে।

---

# Step 1 — Intentionally ambiguous tools তৈরি করা

প্রথমে দুইটা MCP tool তৈরি করবে:

```text
get_customer
lookup_order
```

ইচ্ছা করেই তাদের description খুব vague রাখবে।

যেমন:

```text
get_customer: Retrieves customer information.
lookup_order: Retrieves order details.
```

### কেন ইচ্ছা করে খারাপ description?

কারণ আগে নিজে misrouting দেখলে পরে বুঝতে পারবে **কেন minimal descriptions fail করে।**

এটা শুধু theory না—তুমি হাতে-কলমে problem reproduce করবে।

---

## MCP SDK inputSchema

দুইটা tool-এর `inputSchema`-তে একটি `string` parameter থাকবে, যেটা identifier হিসেবে কাজ করবে।

Conceptually:

```text
get_customer
    identifier: string

lookup_order
    identifier: string
```

কিন্তু description-এ এখনো বেশি information দেবে না।

অর্থাৎ এই stage-এ description হবে **single generic sentence**।

### Expected result

তোমার MCP server-এ দুইটা tool registered থাকবে:

```text
get_customer
lookup_order
```

এবং প্রত্যেকটার description হবে মাত্র এক sentence-এর মতো।

Description-এ থাকবে না:

* input format
* example query
* boundaries

---

# Nudge — এখানে কী missing?

নিজেকে প্রশ্ন করো:

### `get_customer` কী input নেয়?

Email?

Phone number?

Customer ID?

### `lookup_order` কী input নেয়?

Order number?

Tracking ID?

Order ID?

### কোন situation-এ কোনটা ব্যবহার করবে?

যেমন:

> "Find customer information for [john@example.com](mailto:john@example.com)"

এটা `get_customer`.

কিন্তু:

> "Where is order #12345?"

এটা `lookup_order`.

### Ambiguous case কী?

যেমন:

> "Check my account."

এটা customer-related হতে পারে, আবার order-related context-ও হতে পারে।

Tool description-এ এই distinction না থাকলে model guess করবে।

---

# Step 2 — 10টা query দিয়ে test করা

এখন তোমার দুইটা tool available রেখে **10টা different user query** test করবে।

প্রতিটা query-এর জন্য log করবে:

```text
User Query
Expected Tool
Selected Tool
Correct / Incorrect
```

---

## কেন 10টা query?

কারণ শুধু ১-২টা example দেখে বলা যাবে না যে tool selection ভালো বা খারাপ।

10টা query দিয়ে তুমি **selection accuracy quantify** করতে পারবে।

ধরো result হলো:

| Query                                                     | Expected     | Selected     |
| --------------------------------------------------------- | ------------ | ------------ |
| Find customer [john@example.com](mailto:john@example.com) | get_customer | get_customer |
| Where is order #12345?                                    | lookup_order | get_customer |
| Check tracking ID TRK999                                  | lookup_order | lookup_order |
| Find customer by phone                                    | get_customer | get_customer |
| Check my account                                          | get_customer | lookup_order |

এখানে তুমি actual misrouting দেখতে পাচ্ছ।

---

# কী ধরনের query দিতে হবে?

শুধু straightforward query দিলেই হবে না।

Different intent cover করবে।

বিশেষ করে:

### Customer-related

> "Find the customer with email [john@example.com](mailto:john@example.com)."

> "Look up customer 017XXXXXXXX."

### Order-related

> "Where is order #12345?"

> "What's the status of order #54321?"

### Tracking-related

> "Check tracking ID TRK12345."

### Ambiguous

> "Check my account."

> "Can you look this up for me?"

এই ধরনের query model-এর জন্য বেশি challenging।

---

# Nudge

কমপক্ষে এই ধরনের input রাখো:

* order numbers
* customer emails
* tracking IDs
* ambiguous phrases
* customer identifiers

লক্ষ্য হলো শুধু obvious query না, **edge cases-ও test করা।**

---

# Guidance — Test harness

একটা simple test harness তৈরি করবে।

প্রতিটা query Claude API-তে পাঠাবে এবং available tools হিসেবে দুটো tool দেবে।

Tool selection হবে:

```text
tool_choice = auto
```

মানে model নিজেই decide করবে কোন tool call করবে।

তারপর log করবে model কোন tool select করেছে।

---

# Expected result

এই stage-এ তোমার ideally **2–3টা misrouted query** দেখতে পাওয়া উচিত।

যেমন:

```text
"Where is order #12345?"
```

Expected:

```text
lookup_order
```

কিন্তু model select করল:

```text
get_customer
```

অথবা উল্টোটা।

এটাই তোমার baseline।

অর্থাৎ এখন তুমি জানো:

> **Generic tool descriptions → ambiguous tool selection → misrouting**

---

# Step 3 — Tool descriptions improve করা

এখন আসল কাজ।

দুইটা description rewrite করবে।

প্রতিটা description প্রায় **3–5 sentences** হবে।

এবার description-এ পাঁচটা জিনিস explicitly রাখবে:

### 1. Purpose

Tool কী কাজ করে?

### 2. Inputs

কী ধরনের identifier নেয়?

Format কী?

### 3. Examples

কী ধরনের user query-এর জন্য এই tool ব্যবহার করতে হবে?

### 4. Edge cases

Ambiguous বা unusual input কীভাবে interpret করবে?

### 5. Boundaries

কোন কাজের জন্য এই tool **ব্যবহার করবে না**?

এবং দরকার হলে অন্য tool-এর নাম explicitly mention করবে।

---

# Example — improved `get_customer`

ধরো customer tool email বা phone দিয়ে customer খুঁজবে।

তাহলে description conceptually এমন হতে পারে:

```text
Retrieves customer profile information using a customer email address or phone number. 
Use this tool for queries asking about customer identity, profile, contact information, or account details. 
For example, use it for requests such as "Find the customer with john@example.com" or "Look up the customer with phone number 01712345678." 
Do NOT use this tool for order status, order details, or shipment tracking; use lookup_order for those requests.
```

এখানে model অনেক বেশি signal পাচ্ছে।

---

# Example — improved `lookup_order`

```text
Retrieves order information using an order number or tracking ID. 
Use this tool for queries about order status, order details, delivery, or shipment tracking. 
For example, use it for requests such as "What's the status of order #12345?" or "Track shipment TRK12345." 
Do NOT use this tool for customer profile or account information; use get_customer for those requests.
```

এখানে distinction একদম clear।

---

# সবচেয়ে important অংশ: Boundary

এই exercise-এর একটা high-value concept হলো **explicit boundary**।

শুধু বলবে না:

> "Retrieves order information."

বরং বলবে:

> **"Do NOT use this tool for customer profile information; use get_customer instead."**

এটা model-কে শুধু বলে না tool কী করে, বরং **কখন tool-টা ব্যবহার করা উচিত নয়** সেটাও বলে।

এতে overlapping tools-এর মধ্যে routing অনেক reliable হয়।

---

# Nudge — পাঁচটা প্রশ্ন

প্রতিটা tool description লেখার সময় এই পাঁচটা প্রশ্নের উত্তর দাও:

### `get_customer`

1. What does it do?
2. What inputs does it accept?
3. What queries suit it?
4. What does it NOT handle?
5. When should `lookup_order` be used instead?

একইভাবে `lookup_order`-এর জন্যও।

এই পাঁচটা প্রশ্নের উত্তর description-এর মধ্যে থাকলে সাধারণত routing অনেক clearer হবে।

---

# Specific input formats দাও

Generic:

```text
Accepts an identifier.
```

এর চেয়ে specific:

```text
Accepts customer email addresses such as john@example.com or phone numbers such as 01712345678.
```

Order-এর ক্ষেত্রে:

```text
Accepts order numbers such as #12345 or tracking IDs such as TRK12345.
```

এই format examples model-এর জন্য useful signal তৈরি করে।

---

# Return data shape-ও mention করতে পারো

Exercise specifically বলে **return data shape**-ও explicitly state করতে।

যেমন `get_customer`:

```text
Returns customer profile data including customer ID, name, email, and phone number.
```

আর `lookup_order`:

```text
Returns order data including order ID, status, items, and shipment/tracking information.
```

এতে tool-এর purpose আরও clear হয়।

---

# Step 4 — আবার একই 10টা query run করো

এবার সবচেয়ে important rule:

**নতুন query বানাবে না।**

আগের exact একই 10টা query আবার run করবে।

কারণ তুমি জানতে চাচ্ছ:

> Description পরিবর্তন করার কারণে selection কতটা improve হলো?

Architecture change করোনি।

Model change করোনি।

Queries change করোনি।

শুধু **tool descriptions** improve করেছ।

---

# Before vs After comparison

একটা comparison table বানাবে:

| Query                                            | Expected Tool | Before         | After          |
| ------------------------------------------------ | ------------- | -------------- | -------------- |
| Find [john@example.com](mailto:john@example.com) | get_customer  | get_customer   | get_customer   |
| Status of #12345                                 | lookup_order  | get_customer ❌ | lookup_order ✅ |
| Track TRK999                                     | lookup_order  | get_customer ❌ | lookup_order ✅ |
| Find customer by phone                           | get_customer  | get_customer   | get_customer   |

এরপর accuracy calculate করবে।

ধরো আগে:

```text
7/10 = 70%
```

পরে:

```text
10/10 = 100%
```

তাহলে খুব clear evidence পাওয়া গেল যে **description quality-ই routing problem-এর বড় কারণ ছিল।**

---

# Expected result

ভালো description দেওয়ার পর ideally:

```text
9/10 or 10/10
```

selection correct হবে।

বিশেষ করে যেসব query আগে misroute হচ্ছিল, সেগুলো এখন correct tool-এ যাওয়া উচিত।

---

# Step 5 — System prompt check করা

এখন exercise-এর শেষ এবং একটু tricky অংশ।

Tool descriptions perfect হওয়ার পরেও যদি routing ভুল হয়, তাহলে **system prompt** inspect করবে।

কারণ system prompt-এর কোনো instruction tool description-এর সাথে conflict করতে পারে।

---

## Example of a problematic system prompt

ধরো system prompt-এ আছে:

```text
Always check customer details before answering user requests.
```

User বলল:

> "Where is my order #12345?"

এখন system prompt model-কে customer tool-এর দিকে push করতে পারে।

যদিও `lookup_order` description clearly বলেছে:

> order-related queries → use lookup_order

এখানে একটা **keyword-sensitive association** তৈরি হয়েছে:

```text
customer → get_customer
```

এবং model order query-এর মধ্যেও customer tool select করতে পারে।

---

# Nudge — কোন keyword খুঁজবে?

System prompt review করার সময় এই ধরনের words খুঁজবে:

```text
customer
order
check
verify
look up
```

বিশেষ করে এমন sentence:

```text
Always check customer details...
```

```text
Verify the customer before...
```

```text
Look up customer information...
```

এগুলো model-এর কাছে unintended tool association তৈরি করতে পারে।

---

# System prompt ছাড়া vs system prompt সহ

এখানে একটা useful experiment করবে।

প্রথমে:

```text
Tools + user query
```

দিয়ে selection test করো।

তারপর:

```text
System prompt + tools + user query
```

দিয়ে test করো।

যদি প্রথমটায় accuracy হয়:

```text
10/10
```

কিন্তু system prompt যোগ করার পর:

```text
8/10
```

হয়ে যায়, তাহলে বুঝবে **system prompt interference করছে।**

---

# শেষ পর্যন্ত exercise-টা কী শেখাচ্ছে?

পুরো exercise-টা আসলে একটা simple chain:

```text
Bad tool descriptions
        ↓
Ambiguity
        ↓
LLM can't clearly distinguish tools
        ↓
Misrouting
        ↓
Improve descriptions
        ↓
Purpose + Inputs + Examples + Edge Cases + Boundaries
        ↓
Clear tool distinction
        ↓
Better routing accuracy
```

আর এর সাথে আরেকটা layer আছে:

```text
System Prompt
      ↓
Can create conflicting instructions
      ↓
Can override / interfere with tool-selection signals
```

## Exam-এর জন্য মূল takeaway

**Tool selection problem দেখলে প্রথমে tool descriptions inspect করো।**

বিশেষ করে দেখো:

* Purpose clear?
* Input format clear?
* Examples আছে?
* Edge cases covered?
* Explicit boundaries আছে?
* অন্য similar tool কখন ব্যবহার করতে হবে সেটা বলা আছে?
* System prompt কি কোনো conflicting keyword/instruction দিচ্ছে?

সবচেয়ে important মনে রাখার মতো line:

> **Good tool descriptions reduce ambiguity and make LLM tool selection more reliable—without requiring architectural changes.**
