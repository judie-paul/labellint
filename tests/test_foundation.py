"""Foundation contracts: validity, leakage prevention and reproducibility."""

from pathlib import Path

import pytest
from pydantic import ValidationError

from labellint.config import Settings
from labellint.schema import AnnotationRecord, DetectorRecord, GroundTruth
from labellint.synthetic import generate, main, write_jsonl


def test_detector_boundary() -> None:
    record = AnnotationRecord.model_validate(
        generate(1)[0].model_dump()
        | {"ground_truth": GroundTruth(annotator_profile="rusher", is_bad=True, bad_type="speed")}
    )
    public = record.for_detection()
    assert type(public) is DetectorRecord
    assert not hasattr(public, "ground_truth")
    assert "ground_truth" not in public.model_dump_json()
    with pytest.raises(ValidationError):
        DetectorRecord.model_validate(record.model_dump())


@pytest.mark.parametrize("rating", [0, 6, 2.5, True, "4"])
def test_invalid_ratings(rating: object) -> None:
    with pytest.raises(ValidationError):
        AnnotationRecord.model_validate(generate(1)[0].model_dump() | {"rating": rating})


@pytest.mark.parametrize("duration", [0, -1, float("nan"), float("inf")])
def test_invalid_durations(duration: float) -> None:
    with pytest.raises(ValidationError):
        AnnotationRecord.model_validate(generate(1)[0].model_dump() | {"time_spent_sec": duration})


def test_ground_truth_consistency() -> None:
    with pytest.raises(ValidationError):
        GroundTruth(annotator_profile="diligent", is_bad=True)
    with pytest.raises(ValidationError):
        GroundTruth(annotator_profile="diligent", is_bad=False, bad_type="speed")


def test_settings(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LABELLINT_SEED", "123")
    assert Settings().seed == 123
    assert Settings().provider == "mock"
    with pytest.raises(ValidationError):
        Settings(annotators=2, raters_per_item=3)


def test_byte_identical_generation(tmp_path: Path) -> None:
    first, second = tmp_path / "a.jsonl", tmp_path / "nested/b.jsonl"
    write_jsonl(generate(40, 42), first)
    write_jsonl(generate(40, 42), second)
    assert first.read_bytes() == second.read_bytes()
    assert generate(40, 42) != generate(40, 43)
    assert len({record.record_id for record in generate(40)}) == 40
    assert all(record.ground_truth is None for record in generate(40))
    assert len(first.read_text().splitlines()) == 40


def test_invalid_count() -> None:
    with pytest.raises(ValueError, match="count"):
        generate(0)


def test_generator_command(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    destination = tmp_path / "sample.jsonl"
    monkeypatch.setattr(
        "sys.argv", ["synthetic", "--count", "3", "--seed", "19", "--out", str(destination)]
    )
    main()
    records = [
        AnnotationRecord.model_validate_json(line) for line in destination.read_text().splitlines()
    ]
    assert records == generate(3, 19)
