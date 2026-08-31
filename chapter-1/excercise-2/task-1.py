class ResearchCoordinator:
    def __init__(self):
        self.role = "orchestrating hub"

    def decompose(self, topic: str) -> list:
        subtopics = [
            "solar", "wind", "geothermal",
            "tidal", "biomass", "fusion"
        ]
        return subtopics

    def build_subagent_prompt(self, subtopic: str, topic: str, goal: str) -> str:
        return (
            f"Research goal: {goal}\n"
            f"Parent topic: {topic}\n"
            f"Your assigned subtopic: {subtopic}\n"
            f"Task: Research this subtopic thoroughly and return findings."
        )

    def call_web_search_agent(self, prompt: str) -> str:
        return f"[web_search findings for prompt: {prompt[:50]}...]"

    def call_document_agent(self, prompt: str) -> str:
        return f"[document_analysis findings for prompt: {prompt[:50]}...]"

    def evaluate_coverage(self, subtopics: list, findings: dict) -> dict:
        coverage = {}
        for st in subtopics:
            if findings.get(st):
                coverage[st] = "well-covered"
            else:
                coverage[st] = "missing"
        return coverage

    def run(self, topic: str) -> dict:
        goal = f"Produce a comprehensive research report on {topic}"
        subtopics = self.decompose(topic)

        assigned = subtopics[:2]
        web_prompt = self.build_subagent_prompt(assigned[0], topic, goal)
        doc_prompt = self.build_subagent_prompt(assigned[1], topic, goal)

        findings = {
            assigned[0]: self.call_web_search_agent(web_prompt),
            assigned[1]: self.call_document_agent(doc_prompt)
        }

        coverage = self.evaluate_coverage(subtopics, findings)

        report = {
            "topic": topic,
            "subtopics": subtopics,
            "findings": findings,
            "coverage": coverage
        }
        return report

r = ResearchCoordinator().run("renewable energy")
print(r)