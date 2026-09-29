"""Read canonical JSONL and CSV without exposing annotation content in errors."""

import csv
import json
from pathlib import Path

from pydantic import ValidationError

from labellint.schema import AnnotationRecord


def load_local(path: Path) -> list[AnnotationRecord]:
    """Load a nonempty canonical file, rejecting malformed rows and duplicate IDs.

    CSV uses the canonical field names and JSON in the optional ground_truth cell.
    Errors include a file and physical line number, but never private row contents.
    """
    suffix = path.suffix.lower()
    if suffix not in {".jsonl", ".csv"}:
        raise ValueError("local input must have a .jsonl or .csv extension")
    records: list[AnnotationRecord] = []
    seen: set[str] = set()

    def append(data: object, line: int) -> None:
        try:
            record = AnnotationRecord.model_validate(data)
        except ValidationError:
            raise ValueError(f"{path}:{line}: invalid annotation record") from None
        if record.record_id in seen:
            raise ValueError(f"{path}:{line}: duplicate record_id")
        seen.add(record.record_id)
        records.append(record)

    with path.open(encoding="utf-8-sig", newline="") as stream:
        if suffix == ".jsonl":
            for line, raw in enumerate(stream, start=1):
                if not raw.strip():
                    continue
                try:
                    data = json.loads(raw)
                except json.JSONDecodeError:
                    raise ValueError(f"{path}:{line}: malformed JSON") from None
                append(data, line)
        else:
            reader = csv.DictReader(stream, strict=True)
            try:
                headers = reader.fieldnames or []
                required = {
                    name
                    for name, field in AnnotationRecord.model_fields.items()
                    if field.is_required()
                }
                if len(headers) != len(set(headers)) or not required.issubset(headers):
                    raise ValueError(f"{path}:1: missing or duplicate CSV columns")
                for row in reader:
                    line = reader.line_num
                    if None in row or any(value is None for value in row.values()):
                        raise ValueError(f"{path}:{line}: incorrect CSV field count")
                    converted: dict[str, object] = dict(row)
                    try:
                        converted["rating"] = int(row["rating"])
                        converted["time_spent_sec"] = float(row["time_spent_sec"])
                        if "ground_truth" in row:
                            converted["ground_truth"] = (
                                json.loads(row["ground_truth"]) if row["ground_truth"] else None
                            )
                    except (ValueError, TypeError):
                        raise ValueError(f"{path}:{line}: invalid CSV value") from None
                    append(converted, line)
            except csv.Error:
                raise ValueError(f"{path}:{reader.line_num}: malformed CSV") from None
    if not records:
        raise ValueError(f"{path}: no annotation records")
    return records
