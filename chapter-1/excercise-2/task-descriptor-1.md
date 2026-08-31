# Hub-and-Spoke Research Coordinator বিল্ড করুন

**সময়:** ৬০ মিনিট

---

### এই এক্সারসাইজে যা যা শিখবেন:
- `Hub-and-spoke architecture` কীভাবে একটা `coordinator`-এর মাধ্যমে সব কমিউনিকেশন সেন্ট্রালাইজ করে।
- কেন `subagent isolation` মানে হলো প্রতি টুকরো `context`-কে এক্সপ্লিসিটলি পাস করতে হবে।
- কীভাবে এমন `broad task decomposition` ইমপ্লিমেন্ট করবেন যা `narrow decomposition failure` এড়িয়ে চলে।
- `Iterative refinement loops` কীভাবে `coverage gaps` ধরে ফেলে এবং পূরণ করে।
- কেন ফেইলিউর ট্রেস করলে দেখা যায় সমস্যাটা `coordinator decomposition`-এ — এটাই সঠিক `diagnostic approach`।

---

### ধাপ ১: একটা coordinator agent বানান যেটা broad research topic ইনপুট নেয়
একটা `coordinator agent` তৈরি করুন যেটা ইনপুট হিসেবে একটা `broad research topic` নেয়।

- **কেন:** `Hub-and-spoke architecture`-এ coordinator হলো সেন্ট্রাল হাব। এক্সামে দেখা হবে আপনি বুঝছেন কিনা যে `task decomposition`, `subagent selection`, আর `result aggregation` — এই সবকিছুর মালিক coordinator, subagents না।
- **আপনি যা দেখতে পাবেন:** একটা `coordinator function` যেটা একটা `topic string` নেয় আর একটা `structured research report` রিটার্ন করে। এটার `system prompt`-এ এটার রোল `orchestrating hub` হিসেবে ডিফাইন করা থাকবে।
- 💡 **Nudge:** ভাবুন তো coordinator-এর দায়িত্বগুলো কী কী: `decomposition`, `delegation`, `aggregation`, আর `refinement`। ইনিশিয়াল সেটআপে কী কী দরকার?

---

### ধাপ ২: Task decomposition logic ইমপ্লিমেন্ট করুন
টপিকটাকে কমপক্ষে ৫টা আলাদা `subtopics`-এ ভাগ করুন যা পুরো বিষয়টার `full breadth` কভার করে।

- **কেন:** `Narrow decomposition` হলো এক্সামের একটা স্পেসিফিক ফেইলিউর প্যাটার্ন। যেমন `renewable energy` টপিক দিলে coordinator যদি শুধু `solar` আর `wind` assign করে, তাহলে পুরো ক্যাটাগরিই মিস হয়ে যায়। এক্সামে আশা করা হয় আপনি বুঝবেন যে `incomplete output`-এর মূল কারণ `coordinator decomposition`।
- **আপনি যা দেখতে পাবেন:** একটা `decomposition function` যেটা যেকোনো `broad topic`-এর জন্য ৫ বা তার বেশি `subtopics` তৈরি করে। `renewable energy`-এর ক্ষেত্রে কমপক্ষে `solar`, `wind`, `geothermal`, `tidal`, `biomass`, আর `fusion` কভার করা থাকবে।
- 💡 **Nudge:** `breadth` কীভাবে নিশ্চিত করবেন? coordinator-কে প্রথমে ক্যাটাগরিগুলো এক্সপ্লিসিটলি `enumerate` করতে বলুন, তারপর ডিটেইলে যান।

---

### ধাপ ৩: দুটো subagent স্পন করুন — explicit context passing সহ
দুটো `subagent` (web search আর document analysis) স্পন করুন, আর প্রতিটাকে `explicit context passing` করুন — অর্থাৎ প্রতিটা `subagent prompt`-এ সব relevant information ইনক্লুড করুন।

- **কেন:** `Subagent isolation` মানে কোনো `shared memory` নেই, কোনো `inherited context` নেই। এক্সামে এটা খুব জোরে টেস্ট করা হয়: যদি কোনো `subagent` খারাপ রেজাল্ট দেয়, চেক করুন coordinator তাকে যথেষ্ট `context` দিয়েছে কিনা — subagent নিজে ফল্টি কিনা সেটা না।
- **আপনি যা দেখতে পাবেন:** দুটো `subagent invocation`, যেখানে প্রতিটা পায় পুরো assigned `subtopic`, `research goal`, এবং আগের agents-এর যেকোনো relevant `context` — সবকিছু prompt-এ এক্সপ্লিসিটলি ইনক্লুড করা।
- 💡 **Nudge:** মনে রাখবেন: `subagents` একদম `blank slate` নিয়ে শুরু করে। তাদের কাজ ঠিকমতো করার জন্য কী কী তথ্য দরকার?

---

### ধাপ ৪: দুটো subagent-এর results aggregate করুন এবং coverage evaluate করুন
দুটো `subagent`-এর results `aggregate` করুন এবং `coverage completeness` evaluate করুন।

- **কেন:** Coordinator-কে evaluate করতে হবে যে combined results মূল টপিকের `full breadth` কভার করছে কিনা। এখান থেকেই `iterative refinement` শুরু হয় — এখানে ধরা পড়া `gaps` গুলো `re-delegation` ট্রিগার করে।
- **আপনি যা দেখতে পাবেন:** একটা `aggregation function` যেটা দুটো `subagent`-এর results কম্বাইন করে আর একটা `coverage assessment` তৈরি করে — যেখানে লিস্ট করা থাকবে কোন `subtopics` গুলো `well-covered`, কোনগুলো `partially covered`, আর কোনগুলো `missing`।
- 💡 **Nudge:** Coordinator-কে কী চেক করতে হবে? assigned `subtopics` আর actually রিটার্ন হওয়া findings গুলোকে কম্পেয়ার করুন।

---

### ধাপ ৫: Iterative refinement loop ইমপ্লিমেন্ট করুন
যদি coordinator `coverage gaps` খুঁজে পায়, তাহলে targeted queries সহ `subagents`-দের আবার `re-delegate` করুন এবং coverage যথেষ্ট না হওয়া পর্যন্ত re-invoke করতে থাকুন।

- **কেন:** `Iterative refinement` হলো coordinator-এর একটা core responsibility যা এক্সামে টেস্ট হয়। একবার `single-shot delegation` করলেই হবে না — coordinator-কে output evaluate করতে হবে আর gaps-এর জন্য re-delegate করতে হবে। এটাই coordinator-কে সাধারণ `dispatcher` থেকে আলাদা করে।
- **আপনি যা দেখতে পাবেন:** একটা loop যা coverage চেক করে, gaps খুঁজে বের করে, missing `subtopics`-এর জন্য targeted follow-up queries subagents-দের পাঠায়, এবং একটা `coverage threshold` মেটা বা `maximum iteration count`-এ পৌঁছানো পর্যন্ত re-evaluate করতে থাকে।
- 💡 **Nudge:** কী আরেকটা iteration ট্রিগার করে? আর loop টা কোথায় এসে থামে?

---

### ধাপ ৬: "renewable energy technologies" টপিক দিয়ে টেস্ট করুন
`renewable energy technologies` টপিক দিয়ে টেস্ট করুন আর ভেরিফাই করুন যে ফাইনাল আউটপুটে `solar`, `wind`, `geothermal`, `tidal`, `biomass`, আর `fusion` সবই কভার হয়েছে।

- **কেন:** এই স্পেসিফিক টেস্ট কেসটা এক্সামের `narrow decomposition failure` প্যাটার্নের সাথে ম্যাপ করে। যদি আপনার আউটপুটে শুধু `solar` আর `wind` থাকে, তাহলে `root cause` হলো `coordinator decomposition` — এক্সামে ঠিক এই `diagnostic` টাই আশা করা হয় আপনার কাছ থেকে।
- **আপনি যা দেখতে পাবেন:** একটা ফাইনাল `research report` যেখানে ছয়টা এনার্জি টাইপের — `solar`, `wind`, `geothermal`, `tidal`, `biomass`, আর `fusion` — সবগুলোর ওপর substantive section থাকবে। `Coverage evaluation` দেখাবে ১০০% `completeness`।
- 💡 **Nudge:** Coordinator রান করুন আর আউটপুট চেক করুন। ক্যাটাগরি মিসিং থাকলে, পাইপলাইনের কোথায় সমস্যা হলো?

---

### গাইডেন্স (Guidance):
আউটপুটে যদি ক্যাটাগরি মিসিং থাকে, তাহলে ব্যাকওয়ার্ড ট্রেস করুন: `decomposition`-এ কি সেগুলো ইনক্লুড ছিল? না থাকলে, `decomposition` ঠিক করুন। যদি ইনক্লুড থাকে, তাহলে `subagents` কি assignment পেয়েছিল? `context passing` চেক করুন।