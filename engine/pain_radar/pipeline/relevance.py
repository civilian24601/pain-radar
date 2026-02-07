"""Topic relevance check + URL dedup — gates off-topic evidence before analysis."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

from pain_radar.core.models import Citation

logger = logging.getLogger(__name__)


@dataclass
class TopicRelevanceResult:
    """Per-citation topic relevance breakdown."""

    ratio: float  # fraction of on-topic citations
    on_topic_indices: list[int] = field(default_factory=list)
    off_topic_indices: list[int] = field(default_factory=list)


def compute_topic_relevance(
    citations: list[Citation],
    snapshots: list[dict],
    keywords: list[str],
) -> TopicRelevanceResult:
    """Compute what fraction of citations are topically relevant.

    Checks each citation's corresponding snapshot raw_text (falling back to
    excerpt) for keyword matches. Returns a structured result with per-citation
    on/off-topic classification.

    Args:
        citations: All collected citations.
        snapshots: List of dicts with 'content_hash' and 'raw_text'.
        keywords: Extracted search keywords from the idea.
    """
    if not citations or not keywords:
        return TopicRelevanceResult(
            ratio=0.0,
            off_topic_indices=list(range(len(citations))),
        )

    # Build lookup: hash → raw_text
    snapshot_text_by_hash: dict[str, str] = {
        s["content_hash"]: s["raw_text"].lower()
        for s in snapshots
        if s.get("content_hash") and s.get("raw_text")
    }

    # Normalize keywords + build substrings for partial matching
    normalized_keywords: list[str] = []
    for kw in keywords:
        kw_lower = kw.lower().strip()
        if kw_lower:
            normalized_keywords.append(kw_lower)

    if not normalized_keywords:
        return TopicRelevanceResult(
            ratio=0.0,
            off_topic_indices=list(range(len(citations))),
        )

    on_topic: list[int] = []
    off_topic: list[int] = []

    for i, citation in enumerate(citations):
        # Prefer snapshot raw_text, fall back to excerpt
        text = snapshot_text_by_hash.get(citation.snapshot_hash, "")
        if not text:
            text = citation.excerpt.lower()

        # Check if any keyword (or significant substring) appears
        hit = False
        for kw in normalized_keywords:
            if kw in text:
                hit = True
                break
            # Also check substrings >= 4 chars (handles multi-word keywords)
            kw_words = kw.split()
            if any(word in text for word in kw_words if len(word) >= 4):
                hit = True
                break

        if hit:
            on_topic.append(i)
        else:
            off_topic.append(i)

    ratio = len(on_topic) / len(citations)
    return TopicRelevanceResult(
        ratio=ratio,
        on_topic_indices=on_topic,
        off_topic_indices=off_topic,
    )


def deduplicate_citations(citations: list[Citation]) -> list[Citation]:
    """Collapse multiple citations from the same URL into one per URL.

    Keeps the citation with the longest excerpt for each URL.
    This prevents a single page (e.g. G2 editorial) from appearing as
    15 separate evidence points.
    """
    best_by_url: dict[str, Citation] = {}
    for c in citations:
        existing = best_by_url.get(c.url)
        if existing is None or len(c.excerpt) > len(existing.excerpt):
            best_by_url[c.url] = c

    deduped = list(best_by_url.values())
    removed = len(citations) - len(deduped)
    if removed > 0:
        logger.info(
            f"URL dedup: {len(citations)} → {len(deduped)} citations "
            f"({removed} duplicate-URL citations collapsed)"
        )
    return deduped
