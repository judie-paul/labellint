"""Explicit provider selection and cached optional paraphrasing."""

import logging
import os
from functools import lru_cache

from labellint.aggregate import ScanReport
from labellint.llm.base import Provider
from labellint.llm.mock_provider import MockProvider

logger = logging.getLogger(__name__)


def get_provider(name: str) -> Provider:
    """Fall back to deterministic mock when selected provider has no key."""
    if name == "mock":
        return MockProvider()
    if name not in {"openai", "anthropic"}:
        raise ValueError("provider must be mock, openai or anthropic")
    key = os.getenv(f"{name.upper()}_API_KEY")
    if not key:
        logger.info("No key for %s; using mock", name)
        return MockProvider()
    if name == "openai":
        from labellint.llm.openai_provider import OpenAIProvider

        return OpenAIProvider(key)
    from labellint.llm.anthropic_provider import AnthropicProvider

    return AnthropicProvider(key)


def enrich(scan: ScanReport, provider: str = "mock") -> ScanReport:
    """Copy the report and enrich only flagged records; preserve original evidence."""
    client = get_provider(provider)
    result = scan.model_copy(deep=True)
    for row in result.records:
        if row.flagged:
            prompt = "; ".join(f.reason for f in row.findings)
            try:
                row.note = client.complete(prompt)
            except Exception:
                logger.warning("Reviewer note unavailable; preserving audit evidence")
                row.note = "Reviewer note unavailable. Inspect detector evidence."
    return result


@lru_cache(maxsize=1024)
def paraphrase(text: str, provider: str = "mock") -> str:
    """Cache identical provider/input requests within a process."""
    return get_provider(provider).complete("Paraphrase: " + text)
