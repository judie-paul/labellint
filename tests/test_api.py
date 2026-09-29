"""Exercise uploads, synthetic jobs and review responses through HTTP."""

from fastapi.testclient import TestClient

from labellint.api import MAX_UPLOAD, create_app
from labellint.synthetic import generate


def test_demo_review_and_delete() -> None:
    client = TestClient(create_app())
    assert client.get("/api/health").json() == {"status": "ok"}
    response = client.post("/api/demo", json={"items": 8, "seed": 42})
    assert response.status_code == 202
    job_id = response.json()["id"]
    assert client.get(f"/api/jobs/{job_id}").json()["status"] == "completed"
    result = client.get(f"/api/jobs/{job_id}/results").json()
    assert len(result["scan"]["records"]) == 24
    assert result["evaluation"]["records"] == 24
    assert "ground_truth" not in str(result["scan"])
    assert client.get(f"/api/jobs/{job_id}/report").text.startswith("# LabelLint")
    assert len(client.get("/api/jobs").json()) == 1
    assert client.delete(f"/api/jobs/{job_id}").status_code == 204
    assert client.get(f"/api/jobs/{job_id}").status_code == 404


def test_upload_validation_and_unlabeled_data() -> None:
    client = TestClient(create_app())
    raw = generate(1)[0].model_dump_json()
    response = client.post("/api/jobs", files={"file": ("sample.jsonl", raw)})
    assert response.status_code == 202
    result = client.get(f"/api/jobs/{response.json()['id']}/results").json()
    assert result["evaluation"] is None
    assert client.post("/api/jobs", files={"file": ("bad.txt", raw)}).status_code == 422
    assert client.post("/api/jobs", files={"file": ("bad.jsonl", "{}")}).status_code == 422
    assert (
        client.post(
            "/api/jobs", files={"file": ("large.jsonl", b" " * (MAX_UPLOAD + 1))}
        ).status_code
        == 413
    )
    assert client.post("/api/demo", json={"items": 10000}).status_code == 422


def test_failure_state(monkeypatch) -> None:
    def fail(*args):
        raise ValueError("private data must not be returned")

    monkeypatch.setattr("labellint.api.scan", fail)
    client = TestClient(create_app())
    job = client.post("/api/demo", json={"items": 1}).json()
    status = client.get(f"/api/jobs/{job['id']}").json()
    assert status["status"] == "failed"
    assert "private data" not in status["error"]
    assert client.get(f"/api/jobs/{job['id']}/results").status_code == 409
    assert client.get(f"/api/jobs/{job['id']}/report").status_code == 409
