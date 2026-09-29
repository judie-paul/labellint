"""Optional Hugging Face source; default runs never import datasets."""

from labellint.normalize import ultrafeedback
from labellint.schema import AnnotationRecord


def load_ultrafeedback(limit: int = 100) -> list[AnnotationRecord]:
    """Stream at most limit instructions using the optional datasets extra."""
    if limit < 1:
        raise ValueError("limit must be positive")
    try:
        from datasets import load_dataset
    except ImportError:
        raise RuntimeError("Install labellint[datasets] to load UltraFeedback") from None
    dataset = load_dataset("openbmb/UltraFeedback", split="train", streaming=True)
    return [record for i, row in enumerate(dataset.take(limit)) for record in ultrafeedback(row, i)]
