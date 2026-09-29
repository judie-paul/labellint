"""Missing optional dependencies must produce actionable, lazy errors."""

import sys

import pytest

from labellint.detectors.contradiction import ContradictionDetector
from labellint.detectors.duplicate import DuplicateDetector
from labellint.ingest.huggingface import load_ultrafeedback
from labellint.synthetic import generate


def test_missing_optional_models(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setitem(sys.modules, "sentence_transformers", None)
    records = [r.for_detection() for r in generate(2)]
    with pytest.raises(RuntimeError, match=r"labellint\[embeddings\]"):
        DuplicateDetector(backend="embeddings").detect(records)
    with pytest.raises(RuntimeError, match=r"labellint\[nli\]"):
        ContradictionDetector(backend="nli").detect(records)


def test_missing_optional_dataset(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setitem(sys.modules, "datasets", None)
    with pytest.raises(RuntimeError, match=r"labellint\[datasets\]"):
        load_ultrafeedback(1)
    with pytest.raises(ValueError, match="positive"):
        load_ultrafeedback(0)
