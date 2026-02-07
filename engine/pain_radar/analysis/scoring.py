"""Scoring — score clusters on 7 dimensions + payability assessment."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import TYPE_CHECKING

from pain_radar.core.evidence_gate import MAX_RETRIES, validate_output
from pain_radar.core.models import (
    Citation,
    ClusterScores,
    EvidencedClaim,
    PainCluster,
    PayabilityAssessment,
    ScoredDimension,
)
from pain_radar.llm.prompts import (
    PAYABILITY_SYSTEM,
    PAYABILITY_USER,
    SCORING_SYSTEM,
    SCORING_USER,
    format_evidence_summary,
)

if TYPE_CHECKING:
    from pain_radar.llm.base import LLMProvider

logger = logging.getLogger(__name__)


def compute_recency_weight(
    date_published: str | None, niche_velocity: str = "normal"
) -> float:
    """Compute recency weight for evidence.

    - Unknown date: 0.5
    - < 6 months: 1.0
    - 6-24 months: 0.75
    - > 24 months (normal niche): 0.3
    - > 24 months (slow niche): 0.7
    """
    if not date_published:
        return 0.5

    try:
        pub_date = datetime.fromisoformat(date_published.replace("Z", "+00:00"))
        now = datetime.now(timezone.utc)
        months = (now.year - pub_date.year) * 12 + (now.month - pub_date.month)
    except (ValueError, AttributeError):
        return 0.5

    if months < 6:
        return 1.0
    elif months <= 24:
        return 0.75
    elif niche_velocity == "slow":
        return 0.7
    else:
        return 0.3


async def score_clusters(
    clusters: list[PainCluster],
    citations: list[Citation],
    llm: LLMProvider,
) -> list[PainCluster]:
    """Score each cluster on 7 dimensions. Each score passes evidence gate."""
    evidence_dicts = [c.model_dump() for c in citations]
    evidence_summary = format_evidence_summary(evidence_dicts)
    scored = []

    for cluster in clusters:
        prompt_content = SCORING_USER.format(
            cluster_statement=cluster.statement.text,
            who=cluster.who,
            trigger=cluster.trigger,
            citation_indices=cluster.citation_indices,
            count=len(citations),
            evidence_summary=evidence_summary,
        )

        for attempt in range(MAX_RETRIES + 1):
            try:
                raw = await llm.complete_json(
                    system=SCORING_SYSTEM,
                    messages=[{"role": "user", "content": prompt_content}],
                    max_tokens=4096,
                )

                scores = _parse_scores(raw, len(citations), cluster.citation_indices)
                if scores:
                    # Compute recency weight from supporting citations
                    recency_weights = []
                    for idx in cluster.citation_indices:
                        if 0 <= idx < len(citations):
                            w = compute_recency_weight(citations[idx].date_published)
                            recency_weights.append(w)
                    avg_recency = (
                        sum(recency_weights) / len(recency_weights)
                        if recency_weights
                        else 0.5
                    )

                    cluster.scores = scores
                    cluster.confidence = raw.get("confidence", 0.5)
                    cluster.recency_weight = avg_recency
                    break

            except Exception:
                logger.exception(f"Scoring attempt {attempt + 1} failed for cluster {cluster.id}")

        scored.append(cluster)

    return scored


def _parse_scores(raw: dict, pack_size: int, fallback_indices: list[int]) -> ClusterScores | None:
    """Parse raw scoring output into ClusterScores."""
    dimensions = [
        "frequency", "severity", "urgency", "payability",
        "workaround_cost", "saturation", "accessibility",
    ]

    parsed = {}
    for dim in dimensions:
        dim_data = raw.get(dim, {})
        if not isinstance(dim_data, dict):
            return None

        score = dim_data.get("score", 0)
        if not isinstance(score, int) or score < 0 or score > 5:
            score = max(0, min(5, int(score) if isinstance(score, (int, float)) else 0))

        justification = dim_data.get("justification", {})
        if isinstance(justification, str):
            justification = {"text": justification, "citation_indices": fallback_indices[:1]}

        text = justification.get("text", f"Score {score} for {dim}")
        indices = justification.get("citation_indices", fallback_indices[:1])
        valid_indices = [i for i in indices if 0 <= i < pack_size]
        if not valid_indices:
            valid_indices = fallback_indices[:1]

        parsed[dim] = ScoredDimension(
            score=score,
            justification=EvidencedClaim(text=text, citation_indices=valid_indices),
        )

    try:
        return ClusterScores(**parsed)
    except Exception:
        logger.exception("Failed to construct ClusterScores")
        return None


async def assess_payability(
    citations: list[Citation],
    idea: str,
    llm: LLMProvider,
) -> PayabilityAssessment:
    """Assess payability signals from evidence."""
    evidence_dicts = [c.model_dump() for c in citations]
    evidence_summary = format_evidence_summary(evidence_dicts)
    unique_urls = len({c.url for c in citations})

    prompt_content = PAYABILITY_USER.format(
        idea=idea,
        count=len(citations),
        unique_urls=unique_urls,
        evidence_summary=evidence_summary,
    )

    for attempt in range(MAX_RETRIES + 1):
        try:
            raw = await llm.complete_json(
                system=PAYABILITY_SYSTEM,
                messages=[{"role": "user", "content": prompt_content}],
                max_tokens=4096,
            )

            return _parse_payability(raw, len(citations))

        except Exception:
            logger.exception(f"Payability assessment attempt {attempt + 1} failed")

    # Fallback: insufficient evidence
    return PayabilityAssessment(
        hiring_signals=[],
        outsourcing_signals=[],
        template_sop_signals=[],
        overall_strength="none",
        summary="Insufficient evidence to assess payability.",
    )


def _parse_payability(raw: dict, pack_size: int) -> PayabilityAssessment:
    """Parse raw payability output.

    Hard cap: if all signals reference 2 or fewer unique citation indices,
    strength cannot exceed "moderate" (prevents single-source inflation).
    """
    def parse_signals(key: str) -> list[EvidencedClaim]:
        signals = []
        for s in raw.get(key, []):
            if isinstance(s, dict) and s.get("text"):
                indices = [i for i in s.get("citation_indices", []) if 0 <= i < pack_size]
                if indices:
                    signals.append(EvidencedClaim(text=s["text"], citation_indices=indices))
        return signals

    hiring = parse_signals("hiring_signals")
    outsourcing = parse_signals("outsourcing_signals")
    template_sop = parse_signals("template_sop_signals")

    strength = raw.get("overall_strength", "none")
    if strength not in ("strong", "moderate", "weak", "none"):
        strength = "none"

    # Hard cap: count unique citation indices across all signals.
    # If all signals point to <= 2 unique sources, cap at "moderate".
    all_indices: set[int] = set()
    for sig in hiring + outsourcing + template_sop:
        all_indices.update(sig.citation_indices)

    summary = raw.get("summary", "No payability assessment available.")
    if strength == "strong" and len(all_indices) <= 2:
        strength = "moderate"
        summary += (
            " [Capped from 'strong': all signals reference 2 or fewer unique citations.]"
        )

    return PayabilityAssessment(
        hiring_signals=hiring,
        outsourcing_signals=outsourcing,
        template_sop_signals=template_sop,
        overall_strength=strength,
        summary=summary,
    )
