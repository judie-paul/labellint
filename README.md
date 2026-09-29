# LabelLint

An offline-first pipeline for auditing annotation quality in AI training data.
Under development: the current foundation provides validated records, configuration,
an explicit ground-truth boundary, and a deterministic synthetic source generator.

## Start locally

Requires Python 3.11+ and uv; the setup target selects Python 3.12.

```sh
make setup
make lint typecheck test
make ingest
```

The sample is written to `data/raw.jsonl`. Source records have no corruption labels;
the planned simulator will apply corruptions and record their ground truth.
These are templated synthetic examples, not human annotations or a real dataset.
No detector accuracy claims are available yet.

Dependency installation needs a package index or a populated local cache. Runtime
generation needs no network, credentials, or downloaded models. A fresh machine
cannot install uncached dependencies offline; offline distribution is a later milestone.

See [PLAN.md](PLAN.md) for the full implementation sequence and [PROGRESS.md](PROGRESS.md)
for the current state. The API, dashboard, detectors and full CLI are not implemented yet.

## Local data

Load canonical JSONL or CSV using the Python API:

```python
from pathlib import Path
from labellint.ingest import load_local

records = load_local(Path("data/raw.jsonl"))
detector_inputs = [record.for_detection() for record in records]
```

CSV headers use the canonical schema names. The optional `ground_truth` column
contains JSON or an empty cell. Invalid rows and duplicate record IDs are rejected
with file and line context; row contents are excluded from error messages.
