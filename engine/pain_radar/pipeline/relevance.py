"""Topic relevance check + URL dedup — gates off-topic evidence before analysis."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

from pain_radar.core.models import Citation

logger = logging.getLogger(__name__)

# Generic words that cause false-positive relevance matches
_RELEVANCE_STOPWORDS = frozenset({
    "quote", "tool", "form", "data", "plan", "team", "work",
    "cost", "time", "help", "free", "best", "easy", "fast",
    "good", "user", "need", "want", "find", "make",
})


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

    min_matches = 2 if len(normalized_keywords) >= 3 else 1

    for i, citation in enumerate(citations):
        # Prefer snapshot raw_text, fall back to excerpt
        text = snapshot_text_by_hash.get(citation.snapshot_hash, "")
        if not text:
            text = citation.excerpt.lower()

        # Count how many keywords (or significant substrings) match
        matches = 0
        for kw in normalized_keywords:
            kw_words = kw.split()
            # Skip keywords that consist entirely of stopwords/short words
            significant = [w for w in kw_words if len(w) >= 5 and w not in _RELEVANCE_STOPWORDS]
            if kw in text and (significant or len(kw_words) > 1):
                # Full keyword match, but only count if it has substance
                matches += 1
                continue
            if significant and any(word in text for word in significant):
                matches += 1

        if matches >= min_matches:
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
