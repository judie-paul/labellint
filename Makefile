PYTHON ?= .venv/bin/python

.PHONY: setup lint format typecheck test test-slow ingest clean
setup:
	uv --cache-dir /tmp/labellint-uv-cache venv --python 3.12 .venv
	uv --cache-dir /tmp/labellint-uv-cache pip install --python $(PYTHON) -e '.[dev]'
lint:
	$(PYTHON) -m ruff check .
	$(PYTHON) -m ruff format --check .
format:
	$(PYTHON) -m ruff format .
	$(PYTHON) -m ruff check --fix .
typecheck:
	$(PYTHON) -m mypy
test:
	$(PYTHON) -m pytest -m 'not slow'
test-slow:
	$(PYTHON) -m pytest -m slow --no-cov
ingest:
	$(PYTHON) -m labellint.synthetic --count 100 --seed 42 --out data/raw.jsonl
clean:
	rm -rf .pytest_cache .mypy_cache .ruff_cache htmlcov build dist
