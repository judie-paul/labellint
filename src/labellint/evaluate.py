"""Ground truth is used here, after detection, and nowhere in detector inputs."""

from typing import Any

from labellint.aggregate import ScanReport
from labellint.schema import AnnotationRecord


def metrics(truth: list[bool], predicted: list[bool]) -> dict[str, float | int]:
    """Compute confusion counts; zero denominators yield zero metrics."""
    pairs = list(zip(truth, predicted, strict=True))
    tp = sum(t and p for t, p in pairs)
    fp = sum(not t and p for t, p in pairs)
    fn = sum(t and not p for t, p in pairs)
    tn = sum(not t and not p for t, p in pairs)
    return {
        "tp": tp,
        "fp": fp,
        "fn": fn,
        "tn": tn,
        "precision": tp / (tp + fp) if tp + fp else 0.0,
        "recall": tp / (tp + fn) if tp + fn else 0.0,
        "f1": 2 * tp / (2 * tp + fp + fn) if 2 * tp + fp + fn else 0.0,
        "false_positive_rate": fp / (fp + tn) if fp + tn else 0.0,
    }


def evaluate(records: list[AnnotationRecord], scan: ScanReport) -> dict[str, Any]:
    """Require exact ID coverage and complete truth instead of silently dropping rows."""
    source = {r.record_id: r for r in records}
    results = {r.record.record_id: r for r in scan.records}
    if (
        len(source) != len(records)
        or len(results) != len(scan.records)
        or source.keys() != results.keys()
    ):
        raise ValueError("evaluation requires unique, matching record IDs")
    if not records or any(r.ground_truth is None for r in records):
        raise ValueError("evaluation requires ground truth for every record")
    truth = [bool(r.ground_truth and r.ground_truth.is_bad) for r in records]
    predicted = [results[r.record_id].flagged for r in records]
    detectors = {}
    corruption = {}
    for name in ("duplicate", "contradiction", "speed", "agreement"):
        target = [bool(r.ground_truth and r.ground_truth.bad_type == name) for r in records]
        detects = [any(f.detector == name for f in results[r.record_id].findings) for r in records]
        detectors[name] = metrics(target, detects)
        # Per-corruption metrics compare that corruption against clean controls only.
        indices = [i for i in range(len(records)) if target[i] or not truth[i]]
        corruption[name] = metrics([target[i] for i in indices], [predicted[i] for i in indices])
    sweep = {
        str(t): metrics(truth, [results[r.record_id].risk >= t for r in records])
        for t in (0.25, 0.5, 0.75, 0.95)
    }
    return {
        "records": len(records),
        "overall": metrics(truth, predicted),
        "per_detector": detectors,
        "per_corruption": corruption,
        "threshold_sweep": sweep,
    }
