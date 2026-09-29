# Progress

## Current phase

Milestone 2: local file ingestion, followed by annotator simulation.

## Completed PRs

- #2: repository standards and roadmap (merged; closes #1).
- #4: Python foundation and CI (merged; closes #3). Both Python matrix jobs passed.
- Current branch: feat/local-ingestion, tracking issue #5.

## Implemented

- Full phased implementation plan in PLAN.md.
- Python package, environment configuration, schema and detector-safe projection.
- Deterministic synthetic source and JSONL writer.
- Foundation tests and local quality commands.
- MIT license, contributor guidance, issue/PR templates and pre-commit configuration.
- Python 3.11/3.12 CI, verified remotely on PR #4.
- Local JSONL/CSV ingestion with row context and duplicate-ID validation.

## Validation

- Installed editable package and development dependencies in .venv with Python 3.12.12.
- `make lint typecheck test ingest` passes locally.
- 15 tests passed; current package coverage is 98.70%.
- Generated 100 records with seed 42 in data/raw.jsonl (ignored generated output).
- Same-seed byte identity, label stripping, invalid inputs and generator command tested.
- NumPy constrained to >=1.26,<2.3 after newer stubs failed Python 3.11 typing.
- Python 3.11 and 3.12 CI passed tests, typing, lint and package checks for PR #4.
- Isolated wheel/sdist builds and twine validation passed locally as well.
- Ingestion verification: `make lint typecheck test` passes; 30 tests, 97.74% coverage.
- Pre-commit execution is not yet verified.

## Next work

Finish the local ingestion PR, then add fixture-based optional HF mapping and simulation.
The source generator is intentionally small; expand templates before evaluating detectors.

## Constraints

- Repository created: https://github.com/judie-paul/labellint
- Git initialized and origin configured; standards and foundation merged through PRs.
- Main requires PRs, passing Python 3.11/3.12 checks and resolved conversations.
- Force pushes and deletion of main are blocked, including for administrators.
- No release tags or packages have been published.
- Python 3.12 is available via uv; default system Python is 3.14.
- Full pipeline, detectors, evaluation, API, dashboard and containers remain planned.
