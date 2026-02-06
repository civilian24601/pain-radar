"""API request/response schemas."""

from __future__ import annotations

from pydantic import BaseModel

from pain_radar.core.models import (
    ClarificationAnswer,
    ClarificationQuestion,
    JobProgress,
    ResearchReport,
)


# -- Requests --

class RunRequest(BaseModel):
    idea: str
    niche: str | None = None
    geography: str | None = None
    buyer_role: str | None = None
    competitor_names: list[str] | None = None
    constraints: str | None = None


class ClarifyRequest(BaseModel):
    answers: list[ClarificationAnswer]


# -- Responses --

class RunResponse(BaseModel):
    job_id: str


class StatusResponse(BaseModel):
    job_id: str
    status: str
    progress: JobProgress | None = None
    clarification_questions: list[ClarificationQuestion] | None = None


class ReportResponse(BaseModel):
    job_id: str
    status: str
    report: ResearchReport | None = None
    error: str | None = None
