"""Normalize a fixture-compatible UltraFeedback instruction into rating events."""

from typing import Any

from labellint.schema import AnnotationRecord


def ultrafeedback(row: dict[str, Any], index: int) -> list[AnnotationRecord]:
    """Expand per-completion/per-aspect annotations; never invent observed timings."""
    output = []
    for completion_index, completion in enumerate(row["completions"]):
        for aspect, annotation in completion["annotations"].items():
            # Source timings are placeholders, not real worker telemetry. Simulation replaces them.
            output.append(
                AnnotationRecord(
                    record_id=f"uf_{index:06d}_c{completion_index}_{aspect}",
                    item_id=f"uf_{index:06d}_c{completion_index}",
                    source="ultrafeedback",
                    prompt=row["instruction"],
                    response=completion["response"],
                    aspect=aspect,
                    annotator_id="source",
                    rating=int(annotation["Rating"]),
                    rationale=annotation["Rationale"],
                    time_spent_sec=1.0,
                )
            )
    return output
