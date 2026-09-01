# STEP-1
-----------
Create two MCP tools with intentionally ambiguous descriptions (e.g. get_customer: Retrieves customer information and lookup_order: Retrieves order details)

Why: Reproducing a misrouting scenario first-hand builds intuition for why minimal descriptions fail. The exam tests your ability to identify ambiguous descriptions as the root cause of tool selection errors.

You should see: Two tool definitions registered with your MCP server, each having a single-sentence description that does not mention input formats, example queries, or boundaries.
Nudge

Think about what information is missing — what inputs does each tool accept? When should one be used instead of the other?
Guidance

Define each tool using the MCP SDK inputSchema with a string parameter for the identifier. Keep descriptions to one generic sentence each.
Starter Code

import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
const server = new McpServer({ name: "customer-tools", version: "1.0.0" });
server.tool("get_customer", "Retrieves customer information", { identifier: { type: "string" } }, async ({ identifier }) => {
  return { content: [{ type: "text", text: `Customer data for ${identifier}` }] };
});
server.tool("lookup_order", "Retrieves order details", { identifier: { type: "string" } }, async ({ identifier }) => {
  return { content: [{ type: "text", text: `Order data for ${identifier}` }] };
});

# STEP-2
-----------
Test with 10 queries covering different user intents and log which tool the model selects for each

Why: Quantifying selection accuracy before and after description changes gives you concrete evidence of the impact. The exam expects you to know that description quality directly affects selection reliability.

You should see: A log showing at least 2-3 misrouted queries where the model selected get_customer for order-related queries or vice versa, demonstrating the ambiguity problem.
Nudge

Include queries that mention order numbers, customer emails, tracking IDs, and ambiguous phrases like "check my account" to cover edge cases.
Guidance

Create a test harness that sends each query to the Claude API with both tools available and tool_choice set to auto, then logs which tool was called.
Starter Code

const queries = [
  "What is the status of order #12345?",
  "Look up customer john@example.com",
  "Check my order tracking",
  "Find the account for phone 555-0123",
  "Where is my package?",
  "Is order #67890 eligible for a refund?",
  "What loyalty tier is this customer?",
  "I need details on order #11111",
  "Verify the customer account status",
  "When will order #99999 arrive?"
];
for (const query of queries) {
  const response = await client.messages.create({
    model: "claude-sonnet-5",
    max_tokens: 1024,
    tools: toolDefinitions,
    messages: [{ role: "user", content: query }]
  });
  const toolUse = response.content.find(b => b.type === "tool_use");
  console.log(`Query: ${query} => Tool: ${toolUse?.name}`);
}

# STEP-3
-----------
Rewrite both descriptions to include: purpose, expected inputs with formats, example queries, edge cases, and explicit boundaries against the other tool

Why: This is the core exam skill — the lowest-effort, highest-leverage fix for misrouting. Production-grade descriptions include all five elements: purpose, inputs, examples, edge cases, and boundaries.

You should see: Each tool description is 3-5 sentences long, explicitly states accepted identifier formats, gives example queries, and includes a boundary statement like "Do NOT use for order-specific queries — use lookup_order for those."
Nudge

For each tool, answer five questions: What does it do? What inputs does it accept? What queries suit it? What does it NOT handle? When should the other tool be used instead?
Guidance

Include specific format examples (e.g. email addresses, phone numbers, order numbers like #NNNNN) and explicitly state the return data shape for each tool.
Starter Code

server.tool("get_customer", "Looks up a customer account by email address, phone number, or customer ID. Returns customer profile (name, contact details, account status, loyalty tier). Use this when you need to verify who the customer is or check account details. Do NOT use for order-specific queries — use lookup_order for those.", { identifier: { type: "string", description: "Customer email, phone, or ID" } }, async ({ identifier }) => {
  return { content: [{ type: "text", text: `Customer profile for ${identifier}` }] };
});

# STEP-4
-----------
Re-run the same 10 queries and compare selection accuracy before and after

Why: Measuring improvement validates that description quality is the root cause. The exam expects you to understand that better descriptions produce measurably better selection without any architectural changes.

You should see: Selection accuracy improves to 9/10 or 10/10 correct, with previously misrouted queries now hitting the correct tool. A clear before/after comparison showing the improvement.
Nudge

Run the exact same 10 queries and compare results side by side. Pay special attention to the queries that were misrouted before.
Guidance

Create a simple comparison table logging query, expected tool, tool selected before, and tool selected after. Calculate accuracy percentage for both runs.
Starter Code

let correct = 0;
const expected = ["lookup_order", "get_customer", "lookup_order", "get_customer", "lookup_order", "lookup_order", "get_customer", "lookup_order", "get_customer", "lookup_order"];
for (let i = 0; i < queries.length; i++) {
  const response = await client.messages.create({ model: "claude-sonnet-5", max_tokens: 1024, tools: updatedToolDefinitions, messages: [{ role: "user", content: queries[i] }] });
  const toolUse = response.content.find(b => b.type === "tool_use");
  const match = toolUse?.name === expected[i];
  if (match) correct++;
  console.log(`${match ? "CORRECT" : "WRONG"} | ${queries[i]} => ${toolUse?.name} (expected: ${expected[i]})`);
}
console.log(`Accuracy: ${correct}/${queries.length}`);

# STEP-5
-----------
Review your system prompt for keyword-sensitive instructions that could override the improved descriptions

Why: System prompt conflicts are a subtle failure mode the exam tests. Keywords like "always check customer details" can create unintended tool associations that override even well-written descriptions.

You should see: A list of any keyword-sensitive phrases in your system prompt that could trigger incorrect tool associations, along with rewritten versions that avoid the conflict.
Nudge

Search for words like "customer", "order", "check", "verify", "look up" in your system prompt — these could trigger unintended associations with specific tools.
Guidance

Compare tool selection results with and without the system prompt. If accuracy drops with the prompt, identify which phrases are causing the interference.
Starter Code

// Test with a system prompt that contains a conflicting instruction
const conflictingPrompt = "Always check customer details before proceeding with any request.";
const response = await client.messages.create({
  model: "claude-sonnet-5",
  max_tokens: 1024,
  system: conflictingPrompt,
  tools: updatedToolDefinitions,
  messages: [{ role: "user", content: "What is the status of order #12345?" }]
});
// If get_customer is selected instead of lookup_order, the system prompt is interfering