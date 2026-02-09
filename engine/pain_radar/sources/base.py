"""Base source pack interface and evidence collection coordinator."""

from __future__ import annotations

import asyncio
import logging
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Awaitable, Callable

from pain_radar.core.models import Citation

if TYPE_CHECKING:
    from pain_radar.core.config import Settings
    from pain_radar.db import Database

logger = logging.getLogger(__name__)


class SourcePack(ABC):
    """Abstract interface for a source pack."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable name of this source pack."""
        ...

    @abstractmethod
    async def search(
        self,
        queries: list[str],
        idea: str,
        keywords: list[str],
        settings: Settings,
    ) -> list[Citation]:
        """Execute queries and return citations with snapshot hashes."""
        ...


async def collect_all_evidence(
    job_id: str,
    queries: dict[str, list[str]],
    db: Database,
    settings: Settings,
    progress_callback: Callable[[str, str], Awaitable[None]] | None = None,
) -> tuple[list[Citation], dict[str, object]]:
    """Run all source packs and collect evidence.

    Args:
        progress_callback: async callable(pack_name, status_message) for live progress.

    Returns (citations, snapshots_dict).
    """
    from pain_radar.sources.reddit import RedditSourcePack
    from pain_radar.sources.reviews import ReviewSourcePack
    from pain_radar.sources.web_search import WebSearchSourcePack

    keywords = queries.get("_keywords", [])
    idea = queries.get("_idea", "")

    packs: list[SourcePack] = [
        RedditSourcePack(),
        WebSearchSourcePack(),
        ReviewSourcePack(),
    ]

    # Build tasks for packs that have queries, skip empty ones
    async def _run_pack(pack: SourcePack) -> list[Citation]:
        pack_queries = queries.get(pack.name, [])
        if not pack_queries:
            if progress_callback:
                await progress_callback(pack.name, "skipped (no queries)")
            return []
        try:
            if progress_callback:
                await progress_callback(pack.name, f"searching ({len(pack_queries)} queries)")
            logger.info(f"Running source pack: {pack.name} with {len(pack_queries)} queries")
            citations = await pack.search(pack_queries, idea, keywords, settings)
            logger.info(f"Source pack {pack.name} found {len(citations)} citations")
            if progress_callback:
                await progress_callback(pack.name, f"done ({len(citations)} citations)")
            return citations
        except Exception:
            logger.exception(f"Source pack {pack.name} failed")
            if progress_callback:
                await progress_callback(pack.name, "failed")
            return []

    results = await asyncio.gather(*[_run_pack(p) for p in packs])

    all_citations: list[Citation] = []
    for pack_citations in results:
        all_citations.extend(pack_citations)

    # Store snapshots FIRST (citations have FK to snapshots)
    seen_hashes: set[str] = set()
    for citation in all_citations:
        if citation.snapshot_hash not in seen_hashes:
            snapshot_path = settings.snapshots_dir / f"{citation.snapshot_hash}.txt"
            if snapshot_path.exists():
                raw_text = snapshot_path.read_text(encoding="utf-8")
                await db.store_snapshot(
                    content_hash=citation.snapshot_hash,
                    url=citation.url,
                    raw_text=raw_text,
                    fetched_at=citation.date_retrieved,
                    storage_path=str(snapshot_path),
                )
            seen_hashes.add(citation.snapshot_hash)

    # Store citations in DB
    for citation in all_citations:
        await db.store_citation(
            job_id=job_id,
            url=citation.url,
            excerpt=citation.excerpt,
            source_type=citation.source_type.value,
            date_published=citation.date_published,
            date_retrieved=citation.date_retrieved,
            recency_months=citation.recency_months,
            snapshot_hash=citation.snapshot_hash,
        )

    return all_citations, {}
