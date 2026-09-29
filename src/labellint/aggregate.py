"""Transparent record and annotator risk aggregation."""

from pydantic import BaseModel, Field

from labellint.detectors.base import Finding
from labellint.schema import DetectorRecord


class RecordResult(BaseModel):
    """Public record, evidence, combined risk and optional reviewer note."""

    record: DetectorRecord
    risk: float = Field(ge=0, le=1)
    flagged: bool
    findings: list[Finding]
    note: str | None = None


class AnnotatorResult(BaseModel):
    """A worker-level summary; risk is mean record severity, not guilt."""

    annotator_id: str
    records: int
    flagged: int
    risk: float


class ScanReport(BaseModel):
    """Versioned, serializable scan output without simulation labels."""

    schema_version: int = 1
    records: list[RecordResult]
    annotators: list[AnnotatorResult]
    alpha: float | None = None


def aggregate(
    records: list[DetectorRecord], findings: list[Finding], threshold: float
) -> ScanReport:
    """Combine independent evidence by bounded complement product."""
    by_id: dict[str, list[Finding]] = {r.record_id: [] for r in records}
    for finding in findings:
        if finding.record_id not in by_id:
            raise ValueError("finding references an unknown record")
        by_id[finding.record_id].append(finding)
    results = []
    for record in records:
        remaining = 1.0
        for finding in by_id[record.record_id]:
            remaining *= 1 - finding.score
        risk = round(1 - remaining, 6)
        results.append(
            RecordResult(
                record=record,
                risk=risk,
                flagged=risk >= threshold,
                findings=by_id[record.record_id],
            )
        )
    workers = []
    for annotator in sorted({r.annotator_id for r in records}):
        subset = [r for r in results if r.record.annotator_id == annotator]
        workers.append(
            AnnotatorResult(
                annotator_id=annotator,
                records=len(subset),
                flagged=sum(r.flagged for r in subset),
                risk=sum(r.risk for r in subset) / len(subset),
            )
        )
    return ScanReport(records=results, annotators=workers)
