# LabelLint implementation plan

## Scope and working agreement

Build an offline-first annotation quality auditing pipeline and local review app.
Track milestones through issues and pull requests in judie-paul/labellint.
Package publication and release tagging are gated on release readiness.
Use focused changes, real measurements, mocked external integrations and reproducible runs.

## Milestone 1: foundation

- Package with hatchling, Python 3.11+ support, environment settings and canonical schema.
- Dedicated detector input type that cannot carry ground truth.
- Seeded NumPy synthetic source, stable JSONL output and meaningful contract tests.
- Ruff, mypy, pytest coverage, Makefile, repository standards and Python 3.11/3.12 CI.
- Gate: installation, lint, typing, tests and sample generation pass.

## Milestone 2: ingestion and simulation

- CSV/JSONL readers with line-level validation errors; normalize all sources.
- UltraFeedback mapping using a committed nested fixture; optional lazy datasets import.
- Fifty-annotator pool with specified profile shares, three distinct raters per item,
  word-count-scaled log-normal durations and explicit per-event corruption labels.
- Test deterministic bytes, rounding of profile shares, rating bounds, overlap and
  whether each actual corruption agrees with its label. Keep clean source rationale
  variety high enough to avoid accidental duplicate ground truth.
- Gate: local and synthetic data flow into the same schema without network calls.

## Milestone 3: detection and evaluation

- Common interface accepting only reconstructed DetectorRecord instances.
- TF-IDF/nearest-neighbor duplicates with configurable threshold and no self-matches;
  distinguish expected shared-item rationales from suspicious repeated work.
- Lexicon contradiction baseline with neutral and negation handling.
- Speed anomalies normalized for response length; robust handling of tiny/constant groups.
- Agreement by item AND aspect, consensus deviation and Krippendorff alpha with undefined
  cases represented explicitly. Do not conflate annotator bias with isolated mistakes.
- Bounded record/annotator risk aggregation with transparent component evidence.
- Precision, recall, F1 per detector and corruption type, clean-data FPR and threshold sweep.
  Tune on a separate seed from evaluation; define zero-denominator semantics.
- Optional embedding and NLI extras, lazy loading, mocked contracts and actionable errors.
- Gate: planted anomalies and clean edge cases pass; no labels enter detector calculations.

## Milestone 4: usable pipeline

- Typer ingest/simulate/scan/enrich/evaluate/run commands and YAML configuration.
- JSON/Markdown reports and reproducible full sample run; implement remaining Make targets.
- Mock enrichment first, then bounded retries/timeouts/token limits for SDK providers,
  tested exclusively with mocks. Never issue real paid API calls during development.
- Optional cached rationale generation with provider/version/inputs in cache keys.
- Integration tests for stage handoffs, unknown IDs, duplicate IDs and invalid files.
- Gate: make pipeline works without network or keys after dependencies are installed.
  This is the candidate v0.1.0 product milestone, not a published release.

## Milestone 5: API and dashboard

- FastAPI upload, bounded input size, validated records, background jobs and result endpoints.
- Explicit queued/running/completed/failed states; isolated job storage and error responses.
- React/Vite/TypeScript with Recharts: upload, job state, flagged table with filters,
  record evidence, annotator detail and evaluation charts, including empty/error states.
- API TestClient coverage; dashboard build and browser checks on desktop/mobile.
- Gate: upload through review works end to end; start a local server for user review.

## Milestone 6: distribution and release readiness

- Multi-stage Dockerfile, compose, container/build CI, all documented Make targets.
- Repository templates, contributing guide, MIT license, code of conduct and pre-commit hooks.
- Architecture diagram and results generated only from actual evaluation output, with
  seed/config/command and limitations recorded alongside every table.
- Check wheel/sdist with build and twine, clean-install smoke test, >=80% core coverage.
- Version/changelog updates only when corresponding acceptance gates pass.
- Once publication is authorized and a remote is available: focused branches/issues/PRs,
  passing CI, reviewed merges and v0.1.0/v1.0.0 release records as appropriate.

## Constraints and decisions

- Keep main protected and preserve shared commit history.
- Keep dependencies incremental; add the specified frameworks when their stages arrive.
- Missing external services must not block local work. CI configuration is not evidence
  that CI has run; report local and remote validation separately.
- A production service will need authentication, persistence and deployment policy beyond
  the local demo. Do not imply a local background-task prototype provides these guarantees.
