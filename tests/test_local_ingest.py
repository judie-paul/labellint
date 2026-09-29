"""Local file contracts including malformed data and private error contents."""

import csv
import json
from pathlib import Path

import pytest

from labellint.ingest import load_local
from labellint.schema import GroundTruth
from labellint.synthetic import generate, write_jsonl


def test_jsonl_round_trip(tmp_path: Path) -> None:
    records = generate(8)
    path = tmp_path / "records.jsonl"
    write_jsonl(records, path)
    assert load_local(path) == records


@pytest.mark.parametrize("with_truth", [False, True])
def test_csv_round_trip(tmp_path: Path, with_truth: bool) -> None:
    record = generate(1)[0]
    if with_truth:
        record = record.model_copy(
            update={"ground_truth": GroundTruth(annotator_profile="diligent", is_bad=False)}
        )
    row = record.model_dump()
    row["ground_truth"] = json.dumps(row["ground_truth"]) if with_truth else ""
    path = tmp_path / "records.csv"
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(row))
        writer.writeheader()
        writer.writerow(row)
    assert load_local(path) == [record]


def test_jsonl_bom_and_blank_lines(tmp_path: Path) -> None:
    record = generate(1)[0]
    path = tmp_path / "records.jsonl"
    path.write_text("\ufeff\n" + record.model_dump_json() + "\n\n", encoding="utf-8")
    assert load_local(path) == [record]


@pytest.mark.parametrize(
    ("content", "message"),
    [("{broken", "malformed JSON"), ("[]", "invalid annotation"), ("\n", "no annotation")],
)
def test_invalid_jsonl(tmp_path: Path, content: str, message: str) -> None:
    path = tmp_path / "invalid.jsonl"
    path.write_text(content)
    with pytest.raises(ValueError, match=message):
        load_local(path)


def test_duplicate_and_error_privacy(tmp_path: Path) -> None:
    path = tmp_path / "records.jsonl"
    record = generate(1)[0]
    write_jsonl([record, record], path)
    with pytest.raises(ValueError, match=":2: duplicate record_id"):
        load_local(path)
    invalid = record.model_dump() | {"rating": "private-invalid-value"}
    path.write_text(json.dumps(invalid))
    with pytest.raises(ValueError) as error:
        load_local(path)
    assert "private-invalid-value" not in str(error.value)
    assert ":1:" in str(error.value)


@pytest.mark.parametrize("headers", ["rating\n", "rating,rating\n"])
def test_csv_headers(tmp_path: Path, headers: str) -> None:
    path = tmp_path / "records.csv"
    path.write_text(headers)
    with pytest.raises(ValueError, match="missing or duplicate CSV columns"):
        load_local(path)


@pytest.mark.parametrize("value", ["2.5", "bad", "", "6"])
def test_csv_rating_validation(tmp_path: Path, value: str) -> None:
    row = generate(1)[0].model_dump(exclude={"ground_truth"}) | {"rating": value}
    path = tmp_path / "records.csv"
    with path.open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(row))
        writer.writeheader()
        writer.writerow(row)
    with pytest.raises(ValueError, match=":2:"):
        load_local(path)


def test_missing_file_and_extension(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        load_local(tmp_path / "missing.jsonl")
    with pytest.raises(ValueError, match="extension"):
        load_local(tmp_path / "unsupported.txt")
