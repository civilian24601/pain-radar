"""Report assembly — combine all pipeline outputs into a ResearchReport."""

from __future__ import annotations

from pain_radar.core.models import (
    Citation,
    Competitor,
    ConflictReport,
    IdeaBrief,
    PainCluster,
    PayabilityAssessment,
    ResearchReport,
    ValidationPlan,
    Verdict,
)


def assemble_report(
    job_id: str,
    idea_brief: IdeaBrief,
    clusters: list[PainCluster],
    payability: PayabilityAssessment,
    competitors: list[Competitor],
    verdict: Verdict,
    validation_plan: ValidationPlan,
    citations: list[Citation],
    skeptic_flags: list[str],
    conflicts: list[ConflictReport],
) -> ResearchReport:
    """Assemble a full ResearchReport from pipeline outputs."""
    # Sort clusters by composite score (descending)
    sorted_clusters = sorted(
        clusters,
        key=lambda c: _composite_score(c),
        reverse=True,
    )

    return ResearchReport(
        id=job_id,
        idea_brief=idea_brief,
        pain_map=sorted_clusters,
        payability=payability,
        competitors=competitors,
        verdict=verdict,
        validation_plan=validation_plan,
        evidence_pack=citations,
        skeptic_flags=skeptic_flags,
        conflicts=conflicts,
    )


def _composite_score(cluster: PainCluster) -> float:
    """Compute a composite score for ranking clusters.

    Weighted average of dimensions * confidence * recency_weight.
    """
    s = cluster.scores
    raw = (
        s.frequency.score * 1.0
        + s.severity.score * 1.5
        + s.urgency.score * 1.2
        + s.payability.score * 2.0
        + s.workaround_cost.score * 1.0
        + s.saturation.score * 1.3
        + s.accessibility.score * 0.8
    ) / 8.8  # max possible = 5 * 8.8 / 8.8 = 5

    return raw * cluster.confidence * cluster.recency_weight
