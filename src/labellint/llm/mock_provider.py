"""Deterministic provider for offline runs and tests."""


class MockProvider:
    """Produce notes with no API key, network, or random state."""

    def complete(self, prompt: str) -> str:
        """Summarize evidence without pretending a model inspected the annotation."""
        if prompt.startswith("Paraphrase:"):
            return "Reviewer assessment: " + prompt.removeprefix("Paraphrase:").strip()
        return "Review recommended. Automated evidence: " + prompt[:500]
