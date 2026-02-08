"""Web search source pack — Serper.dev with DuckDuckGo fallback."""

from __future__ import annotations

import logging
from datetime import datetime, timezone

import httpx

from pain_radar.core.config import Settings
from pain_radar.core.models import Citation, SourceType
from pain_radar.sources.base import SourcePack
from pain_radar.sources.snapshot import fetch_and_store

logger = logging.getLogger(__name__)


class WebSearchSourcePack(SourcePack):
    @property
    def name(self) -> str:
        return "web"

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
                if settings.has_serper:
                    results = await _serper_search(
                        query, settings.serper_api_key, settings.search_recency,
                    )
                else:
                    results = await _duckduckgo_search(query)

                # Fetch and snapshot each result
                async with httpx.AsyncClient(
                    timeout=15.0,
                    follow_redirects=True,
                    headers={"User-Agent": "PainRadar/0.1 (research tool)"},
                ) as client:
                    for result in results[:5]:  # Top 5 per query
                        url = result.get("link") or result.get("url", "")
                        if not url:
                            continue

                        snapshot = await fetch_and_store(
                            url, settings.snapshots_dir, client
                        )
                        if not snapshot:
                            continue

                        # Use the search snippet as a pointer, but the real
                        # evidence must come from the snapshot via LLM extraction.
                        # For now, store the snippet as the initial excerpt.
                        snippet = result.get("snippet", "")
                        if snippet and snippet in snapshot.raw_text:
                            citations.append(Citation(
                                url=url,
                                excerpt=snippet,
                                source_type=SourceType.WEB,
                                date_published=result.get("date"),
                                date_retrieved=datetime.now(timezone.utc).isoformat(),
                                recency_months=None,
                                snapshot_hash=snapshot.content_hash,
                            ))

            except Exception:
                logger.exception(f"Web search failed for query: {query}")

        return citations


async def _serper_search(query: str, api_key: str, tbs: str = "") -> list[dict]:
    """Search via Serper.dev API."""
    payload: dict = {"q": query, "num": 10}
    if tbs:
        payload["tbs"] = tbs
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.post(
            "https://google.serper.dev/search",
            headers={"X-API-KEY": api_key, "Content-Type": "application/json"},
            json=payload,
        )
        response.raise_for_status()
        data = response.json()
        return data.get("organic", [])


async def _duckduckgo_search(query: str) -> list[dict]:
    """Search via DuckDuckGo (free, no API key)."""
    try:
        from duckduckgo_search import AsyncDDGS
        async with AsyncDDGS() as ddgs:
            results = await ddgs.atext(query, max_results=10)
            return [
                {"link": r.get("href", ""), "snippet": r.get("body", ""), "url": r.get("href", "")}
                for r in results
            ]
    except Exception:
        logger.exception("DuckDuckGo search failed")
        return []
