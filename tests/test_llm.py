"""Provider tests never contact an API or require credentials."""

from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from labellint.config import Settings
from labellint.llm.enrich import enrich, get_provider, paraphrase
from labellint.llm.mock_provider import MockProvider
from labellint.pipeline import scan
from labellint.simulate import simulate
from labellint.synthetic import generate


def test_mock_and_fallback(monkeypatch: pytest.MonkeyPatch) -> None:
    for provider in ("openai", "anthropic"):
        monkeypatch.delenv(provider.upper() + "_API_KEY", raising=False)
        assert isinstance(get_provider(provider), MockProvider)
    with pytest.raises(ValueError):
        get_provider("invalid")
    assert paraphrase("A good answer") == paraphrase("A good answer")
    assert paraphrase.cache_info().hits >= 1
    assert simulate(generate(20), Settings(llm_rationales=True))


def test_sdk_contracts(monkeypatch: pytest.MonkeyPatch) -> None:
    from labellint.llm import anthropic_provider, openai_provider

    openai = MagicMock()
    openai.return_value.chat.completions.create.return_value = SimpleNamespace(
        choices=[SimpleNamespace(message=SimpleNamespace(content="Review this rating."))]
    )
    anthropic = MagicMock()
    anthropic.return_value.messages.create.return_value = SimpleNamespace(
        content=[SimpleNamespace(type="text", text="Review this rating.")]
    )
    monkeypatch.setattr(openai_provider, "OpenAI", openai)
    monkeypatch.setattr(anthropic_provider, "Anthropic", anthropic)
    for name in ("openai", "anthropic"):
        monkeypatch.setenv(name.upper() + "_API_KEY", "test-only-not-a-real-key")
        assert get_provider(name).complete("Evidence") == "Review this rating."
    assert openai.call_args.kwargs["max_retries"] == 2
    assert anthropic.call_args.kwargs["timeout"] == 20


def test_enrichment_failure_preserves_evidence(monkeypatch: pytest.MonkeyPatch) -> None:
    report = scan(simulate(generate(20), Settings()), Settings())
    client = MagicMock()
    client.complete.side_effect = RuntimeError("unavailable")
    monkeypatch.setattr("labellint.llm.enrich.get_provider", lambda _: client)
    result = enrich(report)
    assert all(r.note is None for r in report.records)
    assert all(r.note is not None for r in result.records if r.flagged)
    assert [r.findings for r in result.records] == [r.findings for r in report.records]
