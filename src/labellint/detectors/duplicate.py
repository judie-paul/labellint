"""Cross-item rationale similarity using TF-IDF or optional embeddings."""

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.neighbors import NearestNeighbors

from labellint.detectors.base import Finding, validate_inputs
from labellint.schema import DetectorRecord


class DuplicateDetector:
    """Find within-worker reuse, excluding agreement on the same item."""

    def __init__(self, threshold: float = 0.92, backend: str = "tfidf") -> None:
        if not 0 <= threshold <= 1 or backend not in {"tfidf", "embeddings"}:
            raise ValueError("invalid duplicate detector configuration")
        self.threshold, self.backend = threshold, backend

    def detect(self, records: list[DetectorRecord]) -> list[Finding]:
        """Use radius neighbors to avoid allocating a full dense similarity matrix."""
        validate_inputs(records)
        if len(records) < 2:
            return []
        texts = [r.rationale for r in records]
        if self.backend == "embeddings":
            try:
                from sentence_transformers import SentenceTransformer
            except ImportError:
                raise RuntimeError(
                    "Install labellint[embeddings] for the embedding backend"
                ) from None
            vectors = SentenceTransformer("all-MiniLM-L6-v2").encode(texts)
        else:
            try:
                vectors = TfidfVectorizer(ngram_range=(1, 2)).fit_transform(texts)
            except ValueError:
                return []
        neighbors = NearestNeighbors(metric="cosine", algorithm="brute").fit(vectors)
        findings = []
        for i, record in enumerate(records):
            distances, indices = neighbors.radius_neighbors(
                vectors[i : i + 1], radius=1 - self.threshold + 1e-9, sort_results=True
            )
            for distance, j in zip(distances[0], indices[0], strict=True):
                if (
                    i != j
                    and record.item_id != records[j].item_id
                    and record.annotator_id == records[j].annotator_id
                ):
                    score = float(np.clip(1 - distance, 0, 1))
                    findings.append(
                        Finding(
                            record_id=record.record_id,
                            detector="duplicate",
                            score=score,
                            reason=f"Rationale similarity {score:.3f} to {records[j].record_id}",
                        )
                    )
                    break
        return findings
