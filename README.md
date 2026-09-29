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
