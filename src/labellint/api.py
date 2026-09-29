"""Single-process local review API with bounded uploads and background jobs."""

import logging
import os
import threading
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Annotated, Any
from uuid import uuid4

from fastapi import BackgroundTasks, FastAPI, File, HTTPException, UploadFile
from fastapi.responses import PlainTextResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from labellint import __version__
from labellint.config import Settings
from labellint.evaluate import evaluate
from labellint.ingest import load_local
from labellint.llm.enrich import enrich
from labellint.pipeline import scan
from labellint.report import markdown
from labellint.schema import AnnotationRecord
from labellint.simulate import simulate
from labellint.synthetic import generate

logger = logging.getLogger(__name__)
MAX_UPLOAD = 2 * 1024 * 1024
MAX_RECORDS = 2000


class DemoRequest(BaseModel):
    """Bounded synthetic demo options."""

    seed: int = Field(default=42, ge=0)
    items: int = Field(default=100, ge=1, le=300)


def create_app() -> FastAPI:
    """Create an isolated in-memory job store for local review sessions."""
    app = FastAPI(title="LabelLint", version=__version__)
    jobs: dict[str, dict[str, Any]] = {}
    lock = threading.Lock()

    def process(job_id: str, records: list[AnnotationRecord]) -> None:
        with lock:
            jobs[job_id]["status"] = "running"
        try:
            report = enrich(scan(records, Settings()), "mock")
            evaluation = evaluate(records, report) if all(r.ground_truth for r in records) else None
            payload = {"scan": report.model_dump(mode="json"), "evaluation": evaluation}
            with lock:
                jobs[job_id].update(status="completed", result=payload, markdown=markdown(report))
        except Exception:
            logger.exception("Audit job failed")
            with lock:
                jobs[job_id].update(
                    status="failed", error="Audit failed; verify unique raters per item/aspect."
                )

    def submit(
        records: list[AnnotationRecord], name: str, background: BackgroundTasks
    ) -> dict[str, Any]:
        if not records or len(records) > MAX_RECORDS:
            raise HTTPException(422, f"Provide between 1 and {MAX_RECORDS} records")
        with lock:
            if sum(j["status"] in {"queued", "running"} for j in jobs.values()) >= 2:
                raise HTTPException(429, "Two audits are already active")
            if len(jobs) >= 100:
                raise HTTPException(429, "Session limit reached; delete a completed audit")
            job: dict[str, Any] = {
                "id": uuid4().hex,
                "name": name,
                "status": "queued",
                "records": len(records),
            }
            jobs[job["id"]] = job
        background.add_task(process, job["id"], records)
        return dict(job)

    def find(job_id: str) -> dict[str, Any]:
        if job_id not in jobs:
            raise HTTPException(404, "Audit not found")
        return jobs[job_id]

    @app.get("/api/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/api/jobs")
    def list_jobs() -> list[dict[str, Any]]:
        with lock:
            return [
                {k: v for k, v in job.items() if k not in {"result", "markdown"}}
                for job in reversed(list(jobs.values()))
            ]

    @app.post("/api/demo", status_code=202)
    def demo(options: DemoRequest, background: BackgroundTasks) -> dict[str, Any]:
        records = simulate(generate(options.items, options.seed), Settings(seed=options.seed))
        return submit(records, f"Synthetic audit · seed {options.seed}", background)

    @app.post("/api/jobs", status_code=202)
    async def upload(
        background: BackgroundTasks, file: Annotated[UploadFile, File()]
    ) -> dict[str, Any]:
        suffix = Path(file.filename or "").suffix.lower()
        if suffix not in {".csv", ".jsonl"}:
            raise HTTPException(422, "Upload a CSV or JSONL file")
        content = await file.read(MAX_UPLOAD + 1)
        await file.close()
        if len(content) > MAX_UPLOAD:
            raise HTTPException(413, "Upload exceeds 2 MiB")
        with TemporaryDirectory(prefix="labellint-upload-") as directory:
            path = Path(directory) / ("upload" + suffix)
            path.write_bytes(content)
            try:
                records = load_local(path)
            except (ValueError, UnicodeError) as error:
                raise HTTPException(422, str(error).replace(str(path), "upload")) from None
        return submit(records, Path(file.filename or "Upload").name[:120], background)

    @app.get("/api/jobs/{job_id}")
    def job_status(job_id: str) -> dict[str, Any]:
        with lock:
            return {k: v for k, v in find(job_id).items() if k not in {"result", "markdown"}}

    @app.get("/api/jobs/{job_id}/results")
    def results(job_id: str) -> dict[str, Any]:
        with lock:
            job = find(job_id)
            if job["status"] != "completed":
                raise HTTPException(409, "Audit results are not ready")
            return dict(job["result"])

    @app.get("/api/jobs/{job_id}/report", response_class=PlainTextResponse)
    def report(job_id: str) -> str:
        with lock:
            job = find(job_id)
            if job["status"] != "completed":
                raise HTTPException(409, "Audit report is not ready")
            return str(job["markdown"])

    @app.delete("/api/jobs/{job_id}", status_code=204)
    def delete(job_id: str) -> None:
        with lock:
            if find(job_id)["status"] in {"queued", "running"}:
                raise HTTPException(409, "Cannot delete an active audit")
            del jobs[job_id]

    static = Path(os.getenv("LABELLINT_STATIC_DIR", "dashboard/dist"))
    if static.is_dir():
        app.mount("/", StaticFiles(directory=static, html=True), name="dashboard")
    return app


app = create_app()
