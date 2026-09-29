"""Small deterministic source corpus; annotator simulation is a separate stage."""

import argparse
from pathlib import Path

import numpy as np

from labellint.schema import AnnotationRecord

_TOPICS = (
    ("photosynthesis", "Plants use sunlight to convert water and carbon dioxide into sugars."),
    ("unit testing", "A unit test checks one small behavior with controlled inputs."),
    ("rainfall", "Water droplets in clouds combine and fall when they become heavy enough."),
    ("recycling", "Sorting reusable materials reduces waste and conserves raw resources."),
    ("binary search", "Repeatedly halve a sorted search space to locate a target efficiently."),
)
_RATIONALES = (
    "Incorrect and irrelevant; it fails to address the question.",
    "Poor explanation with missing details and unclear reasoning.",
    "Partially useful, but it needs more context and detail.",
    "Clear and relevant explanation with accurate core details.",
    "Excellent, accurate and helpful explanation that directly answers the question.",
)
_COMMENTS = (
    "The explanation should connect the cause to the outcome.",
    "A concrete example would help a beginner apply the idea.",
    "The terminology needs to match the question's scope.",
    "The response should distinguish the process from its purpose.",
    "The answer needs enough context to stand on its own.",
    "A reader should be able to identify the main mechanism.",
    "Consider whether the stated details support the conclusion.",
    "The level of detail should fit an introductory explanation.",
)


def generate(count: int = 100, seed: int = 42) -> list[AnnotationRecord]:
    """Generate source ratings without inventing corruption ground truth."""
    if count < 1:
        raise ValueError("count must be positive")
    rng = np.random.default_rng(seed)
    records = []
    for index in range(count):
        topic, answer = _TOPICS[int(rng.integers(len(_TOPICS)))]
        rating = int(rng.integers(1, 6))
        response = answer if rating >= 3 else "The answer is unrelated to the requested topic."
        records.append(
            AnnotationRecord(
                record_id=f"syn_{index:06d}_source",
                item_id=f"syn_{index:06d}",
                source="synthetic",
                prompt=f"Explain {topic} for learner {index + 1} in plain language.",
                response=response,
                aspect="helpfulness",
                annotator_id="source",
                rating=rating,
                rationale=(
                    f"For {topic}: {_RATIONALES[rating - 1]} "
                    f"{_COMMENTS[int(rng.integers(len(_COMMENTS)))]}"
                ),
                time_spent_sec=round(float(rng.lognormal(3.8, 0.35)), 3),
            )
        )
    return records


def write_jsonl(records: list[AnnotationRecord], destination: Path) -> None:
    """Write stable UTF-8 JSONL with explicit newline behavior."""
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("w", encoding="utf-8", newline="\n") as stream:
        for record in records:
            stream.write(record.model_dump_json() + "\n")


def main() -> None:
    """Expose the source generator while the full Typer CLI is being built."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--count", type=int, default=100)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--out", type=Path, default=Path("data/raw.jsonl"))
    args = parser.parse_args()
    write_jsonl(generate(args.count, args.seed), args.out)


if __name__ == "__main__":
    main()
