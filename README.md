# LabelLint

[![Quality checks](https://github.com/judie-paul/labellint/actions/workflows/ci.yml/badge.svg)](https://github.com/judie-paul/labellint/actions/workflows/ci.yml)

An offline-first annotation quality audit pipeline with a local review dashboard.
It flags repeated rationales, rating/rationale contradictions, unusual completion
times and disagreement between annotators. Every flag includes reviewer evidence.

The default data and annotators are **synthetic**, generated deterministically to
exercise the workflow without dataset downloads, model weights or API keys.
Results below are a software demonstration, not a real-world accuracy claim.

## Quickstart

With Docker and Compose:

```sh
git clone https://github.com/judie-paul/labellint.git
cd labellint
make docker-up
```

Open **http://localhost:8080** and select **Run sample**, or upload a canonical CSV
or JSONL file. If that port is occupied, use `DASHBOARD_PORT=8081 make docker-up`.
API documentation is at http://localhost:8000/docs. `API_PORT` can also be overridden.

For local Python development, install Python 3.12 and uv:

```sh
make setup
source .venv/bin/activate
make pipeline
make lint typecheck test
make api
```

In a second terminal, `make dashboard` installs Node dependencies and starts Vite
at http://localhost:5173. Node 20.19+ or 22+ is needed. Python 3.11 and 3.12 are
tested in CI; `make setup` selects 3.12. First installation/build needs internet or
prepared package caches. Subsequent default pipeline execution works offline.

## Workflow

```sh
labellint ingest --source synthetic --limit 200 --out data/raw.jsonl
labellint simulate data/raw.jsonl --annotators 50 --raters-per-item 3 --seed 42 --out data/sim.jsonl
labellint scan data/sim.jsonl --detectors all --out reports/scan.json
labellint enrich reports/scan.json --provider mock --out reports/enriched.json
labellint evaluate data/sim.jsonl reports/scan.json --out reports/eval.json
labellint run --config configs/default.yaml
```

The full run writes `raw.jsonl`, `sim.jsonl`, `scan.json`, `eval.json` and `report.md`
to `reports/`. Evaluation includes per-detector and per-corruption metrics,
clean-data false positives, confusion counts and an aggregate risk-threshold sweep.

Settings use `LABELLINT_` environment variables or YAML configuration; see
`.env.example` and `configs/default.yaml`. YAML values override environment defaults.
All randomness passes through a seeded NumPy generator. Ground truth is removed
before detectors run and excluded from public scan records.

## Local records

CSV headers and JSONL keys match this schema:

```json
{"record_id":"example_1","item_id":"item_1","source":"local","prompt":"Explain testing","response":"Tests check expected behavior.","aspect":"helpfulness","annotator_id":"ann_001","rating":4,"rationale":"Clear and accurate.","time_spent_sec":45.0}
```

Optional `ground_truth` is an object with `annotator_profile`, `is_bad` and
`bad_type`; in CSV its cell contains JSON. Ratings must be integers 1-5, times
must be positive and finite, and record IDs must be unique. Simulated sources
must contain one record per item/aspect. Real uploaded data needs no labels to
scan, but evaluation requires labels for every record. Unknown/malformed fields
produce validation errors with file/line context.

```python
from pathlib import Path
from labellint.ingest import load_local
from labellint.pipeline import scan
from labellint.config import Settings

report = scan(load_local(Path("data/annotations.csv")), Settings())
```

## Measured results

Reproduce with `make results`, which runs the pipeline and public evaluation command
for `configs/default.yaml` (seed **42**) and `configs/validation.yaml` (seed **2026**).
Each run has 200 source items, 50 annotators and 600 rating records. Thresholds
are unchanged for the independent validation seed.

| Seed | Precision | Recall | F1 | Clean-data FPR |
|---|---:|---:|---:|---:|
| 42 | 0.7489 | 0.9598 | 0.8413 | 13.1455% |
| 2026 | 0.7250 | 0.9355 | 0.8169 | 12.3596% |

See [full results](docs/results.md) for actual per-detector numbers, confusion counts
and limitations. Agreement is the weakest standalone detector. Duplicate flags can
reflect template reuse, and corrupted peers can cause false accusations. Treat
scores as review priorities, not calibrated probabilities or personnel decisions.

## Optional integrations

```sh
uv pip install -e '.[datasets]'       # Optional HF streaming loader
uv pip install -e '.[embeddings]'     # MiniLM duplicate backend
uv pip install -e '.[nli]'            # NLI contradiction backend
labellint ingest --source ultrafeedback --limit 100 --out data/uf.jsonl
```

Select `duplicate_backend: embeddings` or `contradiction_backend: nli` in YAML.
These integrations need network access or previously cached datasets/models.
The default TF-IDF and lexicon backends do not download models. UltraFeedback
source timings are placeholders that simulation replaces, not measured telemetry.

Reviewer notes default to `mock`. Explicitly select `--provider openai` or
`--provider anthropic` and export the corresponding API key to use a paid provider;
missing keys fall back to mock. SDK calls have timeouts, retry and token limits.
Development and CI use mocks only. `simulate --llm-rationales` enables optional
provider-based paraphrasing with a bounded process-local cache.

## Development and deployment

All requested targets are available: `setup`, `lint`, `format`, `typecheck`, `test`,
`test-slow`, `ingest`, `simulate`, `detect`, `evaluate`, `pipeline`, `api`, `dashboard`,
`docker-build`, `docker-up` and `clean`. `results` regenerates published metrics.
`test-slow` succeeds with no selected tests until real-model tests are added; default
coverage is based on mocked optional-backend contracts, not downloaded models.

CI checks Python 3.11/3.12, coverage >=80%, distribution metadata, frontend format
and build, desktop/mobile browser workflows, and Docker compose startup. Main is
protected; work is merged through reviewed PRs with required checks.

The v1 web app is a **local, single-process tool**: job history is in memory and
clears on restart. Export results to retain them. Limits are 2 MiB, 2,000 records
per upload, two active jobs, and 100 stored jobs. There is no authentication or
multi-worker persistence; do not expose it as a public multi-user service.

See [architecture](docs/architecture.md), [demo workflow](docs/demo.md),
[progress](PROGRESS.md) and [contributing](CONTRIBUTING.md). Licensed under MIT.
