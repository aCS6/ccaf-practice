class ResearchCoordinator:
    def __init__(self):
        self.role = "orchestrating hub"

    def decompose(self, topic: str) -> list:
        # In practice this would call an LLM to enumerate categories.
        # For renewable energy, the expected breadth is:
        subtopics = [
            "solar", "wind", "geothermal",
            "tidal", "biomass", "fusion"
        ]
        return subtopics

    def build_subagent_prompt(self, subtopic: str, topic: str, goal: str) -> str:
        # Everything the subagent needs, since it has NO memory of anything else.
        return (
            f"Research goal: {goal}\n"
            f"Parent topic: {topic}\n"
            f"Your assigned subtopic: {subtopic}\n"
            f"Task: Research this subtopic thoroughly and return findings."
        )
    
    def call_web_search_agent(self, prompt: str) -> str:
        # Placeholder: would call an LLM/tool here
        return f"[web_search findings for prompt: {prompt[:50]}...]"

    def call_document_agent(self, prompt: str) -> str:
        # Placeholder: would call an LLM/tool here
        return f"[document_analysis findings for prompt: {prompt[:50]}...]"
    
    def run(self, topic: str) -> dict:
        goal = f"Produce a comprehensive research report on {topic}"
        subtopics = self.decompose(topic)

        # Only spawning 2 subagents for now (as per this step)
        assigned = subtopics[:2]  # e.g. "solar", "wind"

        web_prompt = self.build_subagent_prompt(assigned[0], topic, goal)
        doc_prompt = self.build_subagent_prompt(assigned[1], topic, goal)

        web_result = self.call_web_search_agent(web_prompt)
        doc_result = self.call_document_agent(doc_prompt)

        report = {
            "topic": topic,
            "subtopics": subtopics,
            "findings": {
                assigned[0]: web_result,
                assigned[1]: doc_result
            },
            "coverage": {}
        }
        return report

r = ResearchCoordinator().run("Artificial Intelligence in Healthcare")
print(r)