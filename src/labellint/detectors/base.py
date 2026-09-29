"""Typed detector contracts and the enforced evaluation-label boundary."""

from typing import Literal, Protocol

from pydantic import BaseModel, ConfigDict, Field

from labellint.schema import DetectorRecord

DetectorName = Literal["duplicate", "contradiction", "speed", "agreement"]


class Finding(BaseModel):
    """An actionable detector observation with normalized severity."""

    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)
    record_id: str
    detector: DetectorName
    score: float = Field(ge=0, le=1)
    reason: str


class Detector(Protocol):
    """Every backend accepts only detector-safe records."""

    def detect(self, records: list[DetectorRecord]) -> list[Finding]: ...


def validate_inputs(records: list[DetectorRecord]) -> None:
    """Reject annotated subclasses as well as duplicate IDs before detection."""
    if any(type(record) is not DetectorRecord for record in records):
        raise TypeError("detectors require exact DetectorRecord inputs without ground truth")
    if len({r.record_id for r in records}) != len(records):
        raise ValueError("duplicate record IDs")
