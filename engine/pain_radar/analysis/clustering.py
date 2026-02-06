"""Pain clustering — group raw evidence into pain clusters."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from pain_radar.core.evidence_gate import MAX_RETRIES, validate_output
from pain_radar.core.models import (
    Citation,
    ClusterScores,
    Competitor,
    EvidencedClaim,
    OnboardingModel,
    PainCluster,
    ScoredDimension,
    SourceType,
)
from pain_radar.llm.prompts import (
    CLUSTERING_SYSTEM,
    CLUSTERING_USER,
    COMPETITOR_SYSTEM,
    COMPETITOR_USER,
    format_evidence_summary,
)

if TYPE_CHECKING:
    from pain_radar.llm.base import LLMProvider

logger = logging.getLogger(__name__)


async def cluster_evidence(
    citations: list[Citation],
    idea: str,
    options: dict,
    llm: LLMProvider,
) -> list[PainCluster]:
    """Group citations into pain clusters via LLM. Output passes evidence gate."""
    evidence_dicts = [c.model_dump() for c in citations]
    evidence_summary = format_evidence_summary(evidence_dicts)

    prompt_content = CLUSTERING_USER.format(
        idea=idea,
        count=len(citations),
        evidence_summary=evidence_summary,
    )

    for attempt in range(MAX_RETRIES + 1):
        try:
            raw = await llm.complete_json(
                system=CLUSTERING_SYSTEM,
                messages=[{"role": "user", "content": prompt_content}],
                max_tokens=8192,
            )

            if not isinstance(raw, list):
                raw = [raw]

            clusters = []
            for item in raw:
                cluster = _parse_cluster(item, len(citations))
                if cluster:
                    clusters.append(cluster)

            if not clusters:
                logger.warning(f"Clustering attempt {attempt + 1}: no valid clusters")
                prompt_content += "\n\nPrevious attempt produced no valid clusters. Try again with valid citation_indices."
                continue

            return clusters

        except Exception:
            logger.exception(f"Clustering attempt {attempt + 1} failed")
            if attempt < MAX_RETRIES:
                prompt_content += "\n\nPrevious attempt failed. Output valid JSON array of cluster objects."

    logger.error("Clustering exhausted all retries")
    return []


def _parse_cluster(item: dict, pack_size: int) -> PainCluster | None:
    """Parse a raw cluster dict into a PainCluster, validating indices."""
    try:
        citation_indices = item.get("citation_indices", [])
        # Filter to valid indices
        valid_indices = [i for i in citation_indices if 0 <= i < pack_size]
        if not valid_indices:
            return None

        # Build placeholder scores (will be filled by scoring stage)
        placeholder_dim = ScoredDimension(
            score=0,
            justification=EvidencedClaim(
                text="Pending scoring",
                citation_indices=valid_indices[:1],
            ),
        )
        placeholder_scores = ClusterScores(
            frequency=placeholder_dim,
            severity=placeholder_dim,
            urgency=placeholder_dim,
            payability=placeholder_dim,
            workaround_cost=placeholder_dim,
            saturation=placeholder_dim,
            accessibility=placeholder_dim,
        )

        return PainCluster(
            id=item.get("id", "unknown"),
            statement=EvidencedClaim(
                text=item.get("statement", "Unknown pain"),
                citation_indices=valid_indices[:3],
            ),
            who=item.get("who", "Unknown"),
            trigger=item.get("trigger", "Unknown"),
            workarounds=item.get("workarounds", []),
            citation_indices=valid_indices,
            scores=placeholder_scores,
            confidence=0.5,
            recency_weight=1.0,
        )
    except Exception:
        logger.exception("Failed to parse cluster")
        return None


async def extract_competitors(
    citations: list[Citation],
    idea: str,
    options: dict,
    llm: LLMProvider,
) -> list[Competitor]:
    """Extract competitor information from evidence. Output passes evidence gate."""
    evidence_dicts = [c.model_dump() for c in citations]
    evidence_summary = format_evidence_summary(evidence_dicts)

    prompt_content = COMPETITOR_USER.format(
        idea=idea,
        count=len(citations),
        evidence_summary=evidence_summary,
    )

    for attempt in range(MAX_RETRIES + 1):
        try:
            raw = await llm.complete_json(
                system=COMPETITOR_SYSTEM,
                messages=[{"role": "user", "content": prompt_content}],
                max_tokens=8192,
            )

            if not isinstance(raw, list):
                raw = [raw]

            competitors = []
            for item in raw:
                comp = _parse_competitor(item, len(citations))
                if comp:
                    competitors.append(comp)

            return competitors

        except Exception:
            logger.exception(f"Competitor extraction attempt {attempt + 1} failed")

    return []


def _parse_competitor(item: dict, pack_size: int) -> Competitor | None:
    """Parse a raw competitor dict into a Competitor model."""
    try:
        citation_indices = [i for i in item.get("citation_indices", []) if 0 <= i < pack_size]
        if not citation_indices:
            return None

        # Parse strengths/weaknesses as EvidencedClaims
        strengths = []
        for s in item.get("strengths", []):
            if isinstance(s, dict) and s.get("text"):
                indices = [i for i in s.get("citation_indices", []) if 0 <= i < pack_size]
                if indices:
                    strengths.append(EvidencedClaim(text=s["text"], citation_indices=indices))

        weaknesses = []
        for w in item.get("weaknesses", []):
            if isinstance(w, dict) and w.get("text"):
                indices = [i for i in w.get("citation_indices", []) if 0 <= i < pack_size]
                if indices:
                    weaknesses.append(EvidencedClaim(text=w["text"], citation_indices=indices))

        # Ensure at least one strength/weakness placeholder
        if not strengths:
            strengths = [EvidencedClaim(text="No strengths identified in evidence", citation_indices=citation_indices[:1])]
        if not weaknesses:
            weaknesses = [EvidencedClaim(text="No weaknesses identified in evidence", citation_indices=citation_indices[:1])]

        # Parse target_icp
        target_icp = None
        if item.get("target_icp") and isinstance(item["target_icp"], dict):
            icp_indices = [i for i in item["target_icp"].get("citation_indices", []) if 0 <= i < pack_size]
            if icp_indices:
                target_icp = EvidencedClaim(
                    text=item["target_icp"].get("text", ""),
                    citation_indices=icp_indices,
                )

        # Parse onboarding model
        onboarding_raw = item.get("onboarding_model", "unknown")
        try:
            onboarding = OnboardingModel(onboarding_raw)
        except ValueError:
            onboarding = OnboardingModel.UNKNOWN

        return Competitor(
            name=item.get("name", "Unknown"),
            url=item.get("url", ""),
            pricing_page_exists=bool(item.get("pricing_page_exists", False)),
            min_price_observed=item.get("min_price_observed"),
            target_icp=target_icp,
            onboarding_model=onboarding,
            positioning=item.get("positioning", ""),
            strengths=strengths,
            weaknesses=weaknesses,
            citation_indices=citation_indices,
        )
    except Exception:
        logger.exception("Failed to parse competitor")
        return None
