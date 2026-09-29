"""Apply one explicit primary corruption per annotation event."""

import numpy as np

from labellint.config import Settings
from labellint.schema import AnnotationRecord, BadType, GroundTruth
from labellint.simulate.profiles import profile_pool


def simulate(records: list[AnnotationRecord], settings: Settings) -> list[AnnotationRecord]:
    """Assign distinct raters per item/aspect and reproducible behavioral profiles."""
    keys = [(r.item_id, r.aspect) for r in records]
    if len(keys) != len(set(keys)):
        raise ValueError("simulation requires one source record per item and aspect")
    rng = np.random.default_rng(settings.seed)
    profiles = profile_pool(settings.annotators, rng)
    directions = rng.choice([-1, 1], settings.annotators)
    output = []
    for source in records:
        for index in rng.choice(settings.annotators, settings.raters_per_item, replace=False):
            profile = profiles[int(index)]
            annotator = f"ann_{index:03d}"
            rating = source.rating
            rationale = source.rationale
            duration = float(rng.lognormal(np.log(max(20, len(source.response.split()) * 3)), 0.3))
            bad: BadType | None = None
            if profile == "diligent":
                rating += int(rng.choice([-1, 0, 1], p=[0.1, 0.8, 0.1]))
            elif profile == "rusher":
                rating = int(rng.choice([2, 3, 4], p=[0.15, 0.7, 0.15]))
                duration *= 0.08
                rationale, bad = "Looks fine.", "speed"
            elif profile == "copy_paster":
                rationale = (
                    "The response addresses the request with sufficient detail."
                    if int(index) % 2
                    else "The answer is acceptable and covers the main points."
                )
                bad = "duplicate"
            elif profile == "random_clicker":
                rating = int(rng.integers(1, 6))
                bad = "agreement" if abs(rating - source.rating) >= 2 else None
            elif profile == "biased":
                rating = int(np.clip(rating + int(directions[index]) * 2, 1, 5))
                bad = "agreement" if abs(rating - source.rating) >= 2 else None
            rating = int(np.clip(rating, 1, 5))
            if (
                profile == "diligent"
                and source.rating != 3
                and rng.random() < settings.contradiction_rate
            ):
                rating = 1 if source.rating >= 4 else 5
                bad = "contradiction"
            if settings.llm_rationales and profile == "copy_paster":
                from labellint.llm.enrich import paraphrase

                rationale = paraphrase(rationale, settings.provider)
            output.append(
                AnnotationRecord.model_validate(
                    source.model_dump()
                    | {
                        "record_id": f"{source.record_id}_{annotator}",
                        "annotator_id": annotator,
                        "rating": rating,
                        "rationale": rationale,
                        "time_spent_sec": round(duration, 6),
                        "ground_truth": GroundTruth(
                            annotator_profile=profile, is_bad=bad is not None, bad_type=bad
                        ),
                    }
                )
            )
    return output
