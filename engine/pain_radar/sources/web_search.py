"""Web search source pack — Serper.dev with DuckDuckGo fallback."""

from __future__ import annotations

import asyncio
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
        serper_sem = asyncio.Semaphore(5)
        fetch_sem = asyncio.Semaphore(10)

        async with httpx.AsyncClient(
            timeout=15.0,
            follow_redirects=True,
            headers={"User-Agent": "PainRadar/0.1 (research tool)"},
        ) as client:

            async def _run_query(query: str) -> list[Citation]:
                query_citations: list[Citation] = []
                try:
                    if settings.has_serper:
                        async with serper_sem:
                            results = await _serper_search(
                                query, settings.serper_api_key,
                                settings.search_recency, client=client,
                            )
                    else:
                        results = await _duckduckgo_search(query)

                    async def _fetch_one(result: dict) -> Citation | None:
                        url = result.get("link") or result.get("url", "")
                        if not url:
                            return None
                        async with fetch_sem:
                            snapshot = await fetch_and_store(
                                url, settings.snapshots_dir, client
                            )
                        if not snapshot:
                            return None
                        snippet = result.get("snippet", "")
                        if snippet and snippet in snapshot.raw_text:
                            return Citation(
                                url=url,
                                excerpt=snippet,
                                source_type=SourceType.WEB,
                                date_published=result.get("date"),
                                date_retrieved=datetime.now(timezone.utc).isoformat(),
                                recency_months=None,
                                snapshot_hash=snapshot.content_hash,
                            )
                        return None

                    fetched = await asyncio.gather(
                        *[_fetch_one(r) for r in results[:5]]
                    )
                    query_citations = [c for c in fetched if c is not None]

                except Exception:
                    logger.exception(f"Web search failed for query: {query}")

                return query_citations

            all_results = await asyncio.gather(*[_run_query(q) for q in queries])

        citations: list[Citation] = []
        for batch in all_results:
            citations.extend(batch)
        return citations


async def _serper_search(
    query: str, api_key: str, tbs: str = "",
    client: httpx.AsyncClient | None = None,
) -> list[dict]:
    """Search via Serper.dev API."""
    payload: dict = {"q": query, "num": 10}
    if tbs:
        payload["tbs"] = tbs
    own_client = client is None
    if own_client:
        client = httpx.AsyncClient(timeout=10.0)
    try:
        response = await client.post(
            "https://google.serper.dev/search",
            headers={"X-API-KEY": api_key, "Content-Type": "application/json"},
            json=payload,
        )
        response.raise_for_status()
        data = response.json()
        return data.get("organic", [])
    finally:
        if own_client:
            await client.aclose()


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
