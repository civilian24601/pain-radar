"""Source snapshot — fetch and store raw HTML/text per URL."""

from __future__ import annotations

import hashlib
import logging
from datetime import datetime, timezone
from pathlib import Path

import httpx
from bs4 import BeautifulSoup

from pain_radar.core.models import SourceSnapshot

logger = logging.getLogger(__name__)

_HTTP_TIMEOUT = 15.0
_MAX_CONTENT_LENGTH = 500_000  # 500KB text limit per snapshot


async def fetch_and_store(
    url: str,
    snapshots_dir: Path,
    client: httpx.AsyncClient | None = None,
) -> SourceSnapshot | None:
    """Fetch a URL, extract text, store raw content, return snapshot."""
    own_client = client is None
    if own_client:
        client = httpx.AsyncClient(
            timeout=_HTTP_TIMEOUT,
            follow_redirects=True,
            headers={"User-Agent": "PainRadar/0.1 (research tool)"},
        )

    try:
        response = await client.get(url)
        response.raise_for_status()
    except (httpx.HTTPError, httpx.TimeoutException) as e:
        logger.warning(f"Failed to fetch {url}: {e}")
        return None
    finally:
        if own_client:
            await client.aclose()

    raw_bytes = response.content
    content_hash = hashlib.sha256(raw_bytes).hexdigest()

    # Extract text from HTML
    content_type = response.headers.get("content-type", "")
    if "html" in content_type:
        soup = BeautifulSoup(raw_bytes, "html.parser")
        # Remove script and style elements
        for tag in soup(["script", "style", "nav", "footer", "header"]):
            tag.decompose()
        raw_text = soup.get_text(separator="\n", strip=True)
    else:
        raw_text = response.text

    # Truncate if too large
    if len(raw_text) > _MAX_CONTENT_LENGTH:
        raw_text = raw_text[:_MAX_CONTENT_LENGTH]

    # Store raw file
    snapshots_dir.mkdir(parents=True, exist_ok=True)
    storage_path = snapshots_dir / f"{content_hash}.txt"
    storage_path.write_text(raw_text, encoding="utf-8")

    return SourceSnapshot(
        url=url,
        content_hash=content_hash,
        raw_text=raw_text,
        fetched_at=datetime.now(timezone.utc).isoformat(),
        storage_path=str(storage_path),
    )
