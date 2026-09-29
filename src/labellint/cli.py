"""Composable commands for offline audit workflows."""

import json
import logging
from pathlib import Path
from typing import Annotated

import typer
import yaml

from labellint.aggregate import ScanReport
from labellint.config import Settings
from labellint.evaluate import evaluate as evaluate_records
from labellint.ingest import load_local
from labellint.pipeline import run as run_pipeline
from labellint.pipeline import scan as scan_records
from labellint.report import write_json
from labellint.simulate import simulate as simulate_records
from labellint.synthetic import generate, write_jsonl

app = typer.Typer(no_args_is_help=True, pretty_exceptions_enable=False)
logger = logging.getLogger(__name__)


@app.callback()
def configure() -> None:
    """LabelLint annotation quality auditing."""
    logging.basicConfig(level=logging.INFO, format="%(message)s")


@app.command()
def ingest(source: str = "synthetic", limit: int = 100, out: Path = Path("data/raw.jsonl")) -> None:
    """Generate offline examples, read a local path, or opt into UltraFeedback."""
    if source == "synthetic":
        records = generate(limit)
    elif source == "ultrafeedback":
        from labellint.ingest.huggingface import load_ultrafeedback

        records = load_ultrafeedback(limit)
    else:
        records = load_local(Path(source))[:limit]
    write_jsonl(records, out)
    logger.info("Wrote %d source records to %s", len(records), out)


@app.command()
def simulate(
    path: Path,
    annotators: int = 50,
    raters_per_item: int = 3,
    seed: int = 42,
    out: Path = Path("data/sim.jsonl"),
    llm_rationales: bool = False,
    provider: str = "mock",
) -> None:
    """Apply seeded annotator profiles and record corruption ground truth."""
    settings = Settings.model_validate(
        dict(
            annotators=annotators,
            raters_per_item=raters_per_item,
            seed=seed,
            llm_rationales=llm_rationales,
            provider=provider,
        )
    )
    write_jsonl(simulate_records(load_local(path), settings), out)


@app.command()
def scan(path: Path, detectors: str = "all", out: Path = Path("reports/scan.json")) -> None:
    """Audit annotations without exposing simulation labels to detectors."""
    result = scan_records(load_local(path), Settings(), detectors)
    write_json(result.model_dump(mode="json"), out)


@app.command()
def enrich(path: Path, provider: str = "mock", out: Path = Path("reports/enriched.json")) -> None:
    """Add bounded reviewer notes to flagged records."""
    from labellint.llm.enrich import enrich as enrich_report

    result = enrich_report(ScanReport.model_validate_json(path.read_text()), provider)
    write_json(result.model_dump(mode="json"), out)


@app.command()
def evaluate(path: Path, report: Path, out: Path = Path("reports/eval.json")) -> None:
    """Compare detections against complete simulation labels."""
    result = evaluate_records(load_local(path), ScanReport.model_validate_json(report.read_text()))
    write_json(result, out)


@app.command()
def run(config: Annotated[Path | None, typer.Option()] = None) -> None:
    """Run the entire offline sample pipeline using optional YAML configuration."""
    data = yaml.safe_load(config.read_text()) if config else {}
    if not isinstance(data, dict):
        raise typer.BadParameter("configuration must be a YAML mapping")
    result = run_pipeline(Settings(**data))
    logger.info("Evaluation: %s", json.dumps(result["overall"], sort_keys=True))


if __name__ == "__main__":
    app()
