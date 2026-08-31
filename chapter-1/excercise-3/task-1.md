# Structured Metadata দিয়ে Context Passing ইমপ্লিমেন্ট করুন

**সময়:** ৫০ মিনিট

---

### এই এক্সারসাইজে যা যা শিখবেন:
- কেন `coordinator`-এর `allowed_tools`-এ `subagents` spawn করার জন্য `Task` (বা এর বর্তমান নাম `Agent`) ইনক্লুড করতেই হবে।
- কীভাবে এমন `structured metadata` ডিজাইন করবেন যা `content`-কে `source attribution` থেকে আলাদা রাখে।
- কেন `context passing` ফেইল করলে `downstream agents`-এ `attribution errors` তৈরি হয়।
- `latency` কমানোর জন্য `independent subagents`-দের কীভাবে `parallel`-এ spawn করবেন।
- `fork_session` আর `parallel Task tool invocation`-এর মধ্যে আসল পার্থক্য কী।

---

### ধাপ ১: `allowed_tools`-এ `Task` (বা `Agent`) রেখে একটা `coordinator agent` বানান
একটা `coordinator agent` তৈরি করুন যার `allowed_tools`-এ `Task` বা `Agent` থাকে।

- **কেন:** `Task` হলো `subagent` spawn করার হার্ড গেট (বর্তমান Claude Code v2.1.63-এ এর নাম `Agent` হয়েছে; তবে `Task` এখনো alias হিসেবে কাজ করে)। `allowed_tools`-এ এটা না থাকলে `coordinator` কোনো `subagent` ইনভোক করতেই পারবে না। এক্সামে এটা একদম বাইনারি রিকোয়ারমেন্ট হিসেবে টেস্ট হয় — এটা অপশনাল না, রানটাইমে কনফিগার করাও যায় না।
- **আপনি যা দেখতে পাবেন:** একটা `query()` কল যার অপশনসে `allowed_tools`-এ এক্সপ্লিসিটলি `Agent` (বা `Task`) থাকবে, সাথে `coordinator`-এর অন্য প্রয়োজনীয় টুলস থাকবে, এবং `options.agents`-এর নিচে `subagent` ডেফিনিশনগুলো থাকবে।
- 💡 **Nudge (ইঙ্গিত):** ভাবুন তো, `allowed_tools` থেকে যদি `Task` (বা `Agent`) বাদ দেন কী হবে? `coordinator` কোনোভাবেই `subagents` spawn করতে পারবে না — কোনো ফলব্যাক নেই।

---

### ধাপ ২: দুটো `subagent` ডিফাইন করুন
দুটো `subagent` ডিফাইন করুন: একটা `web search agent` (যা `source URLs` আর `titles` সহ রেজাল্ট দেয়) আর একটা `document analysis agent` (যা `page references` সহ অ্যানালাইসিস দেয়)।

- **কেন:** প্রতিটা `subagent`-এর নিজের রোল অনুযায়ী স্কোপড টুল অ্যাক্সেস দরকার। এক্সামে চেক করা হয় আপনি `subagents`-কে সঠিক `AgentDefinition` ফিল্ডস সহ ডিফাইন করেছেন কিনা: `description`, `system prompt`, আর `tool restrictions`।
- **আপনি যা দেখতে পাবেন:** দুটো `AgentDefinition` অবজেক্ট, যার প্রতিটাতে `description`, `system prompt`, আর রেস্ট্রিক্টেড টুল সেট আছে। `web search agent`-এ শুধু সার্চ টুলস; `document analysis agent`-এ শুধু ফাইল রিডিং টুলস।
- 💡 **Nudge:** একটা `AgentDefinition` মূলত কোন তিনটা জিনিস স্পেসিফাই করে? ভাবুন তো `coordinator` এই প্রতিটা ফিল্ড কীভাবে ব্যবহার করে।

---

### ধাপ ৩: `content` আর `metadata` আলাদা করে একটা `structured output format` ডিজাইন করুন
এমন একটা `structured output format` ডিজাইন করুন যা `content` আর `metadata` আলাদা করে: প্রতিটা `finding`-এ `claim`, `source_url`, `document_name`, `page_number`, আর `confidence` ইনক্লুড থাকবে।

- **কেন:** এক্সামে স্পেসিফিকলি `attribution failure pattern` টেস্ট করা হয়: যখন একটা `synthesis agent` আনসোর্সড ক্লেম (unsourced claims) প্রোডিউস করে, তখন মূল কারণ হলো `coordinator` `structured metadata` ছাড়া শুধু `content` পাস করেছে। `content` আর `metadata` আলাদা করাই হলো এর সমাধান।
- **আপনি যা দেখতে পাবেন:** একটা TypeScript interface বা JSON schema যা `Finding` টাইপ ডিফাইন করে, যেখানে `content` ফিল্ডস (`claim`, `analysis`) আর `metadata` ফিল্ডস (`source_url`, `document_name`, `page_number`, `confidence`, `retrieved_by`) দুটোই থাকে।
- 💡 **Nudge:** একটা প্রপারলি সাইটেড (properly cited) রিপোর্ট বানানোর জন্য `synthesis agent`-এর কোন ফিল্ডগুলো দরকার? ফুল `attribution`-এর জন্য কী কী লাগবে ভাবুন।

---

### ধাপ ৪: সব `metadata` অক্ষুণ্ণ রেখে `synthesis subagent`-এর কাছে সম্পূর্ণ রেজাল্ট পাস করুন
দুটো `subagent`-এর সম্পূর্ণ `structured results` একটা `synthesis subagent`-এর কাছে পাস করুন, সব `metadata` ইন্ট্যাক্ট (preserve) রেখে।

- **কেন:** এটাই সেই ক্রিটিকাল স্টেপ যাকে এক্সাম টার্গেট করে। `synthesis agent`-এ পাস করার আগে `metadata` স্ট্রিপ (strip) করে ফেলাই হলো `attribution failures`-এর মূল কারণ। `coordinator`-কে শুধু ক্লেম টেক্সট না দিয়ে ফুল `structured output` পাস করতে হবে।
- **আপনি যা দেখতে পাবেন:** `coordinator` সম্পূর্ণ `findings array` (সব `metadata` ইন্ট্যাক্ট রাখা অবস্থায়) `synthesis agent`-এর প্রম্পটে পাস করে। কোনো `metadata` ফিল্ড স্ট্রিপ বা সামারাইজ করা হয় না।

---

### ধাপ ৫: ভেরিফাই করুন যে `synthesis agent` প্রতিটা ক্লেম সাইট করতে পারছে
ভেরিফাই করুন যে `synthesis agent` তার আউটপুটের প্রতিটা `claim`-কে একটা স্পেসিফিক `source`-এর (URL আর page number সহ) সাথে অ্যাট্রিবিউট করতে পারছে কিনা।

- **কেন:** এই ভেরিফিকেশন স্টেপ কনফার্ম করে যে `context passing` ঠিকমতো কাজ করেছে। যদি কোনো `claim`-এ `attribution` না থাকে, তাহলে ব্যাক ট্রেস করুন `metadata` আসলে পাস হয়েছিল কিনা দেখতে — সরাসরি `synthesis agent`-এর প্রম্পটকে দোষ দেবেন না।
- **আপনি যা দেখতে পাবেন:** একটা `synthesis report` যেখানে প্রতিটা ফ্যাকচুয়াল ক্লেম-এ `source URL` আর `page number` সহ সাইটেশন থাকে। কোনো অরফান ক্লেম (orphaned claims) বা আনঅ্যাট্রিবিউটেড ক্লেম থাকা যাবে না।
- 💡 **Nudge:** প্রোগ্রামাটিকালি কীভাবে ভেরিফাই করবেন যে প্রতিটা ক্লেম-এ সাইটেশন আছে? আউটপুটে কোনো প্যাটার্ন খোঁজার চেষ্টা করুন।

---

### ধাপ ৬: `coordinator`-কে রিফ্যাক্টর করে `parallel`-এ `subagents` spawn করান
`coordinator`-কে রিফ্যাক্টর করুন যাতে সে একটা সিঙ্গেল রেসপন্সে একাধিক `Task tool calls` ব্যবহার করে দুটো `research subagents`-কে `parallel`-এ spawn করে।

- **কেন:** এক্সামে `latency awareness` টেস্ট করা হয়। `independent subagents`-দের সিকোয়েন্সিয়ালি (একের পর এক) spawn করলে টাইম নষ্ট হয়। ইন্ডিপেন্ডেন্ট টাস্কগুলোর জন্য সঠিক প্যাটার্ন হলো একটা `coordinator response`-এ একাধিক `Task tool calls`-এর মাধ্যমে `parallel spawning`।
- **আপনি যা দেখতে পাবেন:** `web search` আর `document analysis` — দুটো `subagent`-ই `parallel Task tool calls`-এর মাধ্যমে একসাথে ইনভোক হচ্ছে, আর `coordinator` সিন্থেসিসে (synthesis) যাওয়ার আগে দুটোই শেষ হওয়ার জন্য ওয়েট করছে।
- 💡 **Nudge:** এই দুটো টাস্ক কেন `parallel execution`-এর জন্য উপযুক্ত? এরা তো ইন্ডিপেন্ডেন্ট — কোনো একটার রেজাল্ট অন্যটার দরকার হয় না।