# Contributing

Run `make setup`, then `make lint typecheck test` before proposing a change.
Use small branches named `feat/`, `fix/`, `docs/`, `test/`, `ci/` or `chore/`
and Conventional Commits such as `feat(schema): validate annotation ratings`.
Keep main releasable; do not force-push or rewrite shared history.

Track each substantial unit of work with an issue,
include acceptance criteria, and reference it in a pull request. Review the diff
and require passing checks before merging. Update CHANGELOG.md and PROGRESS.md.
Publication and release activity must follow the repository owner's chosen workflow.

Use seeded NumPy generators for all randomness. Detectors accept DetectorRecord,
never AnnotationRecord; reconstruct inputs with `for_detection()` before dispatch.
Mock downloads, model initialization and API clients in default tests.
Never commit keys, data exports, model weights or invented evaluation results.
