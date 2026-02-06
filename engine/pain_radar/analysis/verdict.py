"""Verdict generation + validation plan."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from pain_radar.core.evidence_gate import MAX_RETRIES
from pain_radar.core.models import (
    Citation,
    Competitor,
    ConflictReport,
    EvidencedClaim,
    PainCluster,
    PayabilityAssessment,
    ValidationPlan,
    Verdict,
    VerdictDecision,
)
from pain_radar.llm.prompts import (
    VALIDATION_PLAN_SYSTEM,
    VALIDATION_PLAN_USER,
    VERDICT_SYSTEM,
    VERDICT_USER,
    format_evidence_summary,
)

if TYPE_CHECKING:
    from pain_radar.llm.base import LLMProvider

logger = logging.getLogger(__name__)


async def generate_verdict(
    clusters: list[PainCluster],
    competitors: list[Competitor],
    payability: PayabilityAssessment,
    conflicts: list[ConflictReport],
    citations: list[Citation],
    llm: LLMProvider,
) -> Verdict:
    """Generate KILL/NARROW/ADVANCE verdict with evidence."""
    evidence_dicts = [c.model_dump() for c in citations]
    evidence_summary = format_evidence_summary(evidence_dicts)

    clusters_summary = "\n".join(
        f"- [{c.id}] {c.statement.text} | frequency={c.scores.frequency.score} "
        f"severity={c.scores.severity.score} payability={c.scores.payability.score} "
        f"confidence={c.confidence:.2f} recency={c.recency_weight:.2f}"
        for c in clusters
    )

    competitors_summary = "\n".join(
        f"- {c.name}: pricing_page={c.pricing_page_exists}, "
        f"min_price={c.min_price_observed or 'unknown'}, "
        f"onboarding={c.onboarding_model.value}"
        for c in competitors
    )

    payability_summary = (
        f"Overall: {payability.overall_strength}\n"
        f"Hiring signals: {len(payability.hiring_signals)}\n"
        f"Outsourcing signals: {len(payability.outsourcing_signals)}\n"
        f"Summary: {payability.summary}"
    )

    conflicts_summary = "\n".join(
        f"- {c.description}" for c in conflicts
    ) or "No conflicts detected"

    prompt_content = VERDICT_USER.format(
        idea=evidence_dicts[0].get("url", "unknown") if evidence_dicts else "unknown",
        clusters_summary=clusters_summary or "No clusters",
        competitors_summary=competitors_summary or "No competitors",
        payability_summary=payability_summary,
        conflicts_summary=conflicts_summary,
        count=len(citations),
        evidence_summary=evidence_summary,
    )

    for attempt in range(MAX_RETRIES + 1):
        try:
            raw = await llm.complete_json(
                system=VERDICT_SYSTEM,
                messages=[{"role": "user", "content": prompt_content}],
                max_tokens=4096,
            )

            verdict = _parse_verdict(raw, len(citations), conflicts)
            if verdict:
                return verdict

        except Exception:
            logger.exception(f"Verdict generation attempt {attempt + 1} failed")

    # Fallback: KILL with insufficient evidence
    return Verdict(
        decision=VerdictDecision.KILL,
        reasons=[EvidencedClaim(
            text="Insufficient evidence to evaluate idea",
            citation_indices=[0] if citations else [0],
        )],
        risks=[EvidencedClaim(
            text="Analysis could not be completed",
            citation_indices=[0] if citations else [0],
        )],
        narrowest_wedge="Unable to determine",
        what_would_change="More evidence from targeted research",
        conflicts=conflicts,
    )


def _parse_verdict(
    raw: dict, pack_size: int, conflicts: list[ConflictReport]
) -> Verdict | None:
    """Parse raw verdict output."""
    try:
        decision_str = raw.get("decision", "KILL").upper()
        try:
            decision = VerdictDecision(decision_str)
        except ValueError:
            decision = VerdictDecision.KILL

        def parse_claims(key: str) -> list[EvidencedClaim]:
            claims = []
            for item in raw.get(key, []):
                if isinstance(item, dict):
                    text = item.get("text", "")
                    indices = [i for i in item.get("citation_indices", []) if 0 <= i < pack_size]
                    if text and indices:
                        claims.append(EvidencedClaim(text=text, citation_indices=indices))
                elif isinstance(item, str):
                    claims.append(EvidencedClaim(text=item, citation_indices=[0]))
            return claims

        reasons = parse_claims("reasons")
        risks = parse_claims("risks")

        if not reasons:
            reasons = [EvidencedClaim(text="No specific reasons provided", citation_indices=[0])]
        if not risks:
            risks = [EvidencedClaim(text="No specific risks identified", citation_indices=[0])]

        return Verdict(
            decision=decision,
            reasons=reasons[:5],
            risks=risks[:5],
            narrowest_wedge=raw.get("narrowest_wedge", "Unknown"),
            what_would_change=raw.get("what_would_change", "Unknown"),
            conflicts=conflicts,
        )
    except Exception:
        logger.exception("Failed to parse verdict")
        return None


async def generate_validation_plan(
    verdict: Verdict,
    clusters: list[PainCluster],
    idea: str,
    options: dict,
    llm: LLMProvider,
) -> ValidationPlan:
    """Generate 7-day validation plan. Mandatory for ALL verdicts."""
    top_clusters_text = "\n".join(
        f"- {c.statement.text} (confidence={c.confidence:.2f})"
        for c in sorted(clusters, key=lambda x: x.confidence, reverse=True)[:5]
    )

    prompt_content = VALIDATION_PLAN_USER.format(
        verdict_decision=verdict.decision.value,
        idea=idea,
        top_clusters=top_clusters_text or "No clusters identified",
        narrowest_wedge=verdict.narrowest_wedge,
        what_would_change=verdict.what_would_change,
    )

    for attempt in range(MAX_RETRIES + 1):
        try:
            raw = await llm.complete_json(
                system=VALIDATION_PLAN_SYSTEM,
                messages=[{"role": "user", "content": prompt_content}],
                max_tokens=4096,
            )

            plan = _parse_validation_plan(raw, verdict.decision)
            if plan:
                return plan

        except Exception:
            logger.exception(f"Validation plan attempt {attempt + 1} failed")

    # Fallback plan
    return ValidationPlan(
        verdict_context=verdict.decision,
        objective="Collect evidence to validate or invalidate this idea",
        channels=["Reddit", "LinkedIn", "Industry forums"],
        outreach_targets=["Identify 20 potential users in target market"],
        interview_script="What is the hardest part of [workflow]? How do you currently handle it?",
        landing_page_hypotheses=[],
        concierge_procedure="",
        success_threshold="3 people willing to pay for a solution",
        reversal_criteria="Strong payability signals from 5+ sources" if verdict.decision == VerdictDecision.KILL else None,
    )


def _parse_validation_plan(raw: dict, decision: VerdictDecision) -> ValidationPlan | None:
    """Parse raw validation plan output."""
    try:
        return ValidationPlan(
            verdict_context=decision,
            objective=raw.get("objective", "Validate idea"),
            channels=raw.get("channels", []),
            outreach_targets=raw.get("outreach_targets", []),
            interview_script=raw.get("interview_script", ""),
            landing_page_hypotheses=raw.get("landing_page_hypotheses", []),
            concierge_procedure=raw.get("concierge_procedure", ""),
            success_threshold=raw.get("success_threshold", ""),
            reversal_criteria=raw.get("reversal_criteria"),
        )
    except Exception:
        logger.exception("Failed to parse validation plan")
        return None
