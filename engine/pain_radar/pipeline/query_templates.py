"""Deterministic query templates + LLM keyword refinement.

NOT pure LLM generation. Templates ensure stability; LLM only extracts
keywords and optionally adds 1-2 niche-specific queries per pack.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from pain_radar.llm.prompts import (
    KEYWORD_EXTRACTION_SYSTEM,
    KEYWORD_EXTRACTION_USER,
    NICHE_QUERY_SYSTEM,
    NICHE_QUERY_USER,
)

if TYPE_CHECKING:
    from pain_radar.llm.base import LLMProvider

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Deterministic templates — keywords are slotted in
# ---------------------------------------------------------------------------

REDDIT_TEMPLATES = [
    '"{keyword}" site:reddit.com pain OR frustrating OR broken OR hate',
    '"{keyword}" site:reddit.com looking for OR need OR alternative',
    '"{keyword}" site:reddit.com paying OR cost OR expensive OR budget',
]

COMPETITOR_TEMPLATES = [
    '"{keyword}" alternatives comparison',
    '"{keyword}" pricing page',
    '"{keyword}" vs',
]

REVIEW_TEMPLATES = [
    '"{keyword}" reviews G2 OR Capterra',
    '"{keyword}" complaints OR issues OR problems',
]

HIRING_TEMPLATES = [
    '"{keyword}" hiring OR job posting',
    '"{keyword}" freelancer OR contractor OR agency',
    '"{keyword}" "looking to hire" OR "need someone" OR "job description"',
    '"{keyword}" salary OR compensation OR "full-time" role',
]

# Tools/substitutes reality check — appended to web pack for ALL ideas
TOOLS_REALITY_TEMPLATES = [
    '"{keyword}" currently using OR "we use" OR "switched from"',
    '"{keyword}" spreadsheet OR manual OR "no tool" workaround',
    '"{keyword}" alternative to OR replacement for',
]

# ---------------------------------------------------------------------------
# Niche-specific templates — activated by keyword match on niche/idea
# ---------------------------------------------------------------------------

NICHE_TEMPLATES: dict[str, dict[str, list[str]]] = {
    "podcast": {
        "reddit": [
            '"podcast guest booking" site:reddit.com frustrating OR manual OR tedious',
            '"podcast outreach" OR "guest scheduling" site:reddit.com',
            '"guest intake form" podcast site:reddit.com',
            'site:reddit.com/r/podcasting guest booking OR outreach OR scheduling',
            'site:reddit.com/r/podcastguestexchange booking workflow',
        ],
        "web": [
            '"podcast guest booking" software OR tool OR platform',
            '"podcast guest management" airtable OR notion OR spreadsheet',
            '"podcast guest" outreach template OR workflow',
            'PodMatch OR MatchMaker.fm OR PodcastGuests review',
            'Rephonic OR "Listen Notes" podcast research tool',
            '"PR pitching podcasts" workflow OR process',
        ],
        "review": [
            '"podcast booking" OR "podcast scheduling" reviews complaints',
            'PodMatch review OR MatchMaker.fm review',
        ],
        "hiring": [
            '"podcast booker" hiring OR job',
            '"podcast booking assistant" job OR role',
            '"guest outreach specialist" podcast',
            '"podcast producer" guest booking',
            '"PR agency" podcast pitching',
        ],
    },
}


def _expand_templates(
    templates: list[str], keywords: list[str]
) -> list[str]:
    """Slot keywords into templates."""
    queries = []
    for template in templates:
        for keyword in keywords:
            queries.append(template.replace("{keyword}", keyword))
    return queries


async def generate_queries(
    idea: str,
    options: dict,
    llm: LLMProvider,
) -> dict[str, list[str]]:
    """Generate search queries: deterministic templates + LLM refinement.

    Returns dict with keys: "reddit", "web", "review", "hiring", "_keywords", "_idea"
    """
    # Step 1: Extract keywords via LLM (constrained to 3-5)
    niche = options.get("niche", "")
    geography = options.get("geography", "")
    buyer_role = options.get("buyer_role", "")

    try:
        keywords = await llm.complete_json(
            system=KEYWORD_EXTRACTION_SYSTEM,
            messages=[{
                "role": "user",
                "content": KEYWORD_EXTRACTION_USER.format(
                    idea=idea, niche=niche or "N/A",
                    geography=geography or "N/A", buyer_role=buyer_role or "N/A",
                ),
            }],
        )
        if not isinstance(keywords, list) or not keywords:
            keywords = [idea[:50]]
        keywords = keywords[:5]  # Hard cap at 5
    except Exception:
        logger.exception("Keyword extraction failed, using idea text")
        keywords = [idea[:50]]

    logger.info(f"Extracted keywords: {keywords}")

    # Step 2: Expand deterministic templates
    queries = {
        "reddit": _expand_templates(REDDIT_TEMPLATES, keywords),
        "web": _expand_templates(COMPETITOR_TEMPLATES, keywords),
        "review": _expand_templates(REVIEW_TEMPLATES, keywords),
        "hiring": _expand_templates(HIRING_TEMPLATES, keywords),
        "_keywords": keywords,
        "_idea": idea,
    }

    # Step 2b: Add tools/reality templates to web pack (all ideas)
    queries["web"].extend(_expand_templates(TOOLS_REALITY_TEMPLATES, keywords))

    # Step 2c: Add niche-specific templates if niche/idea matches
    niche_text = f"{niche} {idea}".lower()
    for niche_key, niche_packs in NICHE_TEMPLATES.items():
        if niche_key in niche_text:
            for pack_name, templates in niche_packs.items():
                if pack_name in queries:
                    queries[pack_name].extend(
                        _expand_templates(templates, keywords)
                    )
            logger.info(f"Activated niche templates: {niche_key}")

    # Step 3: LLM adds 1-2 niche-specific queries per pack (optional)
    try:
        niche_queries = await llm.complete_json(
            system=NICHE_QUERY_SYSTEM,
            messages=[{
                "role": "user",
                "content": NICHE_QUERY_USER.format(
                    keywords=", ".join(keywords),
                    idea=idea,
                    niche=niche or "general",
                ),
            }],
        )
        if isinstance(niche_queries, dict):
            for pack_name, extra_queries in niche_queries.items():
                if pack_name in queries and isinstance(extra_queries, list):
                    # Hard cap: only add up to 2 niche queries per pack
                    queries[pack_name].extend(extra_queries[:2])
    except Exception:
        logger.warning("Niche query refinement failed, using templates only")

    return queries
