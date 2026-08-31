# Build a Multi-Tool Agent Loop

**সময়:** ৪৫ মিনিট

---

### এই এক্সারসাইজে যা যা শিখবেন:
- `Messages API`-এর সাথে `agentic loop lifecycle` ঠিক কীভাবে কাজ করে।
- কেন `stop_reason` হলো `loop control`-এর জন্য একদম নির্ভরযোগ্য (authoritative) signal।
- `tool_use` এবং `end_turn` `stop_reason` ভ্যালুগুলো কীভাবে সঠিকভাবে handle করতে হয়।
- `Multi-turn execution`-এর জন্য `conversation history`-তে `tool results` কীভাবে `append` করতে হয়।
- কখন `safety iteration caps` stopping mechanism হিসেবে ঠিক আছে, আর কখন এটা ব্যবহার করা একদমই উচিত নয়।

---

### ধাপ ১: দুটি tool সহ Claude API client সেটআপ করুন
একটা `calculator tool` (যা `expression` নেয় আর `result` রিটার্ন করে) এবং একটা `web search stub` (যা `query` নেয় আর `mock results` রিটার্ন করে) সেটআপ করুন।

- **কেন:** `Multi-tool setups` মডেলের decision-making প্রসেসটা সামনে নিয়ে আসে। Claude-কে কনটেক্সট বুঝে সঠিক tool select করতে হয়, যা `agentic architecture`-এর মূল জিনিস।
- **আপনি যা দেখতে পাবেন:** সঠিক JSON Schema `input_schema` সহ দুটি tool definition registered থাকবে, যেখানে প্রতিটির `name`, `description`, এবং `parameters` থাকবে।
- 💡 **Nudge (ইঙ্গিত):** ভাবুন তো, Anthropic SDK একটা tool definition-এর জন্য ঠিক কী কী চায় — `name`, `description`, আর কোন ধরনের schema format?

---

### ধাপ ২: Agentic loop ইমপ্লিমেন্ট করুন
এমন একটা `agentic loop` বানান যা Claude-কে request পাঠায় এবং প্রতিটি response-এর পর `stop_reason` চেক করে।

- **কেন:** `Agentic loop` হলো একদম core execution pattern। এক্সামে দেখা হবে আপনি কি `stop_reason` (যা deterministic) ব্যবহার করছেন, নাকি content-type check বা natural language parsing (যা unreliable) ব্যবহার করছেন।
- **আপনি যা দেখতে পাবেন:** একটা `while` loop যা `client.messages.create()` কল করে এবং প্রতিটি iteration-এর পর `response.stop_reason` চেক করে।
- 💡 **Nudge:** API response-এর কোন field আপনাকে একদম ক্লিয়ারলি বলে দেয় যে Claude আরও চালিয়ে যেতে চায়, নাকি সে কাজ শেষ করে দিয়েছে?

---

### ধাপ ৩: `tool_use` stop_reason হ্যান্ডেল করুন
`tool_use` `stop_reason` পেলে requested tool টা execute করুন, একটা `tool result` message বানান, এবং সেটা `conversation history`-তে `append` করে দিন।

- **কেন:** এটা হলো loop-এর সবচেয়ে গুরুত্বপূর্ণ handoff। এক্সামে স্পেসিফিকলি চেক করা হবে আপনি tool calls ঠিকমতো extract করতে পারছেন কিনা, সেগুলো run করতে পারছেন কিনা, এবং সঠিক message format-এ result রিটার্ন করতে পারছেন কিনা।
- **আপনি যা দেখতে পাবেন:** যখন Claude একটা tool request করবে, আপনার কোড `tool_use` block টা extract করবে, ম্যাচিং function টা run করবে, এবং assistant response আর `tool_result` সহ একটা user message — দুটোই conversation-এ append করবে।
- 💡 **Nudge:** Claude response-এ content blocks থাকে। কোন block type আপনাকে বলে দেয় কোন tool-টা call করতে হবে আর কী input দিতে হবে?

---

### ধাপ ৪: `end_turn` stop_reason হ্যান্ডেল করুন
`end_turn` `stop_reason` পেলে final response টা extract করে রিটার্ন করে দিন।

- **কেন:** `end_turn` হলো Claude-এর সিগন্যাল যে সে তার কাজ শেষ করে ফেলেছে। final text response ঠিকমতো extract করলে loop বন্ধ হয় এবং result ইউজারের কাছে চলে যায়।
- **আপনি যা দেখতে পাবেন:** যখন `stop_reason` হবে `end_turn`, তখন আপনার loop বেরিয়ে আসবে (exit করবে) এবং final response থেকে text content টা রিটার্ন করবে।
- 💡 **Nudge:** response object-এর ঠিক কোন জায়গায় সেই final text টা থাকে যা Claude ইউজারকে দেখাতে চায়?

---

### ধাপ ৫: একাধিক sequential tool calls দিয়ে টেস্ট করুন
এমন একটা prompt দিয়ে টেস্ট করুন যেখানে একাধিক `sequential tool calls` দরকার (যেমন: প্রথমে একটা value search করুন, তারপর সেটা দিয়ে কিছু calculate করুন)। দেখুন loop সব iteration জুড়ে ঠিকমতো কাজ করছে কিনা।

- **কেন:** `Sequential tool calls` পুরো loop lifecycle টা টেস্ট করে। agent-কে প্রথমে একটা tool call শেষ করতে হবে, result পেতে হবে, সেটা নিয়ে ভাবতে (reason) হবে, এবং শেষে উত্তর দেওয়ার আগে আরেকটা tool call করার সিদ্ধান্ত নিতে হবে।
- **আপনি যা দেখতে পাবেন:** `end_turn` হওয়ার আগে কমপক্ষে দুটো tool call iteration। agent প্রথমে search করবে, search result টা একটা calculation-এ ব্যবহার করবে, এবং তারপর combined answer রিটার্ন করবে।
- 💡 **Nudge:** এমন একটা prompt ডিজাইন করুন যেখানে প্রথম tool call-এর আউটপুট দ্বিতীয়টার ইনপুট হিসেবে লাগে। কোন ধরনের query দিলে এই chain টা ফোর্স করা যাবে?

---

### ধাপ ৬: Safety iteration cap যোগ করুন
ম্যাক্সিমাম বাউন্ড হিসেবে ২০-এর একটা `safety iteration cap` যোগ করুন (এটা primary stopping mechanism হবে না) এবং এটা ট্রিগার হলে একটা warning log করুন।

- **কেন:** এক্সামে দেখা হবে আপনি `safety caps` (যা fallback হিসেবে ঠিক আছে) আর caps-কে primary stopping mechanism (যা একদমই anti-pattern) হিসেবে ব্যবহার করার পার্থক্য বোঝেন কিনা। নর্মাল অপারেশনে আপনার cap-টা কখনোই ট্রিগার হওয়ার কথা না।
- **আপনি যা দেখতে পাবেন:** একটা `MAX_ITERATIONS` constant, একটা counter যা প্রতিটি loop-এ বাড়তে (increment) থাকবে, আর cap হিট করলে একটা warning log। নর্মাল query গুলো ২০-এ পৌঁছানোর অনেক আগেই `stop_reason`-এর মাধ্যমে থেমে যাবে।
- 💡 **Nudge:** আপনার loop-এর কোথায় counter টা চেক করা উচিত? এটা ট্রিগার হলে কী হওয়া উচিত — error নাকি warning?

---

### গাইডেন্স (Guidance):
Loop-এর শুরুতে একটা counter variable নিন। প্রতিটি iteration-এর শুরুতে এটা increment করুন। যদি `counter >= MAX_ITERATIONS` হয়, তাহলে একটা warning log করুন এবং `break` করুন। মনে রাখবেন, এটা একটা safety net মাত্র, primary control না।

