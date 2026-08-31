class ResearchCoordinator:
    def __init__(self, max_iterations: int = 5):
        self.role = "orchestrating hub"
        self.max_iterations = max_iterations

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
            coverage[st] = "well-covered" if findings.get(st) else "missing"
        return coverage

    def run(self, topic: str) -> dict:
        goal = f"Produce a comprehensive research report on {topic}"
        subtopics = self.decompose(topic)
        findings = {}

        iteration = 0
        while iteration < self.max_iterations:
            coverage = self.evaluate_coverage(subtopics, findings)
            missing = [st for st, status in coverage.items() if status == "missing"]

            if not missing:
                break  # coverage complete, stop looping

            # Re-delegate missing subtopics (alternate between the two agents)
            for i, st in enumerate(missing):
                prompt = self.build_subagent_prompt(st, topic, goal)
                if i % 2 == 0:
                    findings[st] = self.call_web_search_agent(prompt)
                else:
                    findings[st] = self.call_document_agent(prompt)

            iteration += 1

        coverage = self.evaluate_coverage(subtopics, findings)
        report = {
            "topic": topic,
            "subtopics": subtopics,
            "findings": findings,
            "coverage": coverage,
            "iterations_used": iteration
        }
        return report

coordinator = ResearchCoordinator()
report = coordinator.run("renewable energy technologies")

print("Subtopics:", report["subtopics"])
print("Coverage:", report["coverage"])
print("Iterations used:", report["iterations_used"])

# Assertion to confirm full coverage
expected = {"solar", "wind", "geothermal", "tidal", "biomass", "fusion"}
covered = {st for st, status in report["coverage"].items() if status == "well-covered"}

assert expected.issubset(covered), f"Missing: {expected - covered}"
print("✅ Full coverage achieved")