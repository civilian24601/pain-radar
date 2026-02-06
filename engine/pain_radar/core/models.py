"""Core domain models for Pain Radar.

Every claim that references evidence uses EvidencedClaim, which rejects
empty citation_indices at the schema level. No uncited claims pass validation.
"""

from __future__ import annotations

import re
from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class JobStatus(str, Enum):
    CREATED = "created"
    CLARIFYING = "clarifying"
    RESEARCHING = "researching"
    ANALYZING = "analyzing"
    REVIEWING = "reviewing"
    COMPLETE = "complete"
    FAILED = "failed"


class SourceType(str, Enum):
    REDDIT = "reddit"
    REVIEW = "review"
    COMPETITOR = "competitor"
    JOB_POST = "job_post"
    WEB = "web"


class OnboardingModel(str, Enum):
    SELF_SERVE = "self_serve"
    SALES_LED = "sales_led"
    UNKNOWN = "unknown"


class VerdictDecision(str, Enum):
    KILL = "KILL"
    NARROW = "NARROW"
    ADVANCE = "ADVANCE"


# ---------------------------------------------------------------------------
# Source Snapshot — raw content stored for every URL accessed
# ---------------------------------------------------------------------------

class SourceSnapshot(BaseModel):
    url: str
    content_hash: str  # SHA256 of raw content
    raw_text: str  # extracted text (HTML stripped)
    fetched_at: str  # ISO timestamp
    storage_path: str  # path to raw file on disk


# ---------------------------------------------------------------------------
# Citation — must be extractable from its source snapshot
# ---------------------------------------------------------------------------

class Citation(BaseModel):
    url: str
    excerpt: str
    source_type: SourceType
    date_published: str | None = None
    date_retrieved: str  # ISO timestamp
    recency_months: int | None = None  # computed: months since publication
    snapshot_hash: str  # links back to SourceSnapshot


# ---------------------------------------------------------------------------
# Evidence Gate primitives
# ---------------------------------------------------------------------------

class EvidencedClaim(BaseModel):
    """Any claim that references evidence. Rejects empty citation_indices."""

    text: str
    citation_indices: list[int] = Field(..., min_length=1)

    @field_validator("citation_indices")
    @classmethod
    def must_have_citations(cls, v: list[int]) -> list[int]:
        if not v:
            raise ValueError("Claim must reference at least one citation")
        return v


# Regex to find freeform numbers (integers or decimals) that could be invented.
_NUM_PATTERN = re.compile(r"\b\d+(?:\.\d+)?%?\b")


class ScoredDimension(BaseModel):
    score: int = Field(..., ge=0, le=5)
    justification: EvidencedClaim

    @model_validator(mode="after")
    def numeric_must_be_cited(self) -> ScoredDimension:
        """If justification text contains a numeric value, it must appear
        in at least one cited excerpt. Enforced at the evidence gate layer
        (see evidence_gate.py) since we need the full evidence pack context."""
        return self


class ClusterScores(BaseModel):
    frequency: ScoredDimension
    severity: ScoredDimension
    urgency: ScoredDimension
    payability: ScoredDimension
    workaround_cost: ScoredDimension
    saturation: ScoredDimension  # inverse: fewer tools = higher score
    accessibility: ScoredDimension


# ---------------------------------------------------------------------------
# Pain Cluster
# ---------------------------------------------------------------------------

class PainCluster(BaseModel):
    id: str
    statement: EvidencedClaim  # one-sentence pain, must cite
    who: str
    trigger: str
    workarounds: list[str]
    citation_indices: list[int] = Field(..., min_length=1)
    scores: ClusterScores
    confidence: float = Field(..., ge=0.0, le=1.0)
    recency_weight: float = Field(..., ge=0.0, le=1.0)


# ---------------------------------------------------------------------------
# Competitor — explicit observable fields
# ---------------------------------------------------------------------------

class Competitor(BaseModel):
    name: str
    url: str
    pricing_page_exists: bool  # directly observed
    min_price_observed: str | None = None  # e.g. "$29/mo" or None
    target_icp: EvidencedClaim | None = None  # inferred, must cite
    onboarding_model: OnboardingModel = OnboardingModel.UNKNOWN
    positioning: str
    strengths: list[EvidencedClaim]
    weaknesses: list[EvidencedClaim]
    citation_indices: list[int] = Field(..., min_length=1)


# ---------------------------------------------------------------------------
# Conflict Detection
# ---------------------------------------------------------------------------

class ConflictReport(BaseModel):
    description: str
    side_a: EvidencedClaim
    side_b: EvidencedClaim


# ---------------------------------------------------------------------------
# Verdict
# ---------------------------------------------------------------------------

class Verdict(BaseModel):
    decision: VerdictDecision
    reasons: list[EvidencedClaim] = Field(..., min_length=1, max_length=5)
    risks: list[EvidencedClaim] = Field(..., min_length=1, max_length=5)
    narrowest_wedge: str
    what_would_change: str  # evidence that reverses verdict
    conflicts: list[ConflictReport] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Validation Plan — mandatory for ALL verdicts
# ---------------------------------------------------------------------------

class ValidationPlan(BaseModel):
    verdict_context: VerdictDecision
    objective: str  # what this 7-day plan aims to prove/disprove
    channels: list[str]
    outreach_targets: list[str]
    interview_script: str
    landing_page_hypotheses: list[str] = Field(default_factory=list)  # empty for KILL
    concierge_procedure: str = ""  # empty for KILL
    success_threshold: str  # for KILL: "what reversal evidence looks like"
    reversal_criteria: str | None = None  # KILL only


# ---------------------------------------------------------------------------
# Payability Assessment
# ---------------------------------------------------------------------------

class PayabilityAssessment(BaseModel):
    hiring_signals: list[EvidencedClaim]
    outsourcing_signals: list[EvidencedClaim]
    template_sop_signals: list[EvidencedClaim]
    overall_strength: Literal["strong", "moderate", "weak", "none"]
    summary: str


# ---------------------------------------------------------------------------
# Idea Brief
# ---------------------------------------------------------------------------

class IdeaBrief(BaseModel):
    raw_idea: str
    one_liner: str  # LLM-refined one-sentence summary
    buyer_persona: str
    workflow_replaced: str
    moment_of_pain: str
    keywords: list[str] = Field(..., min_length=1, max_length=10)


# ---------------------------------------------------------------------------
# Clarification
# ---------------------------------------------------------------------------

class ClarificationQuestion(BaseModel):
    question: str
    options: list[str] | None = None  # quick-pick options; None = freeform


class ClarificationAnswer(BaseModel):
    question: str
    answer: str


# ---------------------------------------------------------------------------
# Progress Tracking
# ---------------------------------------------------------------------------

class JobProgress(BaseModel):
    stage: str
    source_packs_total: int = 0
    source_packs_done: int = 0
    citations_found: int = 0
    current_action: str = ""


# ---------------------------------------------------------------------------
# Full Research Report
# ---------------------------------------------------------------------------

class ResearchReport(BaseModel):
    id: str
    idea_brief: IdeaBrief
    pain_map: list[PainCluster]
    payability: PayabilityAssessment
    competitors: list[Competitor]
    verdict: Verdict
    validation_plan: ValidationPlan
    evidence_pack: list[Citation]
    skeptic_flags: list[str]
    conflicts: list[ConflictReport]
