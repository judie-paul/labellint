"""Composable offline audit stages."""

from typing import Any

from labellint.aggregate import ScanReport, aggregate
from labellint.config import Settings
from labellint.detectors.agreement import AgreementDetector, reliability
from labellint.detectors.base import Detector
from labellint.detectors.contradiction import ContradictionDetector
from labellint.detectors.duplicate import DuplicateDetector
from labellint.detectors.speed import SpeedDetector
from labellint.evaluate import evaluate
from labellint.report import markdown, write_json
from labellint.schema import AnnotationRecord
from labellint.simulate import simulate
from labellint.synthetic import generate, write_jsonl


def scan(records: list[AnnotationRecord], settings: Settings, detectors: str = "all") -> ScanReport:
    """Strip labels before any detector can observe the input."""
    available: dict[str, Detector] = {
        "duplicate": DuplicateDetector(settings.duplicate_threshold, settings.duplicate_backend),
        "contradiction": ContradictionDetector(settings.contradiction_backend),
        "speed": SpeedDetector(settings.speed_z),
        "agreement": AgreementDetector(settings.agreement_gap),
    }
    selected = list(available) if detectors == "all" else detectors.split(",")
    if not selected or any(name not in available for name in selected):
        raise ValueError("unknown detector; use all or comma-separated detector names")
    public = [r.for_detection() for r in records]
    findings = [f for name in dict.fromkeys(selected) for f in available[name].detect(public)]
    result = aggregate(public, findings, settings.risk_threshold)
    result.alpha = reliability(public)
    return result


def run(settings: Settings) -> dict[str, Any]:
    """Run synthetic generation through evaluation and persist reproducible artifacts."""
    raw = generate(settings.items, settings.seed)
    records = simulate(raw, settings)
    result = scan(records, settings)
    from labellint.llm.enrich import enrich

    result = enrich(result, settings.provider)
    evaluation = evaluate(records, result)
    evaluation["seed"] = settings.seed
    evaluation["settings"] = settings.model_dump(mode="json")
    out = settings.output_dir
    write_jsonl(raw, out / "raw.jsonl")
    write_jsonl(records, out / "sim.jsonl")
    write_json(result.model_dump(mode="json"), out / "scan.json")
    write_json(evaluation, out / "eval.json")
    (out / "report.md").write_text(markdown(result), encoding="utf-8")
    return evaluation
