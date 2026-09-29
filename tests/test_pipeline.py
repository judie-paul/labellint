"""Behavioral tests for simulation, detector evidence and evaluation contracts."""

import json
from collections import Counter
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock

import numpy as np
import pytest
from typer.testing import CliRunner

from labellint.aggregate import aggregate
from labellint.cli import app
from labellint.config import Settings
from labellint.detectors.agreement import AgreementDetector, reliability
from labellint.detectors.contradiction import ContradictionDetector, sentiment
from labellint.detectors.duplicate import DuplicateDetector
from labellint.detectors.speed import SpeedDetector
from labellint.evaluate import evaluate, metrics
from labellint.ingest.huggingface import load_ultrafeedback
from labellint.normalize import ultrafeedback
from labellint.pipeline import run, scan
from labellint.schema import DetectorRecord
from labellint.simulate import simulate
from labellint.simulate.profiles import profile_pool
from labellint.synthetic import generate, write_jsonl


def public(**changes: object) -> DetectorRecord:
    return DetectorRecord.model_validate(generate(1)[0].for_detection().model_dump() | changes)


def test_profiles_and_simulation() -> None:
    pool = profile_pool(50, np.random.default_rng(42))
    assert Counter(pool) == {
        "diligent": 35,
        "rusher": 4,
        "copy_paster": 4,
        "random_clicker": 4,
        "biased": 3,
    }
    raw = generate(100)
    result = simulate(raw, Settings())
    assert result == simulate(raw, Settings())
    assert result != simulate(raw, Settings(seed=43))
    assert len(result) == 300
    assert len({r.record_id for r in result}) == 300
    assert all(sum(r.item_id == source.item_id for r in result) == 3 for source in raw)
    assert {r.ground_truth.bad_type for r in result if r.ground_truth} >= {
        "duplicate",
        "speed",
        "agreement",
        "contradiction",
        None,
    }
    with pytest.raises(ValueError):
        simulate([raw[0], raw[0]], Settings())
    with pytest.raises(ValueError):
        profile_pool(0, np.random.default_rng(1))


@pytest.mark.parametrize(
    "detector", [DuplicateDetector(), ContradictionDetector(), SpeedDetector(), AgreementDetector()]
)
def test_detector_label_boundary(detector: object) -> None:
    with pytest.raises(TypeError, match="without ground truth"):
        detector.detect(generate(3))  # type: ignore[attr-defined]


def test_duplicate_excludes_self_and_same_item() -> None:
    a = public(record_id="a", rationale="This explanation is clear and helpful")
    b = public(record_id="b", rationale=a.rationale)
    assert DuplicateDetector().detect([a, b]) == []
    b = b.model_copy(update={"item_id": "different"})
    assert len(DuplicateDetector().detect([a, b])) == 2
    assert DuplicateDetector().detect([a]) == []
    assert (
        DuplicateDetector().detect(
            [a.model_copy(update={"rationale": "!"}), b.model_copy(update={"rationale": "?"})]
        )
        == []
    )


def test_contradiction_and_negation() -> None:
    assert sentiment("not helpful or accurate") < 0
    assert sentiment("not helpful, but clear and accurate") > 0
    result = ContradictionDetector().detect(
        [
            public(record_id="a", rating=1, rationale="Excellent and helpful"),
            public(record_id="b", rating=5, rationale="Not helpful"),
            public(record_id="c", rating=3, rationale="Poor"),
            public(record_id="d", rating=5, rationale="Clear and helpful"),
        ]
    )
    assert {r.record_id for r in result} == {"a", "b"}


def test_speed_constant_small_and_outlier() -> None:
    detector = SpeedDetector()
    assert detector.detect([public()]) == []
    records = [public(record_id=str(i), time_spent_sec=100) for i in range(20)]
    assert detector.detect(records) == []
    records[-1] = records[-1].model_copy(update={"time_spent_sec": 1})
    assert [f.record_id for f in detector.detect(records)] == ["19"]


def test_agreement_aspects_and_reliability() -> None:
    records = [
        public(record_id=str(i), annotator_id=str(i), rating=5 if i < 2 else 1) for i in range(3)
    ]
    assert [f.record_id for f in AgreementDetector(gap=3).detect(records)] == ["2"]
    assert reliability([]) is None
    assert reliability([records[0]]) is None
    assert reliability(records) is not None
    records[2] = records[2].model_copy(update={"aspect": "honesty"})
    assert AgreementDetector().detect(records) == []


def test_metrics_and_evaluation_validation() -> None:
    assert metrics([True, False, True, False], [True, True, False, False])["f1"] == 0.5
    assert metrics([], [])["f1"] == 0
    records = simulate(generate(20), Settings())
    report = scan(records, Settings())
    result = evaluate(records, report)
    assert result["records"] == 60
    assert 0 <= result["overall"]["f1"] <= 1
    assert "ground_truth" not in report.model_dump_json()
    with pytest.raises(ValueError, match="matching"):
        evaluate(records[:-1], report)
    with pytest.raises(ValueError, match="ground truth"):
        evaluate(generate(1), scan(generate(1), Settings()))
    with pytest.raises(ValueError, match="unknown detector"):
        scan(records, Settings(), "bad")
    assert aggregate([], [], 0.5).records == []


def test_optional_models_mocked(monkeypatch: pytest.MonkeyPatch) -> None:
    module = SimpleNamespace(SentenceTransformer=MagicMock(), CrossEncoder=MagicMock())
    module.SentenceTransformer.return_value.encode.return_value = np.array([[1.0, 0.0], [1.0, 0.0]])
    module.CrossEncoder.return_value.predict.return_value = [[0.9, 0.05, 0.05], [0.1, 0.8, 0.1]]
    monkeypatch.setitem(__import__("sys").modules, "sentence_transformers", module)
    records = [
        public(record_id="a", item_id="a", rating=5),
        public(record_id="b", item_id="b", rating=1),
    ]
    assert len(DuplicateDetector(backend="embeddings").detect(records)) == 2
    assert len(ContradictionDetector("nli").detect(records)) == 1


def test_huggingface_fixture(monkeypatch: pytest.MonkeyPatch) -> None:
    fixture = json.loads(Path("tests/fixtures/ultrafeedback.json").read_text())
    expected = ultrafeedback(fixture[0], 0)
    loader = MagicMock()
    loader.return_value.take.return_value = fixture
    monkeypatch.setitem(__import__("sys").modules, "datasets", SimpleNamespace(load_dataset=loader))
    assert load_ultrafeedback(1) == expected
    assert len(expected) == 3
    assert len({r.record_id for r in expected}) == 3


def test_pipeline_and_cli(tmp_path: Path) -> None:
    settings = Settings(items=15, output_dir=tmp_path / "reports")
    first = run(settings)
    bytes_before = (settings.output_dir / "scan.json").read_bytes()
    assert run(settings) == first
    assert (settings.output_dir / "scan.json").read_bytes() == bytes_before
    runner = CliRunner()
    raw, sim, scanned = tmp_path / "raw.jsonl", tmp_path / "sim.jsonl", tmp_path / "scan.json"
    commands = [
        ["ingest", "--limit", "10", "--out", str(raw)],
        ["simulate", str(raw), "--out", str(sim)],
        ["scan", str(sim), "--out", str(scanned)],
        ["enrich", str(scanned), "--out", str(tmp_path / "enriched.json")],
        ["evaluate", str(sim), str(scanned), "--out", str(tmp_path / "eval.json")],
    ]
    for command in commands:
        result = runner.invoke(app, command)
        assert result.exit_code == 0, result.exception
    config = tmp_path / "config.yaml"
    config.write_text(f"items: 5\noutput_dir: {tmp_path / 'run'}\n")
    result = runner.invoke(app, ["run", "--config", str(config)])
    assert result.exit_code == 0, result.exception
    write_jsonl(generate(1), raw)
