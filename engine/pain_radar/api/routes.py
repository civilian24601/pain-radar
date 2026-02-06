"""API routes for Pain Radar research engine."""

from __future__ import annotations

import csv
import io
import json
import uuid
from typing import TYPE_CHECKING

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse

from pain_radar.api.schemas import (
    ClarifyRequest,
    ReportResponse,
    RunRequest,
    RunResponse,
    StatusResponse,
)
from pain_radar.core.models import ClarificationQuestion, JobProgress

if TYPE_CHECKING:
    from pain_radar.db import Database
    from pain_radar.pipeline.orchestrator import ResearchOrchestrator

router = APIRouter(prefix="/api/research")

# These are set by main.py at startup
_db: Database | None = None
_orchestrator: ResearchOrchestrator | None = None


def init_routes(db: Database, orchestrator: ResearchOrchestrator) -> None:
    global _db, _orchestrator
    _db = db
    _orchestrator = orchestrator


def _get_db() -> Database:
    assert _db is not None, "Database not initialized"
    return _db


def _get_orchestrator() -> ResearchOrchestrator:
    assert _orchestrator is not None, "Orchestrator not initialized"
    return _orchestrator


@router.post("/run", response_model=RunResponse)
async def start_research(req: RunRequest) -> RunResponse:
    db = _get_db()
    orchestrator = _get_orchestrator()

    job_id = str(uuid.uuid4())
    options = {
        "niche": req.niche,
        "geography": req.geography,
        "buyer_role": req.buyer_role,
        "competitor_names": req.competitor_names,
        "constraints": req.constraints,
    }
    await db.create_job(job_id, req.idea, options)

    # Launch research pipeline in background
    orchestrator.launch(job_id, req.idea, options)

    return RunResponse(job_id=job_id)


@router.post("/{job_id}/clarify")
async def submit_clarification(job_id: str, req: ClarifyRequest) -> StatusResponse:
    db = _get_db()
    orchestrator = _get_orchestrator()

    job = await db.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if job["status"] != "clarifying":
        raise HTTPException(status_code=400, detail=f"Job is not awaiting clarification (status: {job['status']})")

    answers = [a.model_dump() for a in req.answers]
    await db.set_clarification_answers(job_id, answers)

    # Resume pipeline with answers
    orchestrator.resume_after_clarification(job_id, req.answers)

    return StatusResponse(job_id=job_id, status="researching")


@router.get("/{job_id}/status", response_model=StatusResponse)
async def get_status(job_id: str) -> StatusResponse:
    db = _get_db()

    job = await db.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    progress = None
    if job["progress_json"]:
        progress = JobProgress(**json.loads(job["progress_json"]))

    questions = None
    if job["status"] == "clarifying" and job["clarification_questions_json"]:
        raw = json.loads(job["clarification_questions_json"])
        questions = [ClarificationQuestion(**q) for q in raw]

    return StatusResponse(
        job_id=job_id,
        status=job["status"],
        progress=progress,
        clarification_questions=questions,
    )


@router.get("/{job_id}/report", response_model=ReportResponse)
async def get_report(job_id: str) -> ReportResponse:
    db = _get_db()

    job = await db.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    if job["status"] == "failed":
        return ReportResponse(job_id=job_id, status="failed", error="Research failed")

    if job["status"] != "complete":
        return ReportResponse(job_id=job_id, status=job["status"])

    report_row = await db.get_report(job_id)
    if not report_row:
        raise HTTPException(status_code=500, detail="Report not found despite complete status")

    from pain_radar.core.models import ResearchReport
    report = ResearchReport(**json.loads(report_row["report_json"]))

    return ReportResponse(job_id=job_id, status="complete", report=report)


@router.get("/{job_id}/export")
async def export_evidence(
    job_id: str, format: str = Query("json", pattern="^(json|csv)$")
) -> StreamingResponse:
    db = _get_db()

    job = await db.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    citations = await db.get_citations(job_id)
    if not citations:
        raise HTTPException(status_code=404, detail="No citations found")

    if format == "json":
        content = json.dumps(citations, indent=2)
        return StreamingResponse(
            io.BytesIO(content.encode()),
            media_type="application/json",
            headers={"Content-Disposition": f"attachment; filename=evidence_{job_id}.json"},
        )

    # CSV export
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=[
        "id", "url", "excerpt", "source_type", "date_published",
        "date_retrieved", "recency_months", "snapshot_hash",
    ])
    writer.writeheader()
    for c in citations:
        writer.writerow({
            "id": c["id"],
            "url": c["url"],
            "excerpt": c["excerpt"],
            "source_type": c["source_type"],
            "date_published": c["date_published"],
            "date_retrieved": c["date_retrieved"],
            "recency_months": c["recency_months"],
            "snapshot_hash": c["snapshot_hash"],
        })

    return StreamingResponse(
        io.BytesIO(output.getvalue().encode()),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=evidence_{job_id}.csv"},
    )
