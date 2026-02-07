"""Conflict detection — find contradictions in evidence."""

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
)
from pain_radar.llm.prompts import (
    CONFLICT_SYSTEM,
    CONFLICT_USER,
    format_evidence_summary,
)

if TYPE_CHECKING:
    from pain_radar.llm.base import LLMProvider

logger = logging.getLogger(__name__)


async def detect_conflicts(
    clusters: list[PainCluster],
    competitors: list[Competitor],
    citations: list[Citation],
    llm: LLMProvider,
) -> list[ConflictReport]:
    """Detect contradictions between clusters, competitors, and evidence."""
    evidence_dicts = [c.model_dump() for c in citations]
    evidence_summary = format_evidence_summary(evidence_dicts)

    clusters_summary = "\n".join(
        f"- [{c.id}] {c.statement.text} (who: {c.who}, citations: {c.citation_indices})"
        for c in clusters
    )

    competitors_summary = "\n".join(
        f"- {c.name} ({c.url}): {c.positioning} (citations: {c.citation_indices})"
        for c in competitors
    )

    prompt_content = CONFLICT_USER.format(
        clusters_summary=clusters_summary or "No clusters",
        competitors_summary=competitors_summary or "No competitors",
        count=len(citations),
        evidence_summary=evidence_summary,
    )

    for attempt in range(MAX_RETRIES + 1):
        try:
            raw = await llm.complete_json(
                system=CONFLICT_SYSTEM,
                messages=[{"role": "user", "content": prompt_content}],
                max_tokens=4096,
            )

            if not isinstance(raw, list):
                raw = []

            conflicts = []
            for item in raw:
                conflict = _parse_conflict(item, len(citations))
                if conflict:
                    conflicts.append(conflict)

            # Strong conflicts first
            conflicts.sort(key=lambda c: 0 if c.relevance == "strong" else 1)
            return conflicts

        except Exception:
            logger.exception(f"Conflict detection attempt {attempt + 1} failed")

    return []


def _parse_conflict(item: dict, pack_size: int) -> ConflictReport | None:
    """Parse a raw conflict dict into a ConflictReport."""
    try:
        description = item.get("description", "")
        if not description:
            return None

        side_a_raw = item.get("side_a", {})
        side_b_raw = item.get("side_b", {})

        def parse_side(side: dict) -> EvidencedClaim | None:
            text = side.get("text", "")
            indices = [i for i in side.get("citation_indices", []) if 0 <= i < pack_size]
            if text and indices:
                return EvidencedClaim(text=text, citation_indices=indices)
            return None

        side_a = parse_side(side_a_raw)
        side_b = parse_side(side_b_raw)

        if side_a and side_b:
            relevance_raw = item.get("relevance", "weak")
            relevance = relevance_raw if relevance_raw in ("strong", "weak") else "weak"
            return ConflictReport(
                description=description,
                side_a=side_a,
                side_b=side_b,
                relevance=relevance,
            )
        return None

    except Exception:
        logger.exception("Failed to parse conflict")
        return None
