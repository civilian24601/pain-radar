"""Reviews source pack — G2/Capterra via web search + snapshot."""

from __future__ import annotations

import logging
from datetime import datetime, timezone

import httpx

from pain_radar.core.config import Settings
from pain_radar.core.models import Citation, SourceType
from pain_radar.sources.base import SourcePack
from pain_radar.sources.snapshot import fetch_and_store

logger = logging.getLogger(__name__)


class ReviewSourcePack(SourcePack):
    @property
    def name(self) -> str:
        return "review"

    async def search(
        self,
        queries: list[str],
        idea: str,
        keywords: list[str],
        settings: Settings,
    ) -> list[Citation]:
        citations: list[Citation] = []

        for query in queries:
            try:
                # Discover review pages via web search
                if settings.has_serper:
                    results = await _serper_search(query, settings.serper_api_key)
                else:
                    results = await _ddg_search(query)

                # Fetch and snapshot each review page
                async with httpx.AsyncClient(
                    timeout=15.0,
                    follow_redirects=True,
                    headers={"User-Agent": "PainRadar/0.1 (research tool)"},
                ) as client:
                    for result in results[:5]:
                        url = result.get("link") or result.get("url", "")
                        if not url:
                            continue

                        # Only process known review sites
                        if not _is_review_site(url):
                            continue

                        snapshot = await fetch_and_store(
                            url, settings.snapshots_dir, client
                        )
                        if not snapshot:
                            continue

                        # Extract review-like chunks from snapshot
                        chunks = _extract_review_chunks(snapshot.raw_text)
                        for chunk in chunks:
                            citations.append(Citation(
                                url=url,
                                excerpt=chunk,
                                source_type=SourceType.REVIEW,
                                date_published=result.get("date"),
                                date_retrieved=datetime.now(timezone.utc).isoformat(),
                                recency_months=None,
                                snapshot_hash=snapshot.content_hash,
                            ))

            except Exception:
                logger.exception(f"Review search failed for query: {query}")

        return citations


def _is_review_site(url: str) -> bool:
    """Check if URL is a known review/comparison site."""
    review_domains = [
        "g2.com", "capterra.com", "trustradius.com", "getapp.com",
        "sourceforge.net/software", "alternativeto.net",
        "producthunt.com", "trustpilot.com",
    ]
    return any(domain in url.lower() for domain in review_domains)


def _extract_review_chunks(text: str, min_length: int = 40) -> list[str]:
    """Extract review-like text chunks from review page content."""
    chunks: list[str] = []
    paragraphs = text.split("\n")
    for p in paragraphs:
        p = p.strip()
        if len(p) >= min_length:
            # Look for review-like content (opinions, complaints, praise)
            review_signals = [
                "love", "hate", "frustrat", "annoying", "great", "terrible",
                "wish", "need", "want", "miss", "broken", "slow", "fast",
                "expensive", "cheap", "worth", "recommend", "switch",
                "pros", "cons", "alternative", "compared to",
            ]
            if any(signal in p.lower() for signal in review_signals):
                if len(p) > 400:
                    p = p[:400]
                chunks.append(p)
    return chunks[:15]


async def _serper_search(query: str, api_key: str) -> list[dict]:
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.post(
            "https://google.serper.dev/search",
            headers={"X-API-KEY": api_key, "Content-Type": "application/json"},
            json={"q": query, "num": 10},
        )
        response.raise_for_status()
        return response.json().get("organic", [])


async def _ddg_search(query: str) -> list[dict]:
    try:
        from duckduckgo_search import AsyncDDGS
        async with AsyncDDGS() as ddgs:
            results = await ddgs.atext(query, max_results=10)
            return [{"url": r.get("href", ""), "link": r.get("href", ""), "snippet": r.get("body", "")} for r in results]
    except Exception:
        logger.exception("DuckDuckGo review search failed")
        return []
