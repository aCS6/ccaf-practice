এই exercise-এর মূল উদ্দেশ্য হলো একটা **deprecated function** খুঁজে বের করা, সেটার কোথায় কোথায় usage আছে trace করা, related test files বের করা, তারপর পুরোনো function call-গুলোকে নতুন API দিয়ে replace করা—সবকিছু **built-in tools** ব্যবহার করে এবং অপ্রয়োজনীয়ভাবে পুরো codebase না পড়ে।

এখানে সবচেয়ে important বিষয় হলো **কোন কাজের জন্য কোন tool ব্যবহার করবে** সেটা ঠিক রাখা।

---

# Exercise: Trace and Refactor a Deprecated Function Using Built-in Tools

**Difficulty:** 30 minutes

ধরো তোমার codebase-এ একটা পুরোনো function আছে:

```ts
processLegacyOrder(orderId)
```

এটা deprecated হয়ে গেছে। এখন নতুন API হলো:

```ts
processOrder(orderId, { validate: true })
```

তোমার কাজ হবে:

1. কোথায় কোথায় `processLegacyOrder` ব্যবহার হয়েছে খুঁজে বের করা
2. সেই caller files identify করা
3. caller-দের related test files খুঁজে বের করা
4. প্রয়োজনীয় fileগুলো Read করে context বোঝা
5. পুরোনো call নতুন API দিয়ে replace করা
6. `Edit` failure হলে সঠিকভাবে recover করা

সবচেয়ে গুরুত্বপূর্ণ workflow:

> **Grep → Glob → Read → Edit**

এই sequence-টাই exercise-এর core।

---

# 1. প্রথমে বুঝে নাও: Grep বনাম Glob

এই exercise-এ exam-এর জন্য খুব important distinction আছে।

### Grep

`Grep` ব্যবহার করবে **file-এর ভিতরের content search** করার জন্য।

যেমন:

```text
processLegacyOrder
```

তুমি জানতে চাচ্ছ:

> কোন কোন file-এর ভিতরে `processLegacyOrder` লেখা আছে?

এটা content search, তাই:

**Grep ✅**

---

### Glob

`Glob` ব্যবহার করবে **file path/name matching** করার জন্য।

যেমন:

```text
**/*.test.tsx
```

তুমি জানতে চাচ্ছ:

> কোন কোন file `.test.tsx` দিয়ে শেষ হয়?

এটা file path/name matching, তাই:

**Glob ✅**

---

### Exam shortcut

মনে রাখো:

> **Grep = ভিতরে কী আছে?**
> **Glob = file কোথায়/কী নামে আছে?**

তাই যদি প্রশ্ন হয়:

**"Find all callers of `processLegacyOrder`"**

→ `Grep`

আর যদি বলে:

**"Find all `.test.tsx` files"**

→ `Glob`

---

# 2. Step 1 — Grep দিয়ে সব caller খুঁজবে

প্রথমে পুরো codebase-এর মধ্যে search করবে:

```text
processLegacyOrder
```

এখানে regex-এর দরকার নেই। Literal string search-ই যথেষ্ট।

তুমি এমন result পেতে পারো:

```text
src/OrderProcessor.ts:42: await processLegacyOrder(orderId)
src/RefundHandler.ts:18: const result = processLegacyOrder(orderId)
src/services/OrderService.ts:71: return processLegacyOrder(id)
src/utils/index.ts:12: export { processLegacyOrder } from "./legacy"
```

এখানে শুধু file name পেলেই কাজ শেষ না।

**line number + matching line** দেখো।

কারণ এতে তুমি বুঝতে পারবে function কোথায় actually call হচ্ছে এবং কোথায় শুধু import/re-export/reference আছে।

---

## কেন Glob এখানে ভুল?

ধরো তুমি করেছ:

```text
**/*processLegacyOrder*
```

এতে তুমি filename/path-এর মধ্যে `processLegacyOrder` খুঁজছ।

কিন্তু function call তো filename-এর মধ্যে থাকার কথা না।

Function call থাকে file-এর **content-এর মধ্যে**।

তাই এখানে Glob ব্যবহার করলে তুমি caller খুঁজে পাবে না।

**Exam-এর একটা common trap এটাই।**

---

# 3. Step 2 — Grep-এর result থেকে caller files identify করো

Grep result থেকে এবার actual caller files আলাদা করো।

যেমন:

```text
src/OrderProcessor.ts
src/RefundHandler.ts
src/services/OrderService.ts
```

এগুলোই এখন তোমার relevant files।

এখনও কিন্তু পুরো codebase Read করবে না।

এটাই exercise-এর আরেকটা major lesson।

---

# 4. Incremental codebase discovery

এখানে একটা ভুল approach হলো:

> "আগে পুরো `src/` folder-এর সব file Read করে নিই, তারপর বুঝব কোথায় function ব্যবহার হয়েছে।"

এটা করবে না।

কারণ এতে context unnecessarily অনেক বড় হয়ে যায়।

Exercise চায়:

```text
Grep
  ↓
Relevant files identify
  ↓
Only those files Read
```

অর্থাৎ **incremental discovery**।

প্রতিটা Read-এর একটা justification থাকতে হবে।

Grep বলেছে `OrderProcessor.ts`-এ function আছে → তাই Read করবে।

কোনো file-এর ব্যাপারে কোনো evidence নেই → speculative Read করবে না।

---

# 5. Step 3 — Caller files-এর test files খুঁজবে

এখন ধরো Grep থেকে caller পেয়েছ:

```text
src/OrderProcessor.ts
src/RefundHandler.ts
```

এবার তোমার related test files খুঁজতে হবে।

এখানে আবার **Glob** ব্যবহার করবে।

যেমন:

```text
**/*.test.tsx
```

অথবা যদি caller filename জানা থাকে:

```text
**/OrderProcessor.test.*
```

এতে তুমি পেতে পারো:

```text
src/OrderProcessor.test.tsx
src/RefundHandler.test.tsx
```

---

## কেন এখানে Grep নয়?

কারণ এখন তুমি আর function-এর content খুঁজছ না।

তুমি file-এর **name pattern** খুঁজছ।

যেমন:

```text
*.test.tsx
```

এটা path matching।

তাই:

**Glob ✅**

---

# 6. Grep → Glob pattern

এই exercise-এর একটা খুব important pattern:

```text
Grep → Glob
```

মানে:

### প্রথমে content থেকে বের করো:

> কোথায় function call হয়েছে?

**Grep**

তারপর:

> সেই caller-এর corresponding test file কোনটা?

**Glob**

এটা মাথায় রাখার মতো pattern।

---

# 7. Step 4 — Caller file Read করো

এখন Grep যেসব file-কে caller হিসেবে identify করেছে, শুধু সেগুলো Read করবে।

যেমন:

```text
src/OrderProcessor.ts
```

Read করে দেখবে:

* `processLegacyOrder` কোথায় call হয়েছে
* কী parameter দেওয়া হয়েছে
* return value কীভাবে ব্যবহার হচ্ছে
* function সরাসরি import করা হয়েছে কিনা
* wrapper-এর মাধ্যমে এসেছে কিনা
* কোনো barrel file ব্যবহার হচ্ছে কিনা

যেমন file-এ থাকতে পারে:

```ts
import { processLegacyOrder } from "./utils";

export async function processOrderRequest(orderId: string) {
    const result = await processLegacyOrder(orderId);
    return result;
}
```

এখানে তুমি বুঝতে পারছ:

```text
OrderProcessor.ts
        ↓
./utils
        ↓
processLegacyOrder
```

---

# 8. Wrapper module এবং Barrel file trace করা

এখানেও exercise একটা important scenario দিচ্ছে।

Function সবসময় সরাসরি import নাও হতে পারে।

যেমন:

```ts
import { processLegacyOrder } from "./utils";
```

কিন্তু `./utils/index.ts`-এ থাকতে পারে:

```ts
export { processLegacyOrder } from "./legacy";
```

তারপর:

```text
OrderProcessor.ts
      ↓
utils/index.ts
      ↓
legacy.ts
      ↓
processLegacyOrder
```

এটাকে বলা হচ্ছে **barrel file / re-export chain**।

তাই caller file Read করার সময় import statement-এর দিকে ভালো করে তাকাবে।

যদি দেখো:

```ts
from "./utils"
```

তাহলে প্রয়োজনে `utils/index.ts` trace করবে।

এখানে আবার একই principle:

> আগে evidence → তারপর Read।

অযথা সব module খুলে বসবে না।

---

# 9. Step 5 — Edit দিয়ে deprecated call replace করো

এখন actual modification।

পুরোনো:

```ts
processLegacyOrder(orderId)
```

নতুন:

```ts
processOrder(orderId, { validate: true })
```

এখানে preferred tool হলো:

**Edit**

---

## কেন Edit?

কারণ তুমি ছোট একটা targeted change করতে চাচ্ছ।

`Read + Write` করলে পুরো file context নিয়ে কাজ করতে হয়।

কিন্তু `Edit` সরাসরি নির্দিষ্ট text replace করতে পারে।

তাই:

> **Modification-এর জন্য Edit primary tool।**

Exam-এ এটা explicitly test করা হতে পারে।

---

# 10. Edit-এর `old_string` গুরুত্বপূর্ণ

ধরো তুমি শুধু দিলে:

```text
old_string = processLegacyOrder
```

কিন্তু file-এর মধ্যে function তিন জায়গায় আছে।

তখন Edit বলবে:

```text
old_string matches 3 locations
```

এটা কোনো bug না।

এটা একটা **safety mechanism**।

Tool নিশ্চিত হতে চাইছে:

> "তুমি আসলে কোন occurrence-টা change করতে চাচ্ছ?"

---

# 11. Non-unique match হলে কী করবে?

ধরো প্রথম attempt:

```text
processLegacyOrder
```

দিয়ে Edit করলে error:

```text
old_string matches 3 locations
```

তখন `Read + Write`-এ immediately চলে যাবে না।

প্রথমে **anchor widen** করবে।

মানে `old_string`-এর সঙ্গে surrounding context যোগ করবে।

আগে:

```text
processLegacyOrder
```

তারপর:

```text
await processLegacyOrder(orderId)
```

আরও specific দরকার হলে:

```text
const result = await processLegacyOrder(orderId);
```

অথবা surrounding lines:

```text
export async function processOrderRequest(orderId: string) {
    const result = await processLegacyOrder(orderId);
    return result;
}
```

এখন Edit-এর target unique হয়ে যাবে।

---

# 12. Anchor কী?

সহজভাবে বললে, **anchor** হলো এমন একটা text pattern যেটা target location-টাকে uniquely identify করে।

যেমন শুধু:

```text
processLegacyOrder
```

হয়তো unique না।

কিন্তু:

```text
const result = await processLegacyOrder(orderId);
```

সম্ভবত unique।

আরও context দরকার হলে enclosing function-এর কিছু অংশ যোগ করবে।

---

# 13. `replace_all: true` কখন ব্যবহার করবে?

যদি তুমি নিশ্চিত হও যে file-এর **সব occurrence** পরিবর্তন করতে চাও, তখন:

```text
replace_all: true
```

ব্যবহার করতে পারো।

যেমন file-এ:

```ts
processLegacyOrder(orderId)
processLegacyOrder(orderId2)
processLegacyOrder(orderId3)
```

এবং তিনটাকেই নতুন API-তে migrate করতে হবে।

তাহলে short anchor দিয়ে `replace_all: true` appropriate হতে পারে।

কিন্তু blindly `replace_all` করবে না।

আগে নিশ্চিত হও:

> সব occurrence-ই কি সত্যিই পরিবর্তন করা উচিত?

কারণ global replacement ভুল জায়গাতেও change করতে পারে।

---

# 14. যদি শুধু একটা occurrence change করতে হয়

তাহলে:

```text
replace_all: false
```

অর্থাৎ default targeted Edit ব্যবহার করো এবং unique anchor দাও।

Workflow হবে:

```text
Edit
 ↓
Non-unique match
 ↓
Read surrounding lines
 ↓
Wider anchor
 ↓
Edit again
```

এটাই expected recovery strategy।

---

# 15. Read + Write কেন last resort?

ধরো:

```text
Edit → fails
```

তাহলেই:

```text
Read entire file
→ modify
→ Write entire file
```

করবে না।

কারণ একটা single-line change-এর জন্য পুরো file context নেওয়া unnecessary।

Preferred order:

```text
Edit
   ↓
Widen anchor
   ↓
Edit again
```

অথবা:

```text
Edit
   ↓
replace_all: true
```

যদি genuinely সব occurrence replace করার দরকার হয়।

`Read + Write` হবে **last resort**—যখন Edit দিয়েও target properly disambiguate করা যাচ্ছে না।

---

# পুরো exercise-এর ideal workflow

এখন পুরো ব্যাপারটা একসাথে দেখলে:

```text
1. Grep
   ↓
   Search: processLegacyOrder

2. Caller files identify
   ↓
   OrderProcessor.ts
   RefundHandler.ts
   ...

3. Glob
   ↓
   Find related *.test.tsx files

4. Read
   ↓
   Only Grep-identified caller files
   ↓
   Understand imports, parameters,
   return values, wrappers, barrel files

5. Trace if necessary
   ↓
   Caller → wrapper → barrel → deprecated function

6. Edit
   ↓
   Replace old API with new API

7. If Edit says non-unique
   ↓
   Widen old_string anchor
   ↓
   Edit again

8. If every occurrence should change
   ↓
   replace_all: true

9. Read + Write
   ↓
   Only as a last resort
```

---

# Exam-এর জন্য সবচেয়ে important points

### 1. Function কোথায় ব্যবহৃত হয়েছে?

**Grep**

```text
Grep → content search
```

### 2. Test files কোথায়?

**Glob**

```text
Glob → path/name matching
```

### 3. সব file আগে Read করবে?

**না।**

প্রথমে discovery:

```text
Grep → relevant files → Read
```

এটাই **incremental codebase discovery**।

### 4. Code modify করার primary tool?

**Edit**

`Read + Write` দিয়ে শুরু করবে না।

### 5. Edit বলছে:

```text
old_string matches 3 locations
```

মানে কী?

Target unique না।

তখন:

```text
widen the anchor
```

অথবা সত্যিই সব occurrence বদলাতে হলে:

```text
replace_all: true
```

### 6. Barrel file দেখলে?

Re-export chain trace করবে:

```text
caller
 ↓
barrel
 ↓
actual module
```

### 7. Core pattern?

> **Grep → Glob → Read → Edit**

আর Edit failure-এর ক্ষেত্রে:

> **Edit → widen anchor / replace_all → Edit again**

---

## এক লাইনে exercise-এর আসল শিক্ষা

এই exercise আসলে deprecated function replace করার চেয়ে বেশি কিছু শেখাচ্ছে—**codebase-এ efficiently navigate করা এবং সঠিক কাজের জন্য সঠিক built-in tool বেছে নেওয়া।**

বিশেষ করে এই ৪টা distinction মাথায় রাখো:

```text
Grep  = content খোঁজা
Glob  = file/path খোঁজা
Read  = discovered context বোঝা
Edit  = targeted modification
```

আর **পুরো codebase আগে Read করা যাবে না**—আগে search করে scope ছোট করতে হবে।
