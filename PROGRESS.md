# Progress

## Implementation status

All functional v1 milestones are implemented: ingestion, normalization, simulation,
four detectors, aggregation, mock-first enrichment, evaluation, CLI, API, dashboard,
containers, documentation and release packaging. Final release work is tracked by
issue #11 and its release PR. GitHub is the authority for final merge/tag status.

## Completed PRs

- [#2](https://github.com/judie-paul/labellint/pull/2): repository standards.
- [#4](https://github.com/judie-paul/labellint/pull/4): Python foundation and CI.
- [#6](https://github.com/judie-paul/labellint/pull/6): local CSV/JSONL ingestion.
- [#8](https://github.com/judie-paul/labellint/pull/8): complete offline audit pipeline.
- [#10](https://github.com/judie-paul/labellint/pull/10): review application and containers.

## Verification

- 51 Python tests pass locally with 97.08% core coverage; Ruff and strict mypy pass.
- Optional dataset/model/SDK integrations are fixture/mocked; missing-extra errors tested.
- Four Playwright scenarios cover desktop/mobile audits, uploads, errors, evidence,
  filters, annotators and evaluation charts. Screenshots were inspected.
- Frontend TypeScript/production build and Prettier checks pass.
- Pre-commit hooks pass, including YAML and private-key checks.
- Python 3.11/3.12, browser/dashboard and container checks passed remotely for PR #10.
- Both Docker targets build; default container pipeline runs with `--network none`.
- v1 wheel and source distribution build and pass twine checks.
- The wheel installs into a fresh environment with `uv pip install --offline` using
  the prepared dependency cache; its CLI runs outside the source checkout.
- `make results` regenerates actual evaluations for seeds 42 and 2026. See
  [results](docs/results.md) for tables, reproduction commands and limitations.

## Releases and workflow

- Repository: https://github.com/judie-paul/labellint
- v0.1.0: https://github.com/judie-paul/labellint/releases/tag/v0.1.0
- v1.0.0 is published from the final merged release PR, with wheel/sdist assets.
- Main requires PRs, both Python checks, browser/dashboard checks, container checks
  and resolved conversations. Force pushes and deletion are blocked for administrators too.
- No PyPI publication is performed; GitHub release assets are the distribution channel.

## Operational notes

This is a local single-process review application. Jobs are in memory and reset on
restart; export results to retain them. Uploads and active jobs are bounded. Auth,
multi-worker persistence and real-model accuracy are outside this local v1 scope.
Results use synthetic data and can produce false positives. API TestClient needs
normal thread/event-loop access on this machine; sandboxed runs may stall.

Default ports are 8000/8080; override with API_PORT/DASHBOARD_PORT if occupied.
The local review instance uses dashboard port 8088. Initial setup needs internet
or prepared caches; default execution needs neither network nor keys.

## Completion check

After the final release PR passes and merges, publish v1.0.0 and verify that the
repository has zero open issues and zero open PRs. No implementation work remains
deferred behind placeholder issues.
