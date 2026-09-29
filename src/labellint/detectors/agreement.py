"""Leave-one-out consensus and ordinal inter-rater reliability."""

from collections import defaultdict

import krippendorff
import numpy as np

from labellint.detectors.base import Finding, validate_inputs
from labellint.schema import DetectorRecord


class AgreementDetector:
    """Only compare independent raters of the same item and aspect."""

    def __init__(self, gap: float = 2.0) -> None:
        self.gap = gap

    def detect(self, records: list[DetectorRecord]) -> list[Finding]:
        """Require two peers and compare to their median rating."""
        validate_inputs(records)
        groups: dict[tuple[str, str], list[DetectorRecord]] = defaultdict(list)
        for record in records:
            groups[record.item_id, record.aspect].append(record)
        findings = []
        for group in groups.values():
            if len({r.annotator_id for r in group}) != len(group):
                raise ValueError("repeated annotator for item/aspect")
            for record in group:
                peers = [r.rating for r in group if r.annotator_id != record.annotator_id]
                if len(peers) >= 2 and abs(record.rating - float(np.median(peers))) >= self.gap:
                    findings.append(
                        Finding(
                            record_id=record.record_id,
                            detector="agreement",
                            score=1,
                            reason=(
                                f"Rating {record.rating} differs from peer median "
                                f"{np.median(peers):.1f}"
                            ),
                        )
                    )
        return findings


def reliability(records: list[DetectorRecord]) -> float | None:
    """Return ordinal alpha, or null when overlap/variation is insufficient."""
    validate_inputs(records)
    groups: dict[tuple[str, str], list[int]] = defaultdict(list)
    for r in records:
        groups[r.item_id, r.aspect].append(r.rating)
    rows = [[values.count(rating) for rating in range(1, 6)] for values in groups.values()]
    if not rows or sum(sum(row) >= 2 for row in rows) == 0:
        return None
    try:
        result = float(
            krippendorff.alpha(
                value_counts=np.asarray(rows),
                value_domain=np.arange(1, 6),
                level_of_measurement="ordinal",
            )
        )
    except ValueError:
        return None
    return result if np.isfinite(result) else None
