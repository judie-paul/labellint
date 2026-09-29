"""Generate published result tables directly from reproducible pipeline runs."""

from pathlib import Path

import yaml

from labellint.cli import app
from labellint.config import Settings
from labellint.pipeline import run


def main() -> None:
    """Write default and independent-seed results without estimating any numbers."""
    reports = []
    for config in ("configs/default.yaml", "configs/validation.yaml"):
        settings = Settings(**yaml.safe_load(Path(config).read_text(encoding="utf-8")))
        reports.append((settings, run(settings)))
    lines = [
        "# Reproducible synthetic results",
        "",
        "These measurements use templated synthetic data and simulated annotators, "
        "not human workers.",
        "Each run has 200 source items, 50 annotators and three raters per item (600 records).",
        "The validation seed was not used to select thresholds. "
        "Defaults are unchanged between runs.",
        "",
        "Reproduce with `make results`, or run the CLI commands:",
        "",
        "```sh",
        "labellint run --config configs/default.yaml",
        "labellint evaluate reports/sim.jsonl reports/scan.json --out reports/eval.json",
        "labellint run --config configs/validation.yaml",
        "labellint evaluate reports/validation/sim.jsonl reports/validation/scan.json "
        "--out reports/validation/eval.json",
        "```",
        "",
    ]
    for settings, report in reports:
        seed, out = settings.seed, settings.output_dir
        # Exercise the same public evaluate command documented above.
        app(
            ["evaluate", f"{out}/sim.jsonl", f"{out}/scan.json", "--out", f"{out}/eval.json"],
            standalone_mode=False,
        )
        lines += [
            f"## Seed {seed}",
            "",
            "| Detector | Precision | Recall | F1 |",
            "|---|---:|---:|---:|",
        ]
        for name, metric in {**report["per_detector"], "Combined": report["overall"]}.items():
            lines.append(
                f"| {name} | {metric['precision']:.4f} | {metric['recall']:.4f} "
                f"| {metric['f1']:.4f} |"
            )
        metric = report["overall"]
        lines += [
            "",
            f"Clean-data false-positive rate: **{metric['false_positive_rate']:.4%}**.",
            f"Confusion counts: TP={metric['tp']}, FP={metric['fp']}, "
            f"FN={metric['fn']}, TN={metric['tn']}.",
            "",
        ]
    lines += [
        "## Interpretation",
        "",
        "Agreement is the weakest standalone baseline: corrupted peers and",
        "rating noise make consensus unreliable. Duplicate precision is limited by source-template",
        "reuse and short rusher rationales. Cross-detector overlap means per-detector scores",
        "should not be interpreted as overall audit performance. False positives remain material.",
        "",
        "`eval.json` also contains per-corruption metrics against clean controls "
        "and a risk-threshold",
        "sweep. Most baseline severity scores are binary, so changing the aggregate threshold",
        "can leave predictions unchanged. Zero metric denominators return zero. No real-world",
        "accuracy claim or paid-model evaluation is made.",
        "",
    ]
    Path("docs").mkdir(exist_ok=True)
    Path("docs/results.md").write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    main()
