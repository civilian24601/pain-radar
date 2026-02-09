"""Intake — generate structured idea brief from raw idea text."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from pain_radar.core.models import IdeaBrief
from pain_radar.llm.prompts import IDEA_BRIEF_SYSTEM, IDEA_BRIEF_USER

if TYPE_CHECKING:
    from pain_radar.llm.base import LLMProvider

logger = logging.getLogger(__name__)

_MAX_RETRIES = 1  # 1 attempt + 1 retry — fast, low-stakes


async def generate_idea_brief(
    idea: str,
    options: dict,
    llm: LLMProvider,
) -> IdeaBrief:
    """Generate structured idea brief via LLM. Falls back to placeholder on failure.

    Returns a proper IdeaBrief with workflow_verbs and incumbent_tools populated
    when the LLM succeeds. On failure, returns a minimal placeholder so the
    pipeline can proceed with keyword-only queries (identical to prior behavior).
    """
    niche = options.get("niche", "")
    buyer_role = options.get("buyer_role", "")

    for attempt in range(_MAX_RETRIES + 1):
        try:
            raw = await llm.complete_json(
                system=IDEA_BRIEF_SYSTEM,
                messages=[{
                    "role": "user",
                    "content": IDEA_BRIEF_USER.format(
                        idea=idea,
                        niche=niche or "N/A",
                        buyer_role=buyer_role or "N/A",
                    ),
                }],
                max_tokens=2048,
            )

            if not isinstance(raw, dict):
                logger.warning(f"IdeaBrief attempt {attempt + 1}: expected dict, got {type(raw)}")
                continue

            # Extract keywords from options or raw
            keywords = raw.get("keywords") or [idea[:50]]
            if isinstance(keywords, str):
                keywords = [keywords]
            keywords = keywords[:10] or [idea[:50]]

            # Parse workflow_verbs — ensure list of strings
            workflow_verbs = raw.get("workflow_verbs", [])
            if not isinstance(workflow_verbs, list):
                workflow_verbs = []
            workflow_verbs = [str(v) for v in workflow_verbs if v][:5]

            # Parse incumbent_tools — ensure list of strings
            incumbent_tools = raw.get("incumbent_tools", [])
            if not isinstance(incumbent_tools, list):
                incumbent_tools = []
            incumbent_tools = [str(t) for t in incumbent_tools if t][:5]

            return IdeaBrief(
                raw_idea=idea,
                one_liner=raw.get("one_liner", idea[:200]),
                buyer_persona=raw.get("buyer_persona", buyer_role or "Unknown"),
                workflow_replaced=raw.get("workflow_replaced", "Unknown"),
                moment_of_pain=raw.get("moment_of_pain", "Unknown"),
                keywords=keywords,
                workflow_verbs=workflow_verbs,
                incumbent_tools=incumbent_tools,
            )

        except Exception:
            logger.exception(f"IdeaBrief generation attempt {attempt + 1} failed")

    # Fallback: minimal placeholder, pipeline proceeds with keyword-only queries
    logger.warning("IdeaBrief generation exhausted retries, using placeholder")
    return IdeaBrief(
        raw_idea=idea,
        one_liner=idea[:200],
        buyer_persona=options.get("buyer_role") or "Unknown",
        workflow_replaced="Unknown",
        moment_of_pain="Unknown",
        keywords=[idea[:50]],
        workflow_verbs=[],
        incumbent_tools=[],
    )
