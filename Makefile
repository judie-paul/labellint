PYTHON ?= .venv/bin/python

.PHONY: setup lint format typecheck test test-slow ingest simulate detect evaluate pipeline results api dashboard docker-build docker-up clean
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
	$(PYTHON) -m pytest -m slow --no-cov; code=$$?; test $$code -eq 0 -o $$code -eq 5
ingest:
	$(PYTHON) -m labellint.cli ingest --limit 200 --out data/raw.jsonl
simulate: ingest
	$(PYTHON) -m labellint.cli simulate data/raw.jsonl --out data/sim.jsonl
detect: simulate
	$(PYTHON) -m labellint.cli scan data/sim.jsonl --out reports/scan.json
evaluate: detect
	$(PYTHON) -m labellint.cli evaluate data/sim.jsonl reports/scan.json --out reports/eval.json
pipeline:
	$(PYTHON) -m labellint.cli run --config configs/default.yaml
results:
	$(PYTHON) scripts/results.py
api:
	$(PYTHON) -m uvicorn labellint.api:app --host 127.0.0.1 --port 8000
dashboard:
	npm --prefix dashboard ci
	npm --prefix dashboard run dev -- --host 127.0.0.1
docker-build:
	docker compose build
docker-up:
	docker compose up --build
clean:
	rm -rf .pytest_cache .mypy_cache .ruff_cache htmlcov build dist
