# Build Exercise: Build a Multi-Pass Code Review Pipeline

**Difficulty:** 60 minutes

এই exercise-এ তুমি এমন একটা **code review pipeline** বানাবে যেখানে একই codebase-কে দুইভাবে review করা হবে:

1. **Single-pass review** → সব file একসাথে model-কে দেওয়া
2. **Multi-pass review** → প্রতিটা file আলাদাভাবে review + শেষে সব file নিয়ে একটা `cross-file integration pass`

তারপর দুটোর result compare করবে।

---

# আগে মূল ধারণাটা বুঝে নাও

ধরো তোমার কাছে 14টা file আছে:

```text
file1.ts
file2.ts
file3.ts
...
file14.ts
```

তুমি যদি সবগুলো একসাথে LLM-কে দাও:

```text
Review file1
Review file2
Review file3
...
Review file14
```

তাহলে model শুরুতে `file1`, `file2`, `file3`-এর দিকে অনেক attention দিতে পারে।

কিন্তু যত সামনে যাবে:

```text
file10
file11
file12
file13
file14
```

তত analysis shallow হয়ে যেতে পারে।

এটাই **attention dilution**।

অর্থাৎ:

> Context অনেক বড় হওয়ায় model-এর attention সব জায়গায় সমানভাবে allocate হচ্ছে না।

---

# Exercise-এ কী শিখবে

### 1. Attention dilution

একসাথে অনেক file review করালে:

* প্রথম দিকের file → বেশি detailed analysis
* পরের file → কম detailed analysis
* শেষের file → superficial বা missing feedback

---

### 2. Multi-pass architecture

এর solution হলো পুরো codebase একবারে না দিয়ে কাজটাকে কয়েকটা pass-এ ভাগ করা।

যেমন:

```text
File 1 → Review
File 2 → Review
File 3 → Review
...
File 14 → Review

        ↓

Cross-file Integration Pass
```

এখানে প্রতিটা file তার নিজের পুরো attention budget পায়।

---

### 3. Fixed sequential pipeline বনাম Dynamic adaptive decomposition

এই exercise-এ তুমি মূলত একটা **fixed sequential pipeline** বানাবে।

মানে structure আগে থেকেই নির্ধারিত:

```text
Pass 1 → Per-file analysis
Pass 2 → Cross-file integration
Pass 3 → Comparison
```

অন্যদিকে **dynamic adaptive decomposition** হলে agent নিজে decide করতে পারত:

> "এই codebase-এর এই অংশটা আলাদাভাবে review করা দরকার।"

এই exercise-এর focus dynamic decomposition না; বরং structural multi-pass approach বোঝা।

---

# Step 1 — Code review agent তৈরি করো

প্রথমে এমন একটা code review agent বানাতে হবে যেটা একটা **directory path** নেবে।

Directory-তে কমপক্ষে **10টা source file** থাকতে হবে।

উদাহরণ:

```text
src/
├── user.ts
├── auth.ts
├── payment.ts
├── product.ts
├── order.ts
├── cart.ts
├── api.ts
├── database.ts
├── notification.ts
├── logger.ts
├── utils.ts
└── config.ts
```

TypeScript অথবা JavaScript ব্যবহার করতে পারো।

### কেন 10+ file?

কারণ 10+ file-এর পর থেকেই **attention dilution** observable হতে শুরু করে।

Exercise-এ এমন scale দরকার যেখানে early file আর later file-এর analysis quality compare করা যায়।

### File-গুলোর মধ্যে কী থাকবে?

সব file perfectly clean হলে exercise-এর লাভ কম।

তাই mix রাখবে:

```text
Good code
+
Bugs
+
Repeated patterns
+
Same bug pattern in multiple files
```

বিশেষ করে একটা একই ধরনের pattern একাধিক file-এ রাখবে।

যেমন:

```typescript
items.forEach(item => {
    process(item);
});
```

এই একই pattern কয়েকটা file-এ থাকতে পারে।

এটা পরে consistency test করতে কাজে লাগবে।

---

# Step 2 — Single-pass review implement করো

এখন baseline হিসেবে একটা **single-pass review** বানাবে।

এখানে সবচেয়ে গুরুত্বপূর্ণ বিষয়:

> সব file-এর content একসাথে একটা prompt-এর মধ্যে পাঠাবে।

Conceptually:

```text
You are a code reviewer.

Review the following files:

--- file1.ts ---
<content>

--- file2.ts ---
<content>

--- file3.ts ---
<content>

...

--- file14.ts ---
<content>
```

তারপর model-কে বলবে সব file review করতে।

### কী record করবে?

প্রতিটা file-এর জন্য:

```text
file name
issue count
severity
line reference
description
```

যেমন:

```text
file1.ts
- 3 issues
- High: line 12
- Medium: line 25
- Low: line 40
```

### তুমি কী observe করতে চাও?

সম্ভাব্য result:

```text
file1  → 5 issues, very detailed
file2  → 4 issues, detailed
file3  → 4 issues, detailed

...

file10 → 2 issues, shallow
file11 → 1 issue, shallow
file12 → 0 issues
file13 → 0 issues
file14 → 1 issue, very brief
```

এটাই **attention dilution pattern**।

এখানে একটা গুরুত্বপূর্ণ point:

**Model necessarily খারাপ হয়ে যায়নি।**

Problem হলো architecture।

---

# Step 3 — Per-file local analysis pass

এখন আসল improvement শুরু।

এবার সব file একসাথে পাঠাবে না।

প্রতিটা file individually review করবে।

মানে:

```text
file1 → LLM → result
file2 → LLM → result
file3 → LLM → result
...
file14 → LLM → result
```

প্রতিটা call-এ একই review prompt থাকবে।

যেমন:

```text
Review this TypeScript file.

Find:
- bugs
- security issues
- performance issues
- bad patterns

Return:
- bug count
- severity
- line number
- description
```

তারপর result structured format-এ collect করবে।

যেমন:

```text
{
    "file": "payment.ts",
    "issues": [
        {
            "line": 23,
            "severity": "HIGH",
            "description": "..."
        },
        {
            "line": 45,
            "severity": "MEDIUM",
            "description": "..."
        }
    ]
}
```

### এখানে কী improvement হবে?

আগের ক্ষেত্রে:

```text
14 files → one attention budget
```

এখন:

```text
file1  → full attention
file2  → full attention
file3  → full attention
...
file14 → full attention
```

তাই `file14` আর "শেষের file" হিসেবে disadvantage-এ থাকবে না।

এটাই **per-file local analysis pass**।

---

# Step 4 — Cross-file integration pass

এটা খুব গুরুত্বপূর্ণ।

অনেকে এখানে ভুল করে ভাবে:

> "প্রতিটা file আলাদাভাবে review করেছি, কাজ শেষ।"

না।

Per-file analysis local problem ধরতে পারে, কিন্তু **cross-file problem** ধরতে পারে না।

উদাহরণ:

```text
auth.ts
    ↓
user.ts
    ↓
payment.ts
```

ধরো `auth.ts` একটা value return করছে:

```text
user_id
```

কিন্তু `payment.ts` expect করছে:

```text
userId
```

প্রতিটা file individually দেখলে দুইটাকেই valid মনে হতে পারে।

কিন্তু একসাথে relationship দেখলে বোঝা যাবে:

```text
auth.ts → user_id
payment.ts → userId
```

অর্থাৎ data flow problem।

---

## তাই আলাদা Cross-file Integration Pass লাগবে

এবার model-কে সব raw file আবার পাঠানোর দরকার নেই।

আগের pass-এর **summaries** পাঠাবে।

সাথে file structure / imports / relationships-এর information দিতে পারো।

Conceptually:

```text
File summaries:

auth.ts
- exports authenticateUser()
- returns user_id

user.ts
- imports authenticateUser()

payment.ts
- expects userId

...

Now analyze cross-file concerns.
```

Model-কে specifically বলবে check করতে:

### 1. Data flow

```text
File A → File B → File C
```

Data ঠিকভাবে flow করছে কিনা।

### 2. API consistency

এক file-এ API যেভাবে ব্যবহার করা হচ্ছে অন্য file-এ একইভাবে করা হচ্ছে কিনা।

### 3. Import chains

Imports-এর মধ্যে কোনো broken বা problematic dependency আছে কিনা।

### 4. Pattern usage consistency

একই pattern এক file-এ একটা way-তে এবং অন্য file-এ অন্যভাবে ব্যবহার করা হয়েছে কিনা।

---

# Step 5 — Single-pass বনাম Multi-pass compare করো

এখন দুইটা result তোমার কাছে থাকবে:

```text
Single-pass results
        VS
Multi-pass results
```

প্রতিটা file-এর issue count compare করবে।

উদাহরণ:

| File      | Single-pass | Multi-pass |
| --------- | ----------: | ---------: |
| file1.ts  |           5 |          5 |
| file2.ts  |           4 |          5 |
| file3.ts  |           4 |          4 |
| file4.ts  |           3 |          5 |
| file5.ts  |           3 |          4 |
| file10.ts |           1 |          4 |
| file11.ts |           0 |          3 |
| file12.ts |           0 |          4 |
| file13.ts |           1 |          3 |
| file14.ts |           0 |          4 |

এখানে patternটা clear:

**Single-pass:**

```text
Early files
████████████
██████████

Later files
████
██
```

**Multi-pass:**

```text
File 1   ███████
File 2   ███████
File 3   ██████
...
File 14  ███████
```

Multi-pass-এ analysis depth বেশি consistent।

---

## Standard deviation কেন calculate করতে বলেছে?

Exercise-এ বলা হয়েছে issue count-এর **standard deviation** calculate করতে।

কারণ:

> Standard deviation কম = file-to-file analysis বেশি consistent।

ধরো:

### Single-pass

```text
5, 5, 4, 3, 2, 2, 1, 0, 0, 1
```

অনেক variation।

### Multi-pass

```text
4, 5, 4, 4, 5, 3, 4, 4, 5, 4
```

Values কাছাকাছি।

তাই দ্বিতীয়টার standard deviation কম হবে।

genui{"learning_viz":{"type_id":"STANDARD_DEVIATION","locale_override":"bn-BD"}}

Exercise-এর argument হচ্ছে:

```text
Lower standard deviation
        ↓
More consistent analysis
        ↓
Less attention dilution
```

---

# Step 6 — Attention dilution artefacts খুঁজে বের করো

এটা exercise-এর সবচেয়ে interesting অংশ।

ধরো একই code pattern দুই জায়গায় আছে।

### file3.ts

```typescript
users.forEach(user => {
    sendEmail(user);
});
```

Model বলল:

```text
⚠️ Potential performance issue
```

কিন্তু `file11.ts`-এ exact/similar pattern:

```typescript
users.forEach(user => {
    sendEmail(user);
});
```

Model বলল:

```text
No issues found.
```

এটা হলো:

**attention dilution artefact**

কারণ একই ধরনের pattern-কে model দুইভাবে evaluate করেছে।

---

# কেন এটা গুরুত্বপূর্ণ?

এখানে problemটা শুধু:

> "একটা bug miss করেছে"

এটা নয়।

আরও গুরুত্বপূর্ণ হলো:

> **একই pattern-এর জন্য inconsistent judgment দিয়েছে।**

যেমন:

```text
File 3
forEach → flagged

File 11
forEach → approved
```

এটা evidence যে attention allocation consistent ছিল না।

---

# Multi-pass এখানে কী করবে?

Per-file analysis-এ:

```text
file3 → pattern detected
file11 → same pattern detected
```

দুই file-ই আলাদাভাবে full attention পেয়েছে।

তারপর `cross-file integration pass` চাইলে আরও বলতে পারে:

```text
The same pattern appears in file3 and file11.
Are they being used consistently?
```

তখন inconsistency detect করা সহজ হয়।

---

# পুরো Architecture একসাথে

Exercise-টার final architecture মোটামুটি এমন:

```text
                 Codebase
                    │
                    ▼
             ┌─────────────┐
             │ Single Pass │
             └──────┬──────┘
                    │
                    ▼
            Single-pass Results
                    │
                    │
                    │ compare
                    │
                    ▼
┌─────────────────────────────────────┐
│          Multi-pass Pipeline        │
│                                     │
│  file1 ──→ Local Analysis           │
│  file2 ──→ Local Analysis           │
│  file3 ──→ Local Analysis           │
│   ...                               │
│  file14 ─→ Local Analysis           │
│                                     │
│             ↓                       │
│                                     │
│     Cross-file Integration Pass     │
│                                     │
└──────────────────┬──────────────────┘
                   │
                   ▼
             Multi-pass Results
                   │
                   ▼
             Compare Results
                   │
                   ▼
       Find Attention Dilution
             Artefacts
```

---

# Exercise শেষে তোমার কাছে কী থাকা উচিত?

শেষে ideally তোমার কাছে থাকবে:

### 1. Source directory

```text
10–15 TypeScript/JavaScript files
```

যেখানে থাকবে:

* good code
* bugs
* repeated patterns
* একই bug/pattern multiple files-এ

---

### 2. Single-pass reviewer

```text
all files
   ↓
one prompt
   ↓
one review
```

---

### 3. Per-file reviewer

```text
file1 → review
file2 → review
...
file14 → review
```

প্রতিটা structured output দেবে:

```text
file
issues[]
  ├── line
  ├── severity
  └── description
```

---

### 4. Cross-file integration reviewer

এটা check করবে:

```text
Data flow
API consistency
Import chains
Pattern consistency
```

---

### 5. Comparison

প্রতিটা file-এর জন্য:

```text
single-pass issue count
vs
multi-pass issue count
```

এবং calculate করবে:

```text
standard deviation
```

---

### 6. Attention dilution artefacts

কমপক্ষে একটা case document করবে যেখানে:

```text
Same pattern

File A → flagged
File B → approved/ignored
```

এবং দেখাবে যে:

```text
Single-pass → inconsistent

Multi-pass → consistent
```

---

# একদম সহজ ভাষায় Exercise-টার মূল শিক্ষা

এখানে **prompt engineering** মূল solution না।

ধরো তুমি single-pass prompt-টা আরও সুন্দর করলে:

```text
"Please carefully review EVERY file..."
```

তবুও structural attention problem পুরোপুরি solve হবে না।

আর context window বড় করলেও একই সমস্যা থাকতে পারে।

মূল solution হলো **architecture change করা**:

```text
❌ All files → One giant review

        ↓

✅ Each file → Local review
        +
   All summaries → Cross-file review
```

অর্থাৎ:

> **Attention dilution is an architectural problem, not simply a prompting problem.**

আর একটা খুব important distinction:

```text
Per-file pass
    ↓
Local issues
```

কিন্তু:

```text
Cross-file integration pass
    ↓
Relationships between files
```

তাই শুধু batching/per-file review করলেই complete solution হয় না।

**Final mental model:**

```text
Single-pass
= সবকিছু একসাথে
= attention dilution risk

Multi-pass
= local analysis
  +
  cross-file integration
= better + more consistent review
```

এই exercise-এর আসল লক্ষ্য হলো **"LLM-কে আরও ভালোভাবে prompt করো"** নয়; বরং **"কাজের structure এমনভাবে ভাঙো যাতে model-এর attention reliably allocate হয়"**—এই architectural thinkingটা বোঝা।
