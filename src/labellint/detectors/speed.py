"""Word-count-normalized log-time anomalies."""

from collections import defaultdict

import numpy as np
from scipy.stats import zscore

from labellint.detectors.base import Finding, validate_inputs
from labellint.schema import DetectorRecord


class SpeedDetector:
    """Compare global and within-annotator completion times, avoiding zero variance."""

    def __init__(self, threshold: float = 2.0) -> None:
        self.threshold = threshold

    def detect(self, records: list[DetectorRecord]) -> list[Finding]:
        """Flag unusually short times; small groups alone are insufficient evidence."""
        validate_inputs(records)
        if len(records) < 3:
            return []
        values = np.log([r.time_spent_sec / max(7, len(r.response.split())) for r in records])
        global_z = zscore(values) if float(values.std()) > 1e-9 else np.zeros(len(records))
        local_z = np.zeros(len(records))
        groups: dict[str, list[int]] = defaultdict(list)
        for i, record in enumerate(records):
            groups[record.annotator_id].append(i)
        for indices in groups.values():
            if len(indices) >= 3 and float(values[indices].std()) > 1e-9:
                local_z[indices] = zscore(values[indices])
        return [
            Finding(
                record_id=r.record_id,
                detector="speed",
                score=1.0,
                reason=(
                    f"Normalized log-time z: global={global_z[i]:.2f}, annotator={local_z[i]:.2f}"
                ),
            )
            for i, r in enumerate(records)
            if min(global_z[i], local_z[i]) <= -self.threshold
        ]
