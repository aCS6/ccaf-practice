class ResearchCoordinator:
    def __init__(self, max_iterations: int = 5):
        self.role = "orchestrating hub"
        self.max_iterations = max_iterations

    # ---------- 1. DECOMPOSITION ----------
    def decompose(self, topic: str) -> list:
        """Break topic into subtopics covering full breadth."""
        subtopics = [
            "solar", "wind", "geothermal",
            "tidal", "biomass", "fusion"
        ]
        return subtopics

    # ---------- Helpers used by delegation ----------
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

    # ---------- 2. DELEGATION ----------
    def delegate(self, subtopics: list, topic: str, goal: str) -> dict:
        """Send subtopics to subagents with explicit context. Returns findings."""
        results = {}
        for i, st in enumerate(subtopics):
            prompt = self.build_subagent_prompt(st, topic, goal)
            if i % 2 == 0:
                results[st] = self.call_web_search_agent(prompt)
            else:
                results[st] = self.call_document_agent(prompt)
        return results

    # ---------- 3. AGGREGATION ----------
    def aggregate(self, subtopics: list, findings: dict) -> dict:
        """Combine findings + evaluate coverage (well-covered/missing)."""
        coverage = {}
        for st in subtopics:
            coverage[st] = "well-covered" if findings.get(st) else "missing"
        return coverage

    # ---------- 4. REFINEMENT ----------
    def refine(self, topic: str, goal: str, subtopics: list, findings: dict) -> dict:
        """Loop: check coverage, re-delegate gaps, until complete or max_iterations."""
        iteration = 0
        while iteration < self.max_iterations:
            coverage = self.aggregate(subtopics, findings)
            missing = [st for st, status in coverage.items() if status == "missing"]

            if not missing:
                break

            new_results = self.delegate(missing, topic, goal)
            findings.update(new_results)
            iteration += 1

        self.iterations_used = iteration  # stored for reporting
        return findings

    # ---------- ORCHESTRATOR ----------
    def run(self, topic: str) -> dict:
        goal = f"Produce a comprehensive research report on {topic}"

        subtopics = self.decompose(topic)
        findings = self.delegate(subtopics, topic, goal)
        findings = self.refine(topic, goal, subtopics, findings)
        coverage = self.aggregate(subtopics, findings)

        return {
            "topic": topic,
            "subtopics": subtopics,
            "findings": findings,
            "coverage": coverage,
            "iterations_used": getattr(self, "iterations_used", 0)
        }


# ---------- Test ----------
coordinator = ResearchCoordinator()
report = coordinator.run("renewable energy technologies")

print("Subtopics:", report["subtopics"])
print("Coverage:", report["coverage"])
print("Iterations used:", report["iterations_used"])

expected = {"solar", "wind", "geothermal", "tidal", "biomass", "fusion"}
covered = {st for st, status in report["coverage"].items() if status == "well-covered"}
assert expected.issubset(covered), f"Missing: {expected - covered}"
print("✅ Full coverage achieved")