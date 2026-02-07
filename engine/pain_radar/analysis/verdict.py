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


def _best_citation_indices(citations: list[Citation], n: int = 3) -> list[int]:
    """Pick up to *n* citation indices from diverse source types."""
    if not citations:
        return [0]
    seen_types: set[str] = set()
    picked: list[int] = []
    for i, c in enumerate(citations):
        stype = c.source_type.value if hasattr(c.source_type, "value") else str(c.source_type)
        if stype not in seen_types:
            picked.append(i)
            seen_types.add(stype)
            if len(picked) >= n:
                break
    # Fill remaining slots if we haven't reached n
    if len(picked) < n:
        for i in range(len(citations)):
            if i not in picked:
                picked.append(i)
                if len(picked) >= n:
                    break
    return picked or [0]


def _match_citation_to_text(text: str, citations: list[Citation]) -> list[int]:
    """Find the best-matching citation for a text string via word overlap."""
    if not citations:
        return [0]
    text_words = set(text.lower().split())
    best_idx = 0
    best_score = 0
    for i, c in enumerate(citations):
        excerpt_words = set(c.excerpt.lower().split())
        overlap = len(text_words & excerpt_words)
        if overlap > best_score:
            best_score = overlap
            best_idx = i
    return [best_idx]


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

            verdict = _parse_verdict(raw, len(citations), conflicts, citations)
            if verdict:
                return verdict

        except Exception:
            logger.exception(f"Verdict generation attempt {attempt + 1} failed")

    # Fallback: INSUFFICIENT_EVIDENCE when retries exhausted
    fallback_indices = _best_citation_indices(citations)
    return Verdict(
        decision=VerdictDecision.INSUFFICIENT_EVIDENCE,
        reasons=[EvidencedClaim(
            text="Insufficient evidence to evaluate idea after exhausting analysis retries",
            citation_indices=fallback_indices,
        )],
        risks=[EvidencedClaim(
            text="Analysis could not be completed; evidence may be off-topic or too sparse",
            citation_indices=fallback_indices,
        )],
        narrowest_wedge="Unable to determine",
        what_would_change="More evidence from targeted research",
        conflicts=conflicts,
    )


def _parse_verdict(
    raw: dict,
    pack_size: int,
    conflicts: list[ConflictReport],
    citations: list[Citation] | None = None,
) -> Verdict | None:
    """Parse raw verdict output."""
    try:
        decision_str = raw.get("decision", "KILL").upper()
        try:
            decision = VerdictDecision(decision_str)
        except ValueError:
            decision = VerdictDecision.KILL

        _citations = citations or []

        def parse_claims(key: str) -> list[EvidencedClaim]:
            claims = []
            for item in raw.get(key, []):
                if isinstance(item, dict):
                    text = item.get("text", "")
                    indices = [i for i in item.get("citation_indices", []) if 0 <= i < pack_size]
                    if text and indices:
                        claims.append(EvidencedClaim(text=text, citation_indices=indices))
                elif isinstance(item, str) and item.strip():
                    claims.append(EvidencedClaim(
                        text=item,
                        citation_indices=_match_citation_to_text(item, _citations),
                    ))
            return claims

        reasons = parse_claims("reasons")
        risks = parse_claims("risks")

        # Filter out meta-statements (about the analysis process, not the domain)
        meta_phrases = [
            "insufficient evidence",
            "evidence is too sparse",
            "no specific reasons",
            "evidence mix",
            "too thin",
            "analysis process",
            "evidence too sparse",
            "risk assessment incomplete",
        ]

        def is_meta_statement(text: str) -> bool:
            lower = text.lower()
            return any(p in lower for p in meta_phrases)

        reasons = [r for r in reasons if not is_meta_statement(r.text)]
        risks = [r for r in risks if not is_meta_statement(r.text)]

        fallback_indices = _best_citation_indices(_citations)
        if not reasons:
            # Generate a domain-grounded fallback by describing what the
            # closest evidence actually shows
            closest = _citations[fallback_indices[0]] if _citations else None
            if closest:
                fallback_text = (
                    f"Closest available evidence (citation [{fallback_indices[0]}]) "
                    f"discusses '{closest.excerpt[:100]}...' which does not "
                    f"demonstrate the workflow pain this idea targets"
                )
            else:
                fallback_text = "No evidence found describing the target workflow pain"
            reasons = [EvidencedClaim(
                text=fallback_text,
                citation_indices=fallback_indices,
            )]
        if not risks:
            risks = [EvidencedClaim(
                text=(
                    "No domain-specific risk signals found in the evidence — "
                    "the evidence set does not address this idea's workflow directly"
                ),
                citation_indices=fallback_indices,
            )]

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
        reversal_criteria=(
            "Strong payability signals from 5+ sources"
            if verdict.decision in {VerdictDecision.KILL, VerdictDecision.INSUFFICIENT_EVIDENCE}
            else None
        ),
    )


def _parse_validation_plan(raw: dict, decision: VerdictDecision) -> ValidationPlan | None:
    """Parse raw validation plan output."""
    try:
        success_threshold = raw.get("success_threshold", "")
        if not success_threshold:
            success_threshold = "Define measurable threshold after collecting evidence"

        return ValidationPlan(
            verdict_context=decision,
            objective=raw.get("objective", "Validate idea"),
            channels=raw.get("channels", []),
            outreach_targets=raw.get("outreach_targets", []),
            interview_script=raw.get("interview_script", ""),
            landing_page_hypotheses=raw.get("landing_page_hypotheses", []),
            concierge_procedure=raw.get("concierge_procedure", ""),
            success_threshold=success_threshold,
            reversal_criteria=raw.get("reversal_criteria"),
        )
    except Exception:
        logger.exception("Failed to parse validation plan")
        return None


def enforce_verdict_payability_consistency(
    verdict: Verdict,
    payability: PayabilityAssessment,
) -> PayabilityAssessment:
    """Cap payability when verdict contradicts it.

    - INSUFFICIENT_EVIDENCE: cap to "none" (can't assess payability without evidence)
    - KILL: cap to "weak" (if evidence is too weak for ADVANCE, payability can't
      be strong either — at best general market signals exist)
    """
    original = payability.overall_strength

    if verdict.decision == VerdictDecision.INSUFFICIENT_EVIDENCE:
        if original not in ("none",):
            return PayabilityAssessment(
                hiring_signals=payability.hiring_signals,
                outsourcing_signals=payability.outsourcing_signals,
                template_sop_signals=payability.template_sop_signals,
                overall_strength="none",
                summary=(
                    f"{payability.summary} "
                    f"[Capped from '{original}' to 'none': evidence is "
                    f"insufficient to assess idea-specific payability.]"
                ),
            )

    if verdict.decision == VerdictDecision.KILL:
        if original in ("strong", "moderate"):
            return PayabilityAssessment(
                hiring_signals=payability.hiring_signals,
                outsourcing_signals=payability.outsourcing_signals,
                template_sop_signals=payability.template_sop_signals,
                overall_strength="weak",
                summary=(
                    f"{payability.summary} "
                    f"[Capped from '{original}' to 'weak': if evidence "
                    f"supports KILL, idea-specific payability cannot be "
                    f"strong. General market signals may exist but are not "
                    f"idea-specific.]"
                ),
            )

    return payability
