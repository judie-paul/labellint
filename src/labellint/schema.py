"""Validated records and the explicit detector data boundary."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

Profile = Literal["diligent", "rusher", "copy_paster", "random_clicker", "biased"]
BadType = Literal["duplicate", "contradiction", "speed", "agreement"]


class GroundTruth(BaseModel):
    """Simulation labels available only to evaluation."""

    model_config = ConfigDict(extra="forbid", frozen=True)
    annotator_profile: Profile
    is_bad: bool
    bad_type: BadType | None = None

    @model_validator(mode="after")
    def consistent_label(self) -> "GroundTruth":
        """Require a corruption type exactly when the event is bad."""
        if self.is_bad != (self.bad_type is not None):
            raise ValueError("is_bad must match the presence of bad_type")
        return self


class DetectorRecord(BaseModel):
    """Public annotation fields; ground truth is forbidden."""

    model_config = ConfigDict(extra="forbid", frozen=True, allow_inf_nan=False)
    record_id: str = Field(min_length=1)
    item_id: str = Field(min_length=1)
    source: str = Field(min_length=1)
    prompt: str = Field(min_length=1)
    response: str = Field(min_length=1)
    aspect: str = Field(min_length=1)
    annotator_id: str = Field(min_length=1)
    rating: int = Field(ge=1, le=5, strict=True)
    rationale: str = Field(min_length=1)
    time_spent_sec: float = Field(gt=0)


class AnnotationRecord(DetectorRecord):
    """Canonical input, optionally carrying simulation labels."""

    ground_truth: GroundTruth | None = None

    def for_detection(self) -> DetectorRecord:
        """Reconstruct the exact public type without evaluation-only fields."""
        return DetectorRecord.model_validate(self.model_dump(exclude={"ground_truth"}))
