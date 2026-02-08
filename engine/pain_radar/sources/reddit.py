"""Reddit source pack — API for posts+comments, web search for discovery only."""

from __future__ import annotations

import logging
import re
from datetime import datetime, timezone

import httpx
from bs4 import BeautifulSoup

from pain_radar.core.config import Settings
from pain_radar.core.models import Citation, SourceType
from pain_radar.sources.base import SourcePack
from pain_radar.sources.snapshot import fetch_and_store

logger = logging.getLogger(__name__)

_REDDIT_THREAD_PATTERN = re.compile(
    r"https?://(?:www\.)?reddit\.com/r/\w+/comments/\w+"
)


class RedditSourcePack(SourcePack):
    @property
    def name(self) -> str:
        return "reddit"

    async def search(
        self,
        queries: list[str],
        idea: str,
        keywords: list[str],
        settings: Settings,
    ) -> list[Citation]:
        # Phase 1: DISCOVERY — find Reddit thread URLs via web search
        thread_urls = await _discover_threads(queries, settings)
        logger.info(f"Reddit discovery found {len(thread_urls)} threads")

        if not thread_urls:
            return []

        # Phase 2: FETCH — get actual post + comments content
        citations: list[Citation] = []
        for url in thread_urls[:15]:  # Cap at 15 threads
            try:
                if settings.has_reddit:
                    snapshot = await _fetch_via_api(url, settings)
                else:
                    snapshot = await _fetch_via_html(url, settings)

                if not snapshot:
                    continue

                # Extract evidence from the snapshot text
                # For now, take meaningful chunks; LLM extraction refines later
                chunks = _extract_meaningful_chunks(snapshot.raw_text)
                for chunk in chunks:
                    citations.append(Citation(
                        url=url,
                        excerpt=chunk,
                        source_type=SourceType.REDDIT,
                        date_published=None,
                        date_retrieved=datetime.now(timezone.utc).isoformat(),
                        recency_months=None,
                        snapshot_hash=snapshot.content_hash,
                    ))

            except Exception:
                logger.exception(f"Reddit fetch failed for: {url}")

        return citations


async def _discover_threads(queries: list[str], settings: Settings) -> list[str]:
    """Use web search to discover Reddit thread URLs. SERP snippets NOT used as evidence."""
    urls: list[str] = []
    seen: set[str] = set()

    for query in queries:
        try:
            if settings.has_serper:
                results = await _serper_reddit_search(
                    query, settings.serper_api_key, settings.search_recency,
                )
            else:
                results = await _ddg_reddit_search(query)

            for r in results:
                url = r.get("link") or r.get("url", "")
                # Normalize to canonical thread URL
                match = _REDDIT_THREAD_PATTERN.search(url)
                if match:
                    canonical = match.group(0)
                    if canonical not in seen:
                        seen.add(canonical)
                        urls.append(canonical)
        except Exception:
            logger.exception(f"Reddit discovery failed for query: {query}")

    return urls


async def _serper_reddit_search(query: str, api_key: str, tbs: str = "") -> list[dict]:
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
        return response.json().get("organic", [])


async def _ddg_reddit_search(query: str) -> list[dict]:
    try:
        from duckduckgo_search import AsyncDDGS
        async with AsyncDDGS() as ddgs:
            results = await ddgs.atext(query, max_results=10)
            return [{"url": r.get("href", "")} for r in results]
    except Exception:
        logger.exception("DuckDuckGo Reddit search failed")
        return []


async def _fetch_via_api(url: str, settings: Settings):
    """Fetch Reddit post + top comments via Reddit API."""
    from pain_radar.sources.snapshot import SourceSnapshot
    import hashlib

    # Extract post ID from URL
    match = re.search(r"/comments/(\w+)", url)
    if not match:
        return None

    post_id = match.group(1)

    # Get OAuth token
    async with httpx.AsyncClient(timeout=10.0) as client:
        auth_resp = await client.post(
            "https://www.reddit.com/api/v1/access_token",
            auth=(settings.reddit_client_id, settings.reddit_client_secret),
            data={"grant_type": "client_credentials"},
            headers={"User-Agent": "PainRadar/0.1"},
        )
        auth_resp.raise_for_status()
        token = auth_resp.json()["access_token"]

        # Fetch post + comments
        resp = await client.get(
            f"https://oauth.reddit.com/comments/{post_id}?limit=25&sort=top",
            headers={
                "Authorization": f"Bearer {token}",
                "User-Agent": "PainRadar/0.1",
            },
        )
        resp.raise_for_status()
        data = resp.json()

    # Build text from post + comments
    lines = []
    if isinstance(data, list) and len(data) >= 1:
        post_data = data[0].get("data", {}).get("children", [{}])
        if post_data:
            post = post_data[0].get("data", {})
            lines.append(f"TITLE: {post.get('title', '')}")
            lines.append(f"BODY: {post.get('selftext', '')}")
            lines.append(f"SCORE: {post.get('score', 0)}")
            lines.append(f"CREATED: {post.get('created_utc', '')}")
            lines.append("")

        if len(data) >= 2:
            comments = data[1].get("data", {}).get("children", [])
            for c in comments[:25]:
                cd = c.get("data", {})
                if cd.get("body"):
                    lines.append(f"COMMENT (score {cd.get('score', 0)}):")
                    lines.append(cd["body"])
                    lines.append("")

    raw_text = "\n".join(lines)
    content_hash = hashlib.sha256(raw_text.encode()).hexdigest()

    # Store snapshot
    snapshot_path = settings.snapshots_dir / f"{content_hash}.txt"
    settings.snapshots_dir.mkdir(parents=True, exist_ok=True)
    snapshot_path.write_text(raw_text, encoding="utf-8")

    return SourceSnapshot(
        url=url,
        content_hash=content_hash,
        raw_text=raw_text,
        fetched_at=datetime.now(timezone.utc).isoformat(),
        storage_path=str(snapshot_path),
    )


async def _fetch_via_html(url: str, settings: Settings):
    """Fallback: fetch Reddit thread HTML directly."""
    # Use old.reddit.com for simpler HTML
    old_url = url.replace("www.reddit.com", "old.reddit.com")
    return await fetch_and_store(old_url, settings.snapshots_dir)


def _extract_meaningful_chunks(text: str, min_length: int = 50) -> list[str]:
    """Extract meaningful text chunks from Reddit post/comment text."""
    chunks: list[str] = []
    # Split by double newlines to get paragraphs
    paragraphs = text.split("\n\n")
    for p in paragraphs:
        p = p.strip()
        if len(p) >= min_length:
            # Cap individual chunk length
            if len(p) > 500:
                p = p[:500]
            chunks.append(p)
    return chunks[:20]  # Cap total chunks per thread
