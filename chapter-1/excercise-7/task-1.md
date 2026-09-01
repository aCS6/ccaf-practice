# Build Exercise: Implement Session Management Strategies

**Difficulty:** 45 minutes

এই exercise-এ তুমি মূলত ৩টা session management strategy হাতে-কলমে দেখবে:

1. **`resume`** → আগের session যেখানে শেষ হয়েছিল, সেখান থেকেই continue করা
2. **`fork_session`** → existing session-এর knowledge নিয়ে আলাদা/different exploration করা
3. **Fresh start + summary injection** → নতুন session শুরু করে আগের findings-এর structured summary prompt-এর মধ্যে দেওয়া

সবচেয়ে important lesson:

> **Files unchanged থাকলে `resume` ভালো। কিন্তু files পরিবর্তন হয়ে গেলে পুরোনো session-এর context stale হয়ে যেতে পারে। তখন fresh session + summary injection বেশি reliable।**

---

# 1. প্রথমে একটি named Claude Code session তৈরি করা

প্রথম কাজ হলো Claude Code দিয়ে একটি **10-file codebase analyse** করা এবং session-টির একটি নাম দেওয়া।

এখানে `--name` বা `-n` flag ব্যবহার করবে।

উদাহরণ:

```bash
claude --name codebase-review
```

তারপর Claude Code-কে বলবে:

> Analyse all 10 source files in the codebase directory and identify issues, severity, and recommendations.

### কেন এটা করতে হবে?

কারণ session-টাকে একটি নাম দিলে পরে সেটাকে সহজে আবার **`--resume`** করা যায়।

যেমন:

```bash
claude --resume codebase-review
```

এখানে exam-এর জন্য গুরুত্বপূর্ণ distinction:

* **Files change হয়নি** → `--resume` করা reasonable
* **Files change হয়েছে** → `--resume` করলে stale context problem হতে পারে

### কী দেখতে পাবে?

একটি named Claude Code session থাকবে যেটা:

* 10টি source file পড়েছে
* প্রতিটি file analyse করেছে
* findings তৈরি করেছে
* recommendations দিয়েছে

---

## Nudge-এর মানে

> How do you give a Claude Code session a name you can resume by later? Which flag sets it at start-up?

সহজ উত্তর:

**Startup-এর সময় `--name` বা `-n` ব্যবহার করবে।**

তারপর একই নাম দিয়ে:

```bash
claude --resume <session-name>
```

---

# 2. Initial analysis-এর findings-এর একটি structured summary তৈরি করা

এখন প্রথম session-এর analysis থেকে important findings আলাদা করে একটি **structured summary** তৈরি করবে।

ধরো:

```markdown
# Codebase Analysis Summary

## auth.ts
- Issue: SQL injection vulnerability
- Severity: Critical
- Recommendation: Use parameterized queries

## database.ts
- Issue: Database connections are not properly cleaned up
- Severity: High
- Recommendation: Add connection cleanup

## api-routes.ts
- Issue: No rate limiting
- Severity: High
- Recommendation: Add rate limiting

...
```

অথবা JSON:

```json
{
  "auth.ts": {
    "issues": [
      {
        "description": "SQL injection vulnerability",
        "severity": "Critical"
      }
    ],
    "recommendations": [
      "Use parameterized queries"
    ]
  }
}
```

### কেন summary দরকার?

এটাই পরবর্তীতে **fresh session-এর knowledge** হিসেবে ব্যবহার করবে।

এখানে একটা খুব important concept আছে:

### Summary ≠ raw tool output

তুমি fresh session-কে পুরো পুরোনো tool output বা পুরোনো file contents দেবে না।

বরং দেবে:

* কোন file-এ কী issue ছিল
* severity কী
* কী recommendation দেওয়া হয়েছিল

অর্থাৎ **conclusions preserve করবে, raw context নয়।**

---

# 3. তিনটি file modify করা

এখন initial analysis থেকে critical issue থাকা ৩টি file ঠিক করবে।

Exercise-এর guidance অনুযায়ী:

### `auth.ts`

SQL injection fix করবে।

### `database.ts`

Connection cleanup যোগ করবে।

### `api-routes.ts`

Rate limiting যোগ করবে।

অর্থাৎ initial analysis-এর পরে codebase এখন **আগের অবস্থায় নেই**।

এটাই exercise-এর সবচেয়ে গুরুত্বপূর্ণ setup।

---

# কেন file পরিবর্তন করা হলো?

কারণ এখন একটা interesting situation তৈরি হয়েছে।

পুরোনো session-এর history-তে Claude দেখেছে:

```text
auth.ts → SQL injection exists
```

কিন্তু actual file এখন:

```text
auth.ts → SQL injection fixed
```

অর্থাৎ:

```text
Old session context
        ↓
SQL injection exists

Actual current file
        ↓
SQL injection fixed
```

এই দুইটা information conflict করতে পারে।

এটাই **stale context problem**।

---

# 4. এবার `--resume` করে stale context observe করা

এখন পুরোনো session-এ ফিরে যাবে:

```bash
claude --resume codebase-review
```

তারপর জিজ্ঞেস করবে:

> What is the current state of auth.ts? Are there still security issues?

এখন observe করবে Claude কী বলে।

সমস্যা হতে পারে:

* Claude পুরোনো SQL injection-এর কথা বলছে
* অথচ তুমি সেটা ইতিমধ্যে fix করেছ
* পুরোনো code reference করছে
* নতুন code-এর সঙ্গে পুরোনো findings মিশিয়ে ফেলছে
* already-fixed issue আবার fix করতে বলছে

এটাই **stale context**।

---

## Stale context আসলে কী?

সহজভাবে:

> Session history-তে থাকা পুরোনো information আর বর্তমান filesystem-এর information এক না হলে stale context তৈরি হয়।

ধরো প্রথম session-এ:

```text
auth.ts

query = "SELECT * FROM users WHERE id = " + userId
```

Claude বলল:

> SQL injection vulnerability আছে।

পরে তুমি fix করলে:

```text
query = "SELECT * FROM users WHERE id = ?"
```

কিন্তু resumed session-এর history-তে এখনও পুরোনো tool result আছে।

তাই Claude-এর কাছে simultaneously দুই ধরনের information থাকতে পারে:

```text
Old tool result:
SQL injection exists

Current file:
SQL injection fixed
```

ফলে contradictory advice আসতে পারে।

---

# 5. Fresh session + structured summary injection

এখন সঠিক approach ব্যবহার করবে।

**পুরোনো session resume করবে না।**

বরং একদম নতুন session শুরু করবে।

কিন্তু সমস্যা হলো:

> নতুন session তো আগের analysis জানে না।

এখানেই **structured summary injection** ব্যবহার হবে।

তুমি নতুন session-এর initial prompt-এর মধ্যে আগের summary inject করবে।

Conceptually:

```text
Here is the previous analysis summary:

[structured summary]

Three files have changed:
- auth.ts
- database.ts
- api-routes.ts

Re-analyse only these three files based on their current contents.
Use the previous summary as historical findings, but treat the current files as authoritative.
```

এখানে নতুন session:

* পুরোনো findings জানে
* কিন্তু পুরোনো raw tool results carry করছে না
* current files নতুন করে পড়ে
* শুধু changed files re-analyse করে

---

# 6. কেন শুধু 3টা file re-analyse?

এটাই **targeted re-analysis**।

ধরো 10টা file ছিল:

```text
1. auth.ts          ← changed
2. database.ts      ← changed
3. api-routes.ts    ← changed
4. users.ts         ← unchanged
5. config.ts        ← unchanged
6. models.ts        ← unchanged
7. logger.ts        ← unchanged
8. utils.ts         ← unchanged
9. cache.ts         ← unchanged
10. server.ts       ← unchanged
```

সব 10টা আবার analyse করার দরকার নেই।

কারণ:

```text
3 files changed
7 files unchanged
```

তাই:

```text
Previous findings
       +
Current analysis of changed files
       ↓
Updated understanding
```

এটা অনেক বেশি efficient।

---

# 7. `resume` বনাম Fresh Start

এটা exercise-এর সবচেয়ে exam-relevant অংশ।

| Situation                                          | Best approach                   |
| -------------------------------------------------- | ------------------------------- |
| Files unchanged                                    | `resume`                        |
| Files changed                                      | Fresh start + summary injection |
| Previous work continue করতে হবে                    | `resume`                        |
| Code পরিবর্তনের পর accurate current analysis দরকার | Fresh session                   |
| Previous knowledge রাখতে হবে                       | Structured summary injection    |
| কয়েকটি file পরিবর্তন হয়েছে                         | Targeted re-analysis            |
| Completely different exploration দরকার             | `fork_session`                  |

---

# 8. `fork_session` কোথায় আসে?

`fork_session` আর `resume` এক জিনিস না।

### `resume`

মানে:

> "আমি আগের কাজটাই continue করতে চাই।"

ধরো:

```text
Session A
   ↓
Analysis
   ↓
Break
   ↓
resume
   ↓
Continue same work
```

---

### `fork_session`

মানে:

> "আগের session-এর context/knowledge থেকে একটা আলাদা exploration branch তৈরি করতে চাই।"

Conceptually:

```text
             Session A
                |
        -----------------
        |               |
     Continue         Fork
        |               |
    Same direction   New direction
```

অর্থাৎ `fork_session` useful যখন তুমি **divergent exploration** করতে চাও।

আর `resume` হলো **continuation**।

---

# 9. শেষ ধাপে দুই session-এর output compare করবে

এখন তোমার কাছে দুটি result থাকবে।

### Resumed session

সম্ভবত:

```text
auth.ts still has SQL injection
```

অথবা:

```text
You should fix the SQL injection
```

যদিও তুমি already fix করে ফেলেছ।

### Fresh session

Current `auth.ts` দেখে বলবে:

```text
The SQL injection issue identified previously
has been fixed. The current implementation uses
parameterized queries.
```

অর্থাৎ current code-এর সঙ্গে consistent।

---

# কী কী compare করবে?

Exercise তোমাকে চারটা জিনিস specifically document করতে বলছে।

### 1. Resume session কি old code reference করেছে?

যেমন:

> SQL injection এখনও আছে

যদিও সেটা fix করা হয়েছে।

---

### 2. Already-applied fixes আবার recommend করেছে?

যেমন:

> Add parameterized queries.

কিন্তু তুমি already সেটা করে ফেলেছ।

---

### 3. Fresh session কি current state correctly identify করেছে?

অর্থাৎ:

> SQL injection fixed.

এবং বর্তমান code দেখে analysis করেছে।

---

### 4. Targeted re-analysis কি unnecessary কাজ কমিয়েছে?

10টা file আবার analyse না করে:

```text
auth.ts
database.ts
api-routes.ts
```

এই 3টা file-ই analyse করেছে।

---

# পুরো Exercise-এর flow এক নজরে

```text
10-file codebase
       │
       ▼
Create named session
(--name)
       │
       ▼
Analyse all 10 files
       │
       ▼
Create structured summary
(file + issue + severity + recommendation)
       │
       ▼
Modify 3 files
       │
       ▼
Old session now contains stale tool results
       │
       ▼
--resume
       │
       ▼
Observe stale / contradictory advice
       │
       │
       ▼
Start NEW session
       │
       ▼
Inject structured summary
       │
       ▼
Tell it which 3 files changed
       │
       ▼
Targeted re-analysis
       │
       ▼
Accurate + consistent result
```

---

# সবচেয়ে important takeaway

এই exercise আসলে একটা rule শেখাচ্ছে:

> **`resume` = continuation, not automatic synchronization with changed files.**

যদি files **unchanged** থাকে:

```text
resume
```

ভালো choice।

কিন্তু files **changed** হলে:

```text
Fresh session
    +
Structured summary injection
    +
Targeted re-analysis
```

হলো safer এবং more efficient approach।

আর মনে রাখবে:

```text
resume
→ continuation

fork_session
→ divergent exploration

fresh + summary
→ preserve knowledge without preserving stale tool results
```

এই distinction-টাই exercise-এর core concept।
