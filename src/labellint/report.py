"""Stable machine-readable and human-readable audit reports."""

import json
from pathlib import Path
from typing import Any

from labellint.aggregate import ScanReport


def write_json(data: Any, path: Path) -> None:
    """Serialize JSON without NaN and with stable key order."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(data, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8"
    )


def markdown(scan: ScanReport) -> str:
    """Summarize aggregate results without embedding private annotation text."""
    lines = [
        "# LabelLint audit",
        "",
        f"Records: {len(scan.records)}",
        f"Flagged: {sum(r.flagged for r in scan.records)}",
        f"Ordinal alpha: {scan.alpha}",
        "",
        "| Annotator | Records | Flagged | Mean risk |",
        "|---|---:|---:|---:|",
    ]
    for worker in scan.annotators:
        safe_id = worker.annotator_id.replace("|", "\\|").replace("\n", " ")
        lines.append(f"| {safe_id} | {worker.records} | {worker.flagged} | {worker.risk:.3f} |")
    return "\n".join(lines) + "\n"
