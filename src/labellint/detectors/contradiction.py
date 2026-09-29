"""Rationale polarity versus ordinal rating, with an optional NLI backend."""

import re

import numpy as np

from labellint.detectors.base import Finding, validate_inputs
from labellint.schema import DetectorRecord

POSITIVE = {"excellent", "accurate", "helpful", "clear", "relevant", "correct", "good"}
NEGATIVE = {"incorrect", "irrelevant", "poor", "missing", "unclear", "fails", "wrong", "bad"}


def sentiment(text: str) -> int:
    """Count polarity terms with short-window negation; neutral text scores zero."""
    words = re.findall(r"[a-z]+|[.!?;,]", text.lower())
    score = 0
    negated = False
    for word in words:
        if word in {"not", "never", "no"}:
            negated = True
        if word in {"but", "however", ".", "!", "?", ";", ","}:
            negated = False
        value = int(word in POSITIVE) - int(word in NEGATIVE)
        if negated:
            value *= -1
        score += value
    return score


class ContradictionDetector:
    """Detect strong opposing sentiment; NLI uses model's contradiction class."""

    def __init__(self, backend: str = "lexicon", threshold: float = 0.7) -> None:
        if backend not in {"lexicon", "nli"} or not 0 <= threshold <= 1:
            raise ValueError("invalid contradiction detector configuration")
        self.backend, self.threshold = backend, threshold

    def detect(self, records: list[DetectorRecord]) -> list[Finding]:
        """Return strong conflicts only; rating three has no directional hypothesis."""
        validate_inputs(records)
        if not records:
            return []
        if self.backend == "nli":
            try:
                from sentence_transformers import CrossEncoder
            except ImportError:
                raise RuntimeError("Install labellint[nli] for the NLI backend") from None
            model = CrossEncoder("cross-encoder/nli-deberta-v3-base")
            pairs = [
                (
                    r.rationale,
                    "The response is "
                    + ("good." if r.rating >= 4 else "poor." if r.rating <= 2 else "average."),
                )
                for r in records
            ]
            probabilities = np.asarray(model.predict(pairs, apply_softmax=True))
            # This model's published label order is contradiction, entailment, neutral.
            conflicts = [float(row[0]) for row in probabilities]
        else:
            conflicts = [float(sentiment(r.rationale) * (r.rating - 3) < 0) for r in records]
        return [
            Finding(
                record_id=r.record_id,
                detector="contradiction",
                score=score,
                reason="Rationale sentiment conflicts with the assigned rating",
            )
            for r, score in zip(records, conflicts, strict=True)
            if r.rating != 3 and score >= self.threshold
        ]
