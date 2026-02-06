"""Skeptic pass — red team review of the full report."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from pain_radar.core.models import Citation, ResearchReport
from pain_radar.llm.prompts import SKEPTIC_SYSTEM, SKEPTIC_USER

if TYPE_CHECKING:
    from pain_radar.llm.base import LLMProvider

logger = logging.getLogger(__name__)


async def run_skeptic_pass(
    report: ResearchReport,
    citations: list[Citation],
    llm: LLMProvider,
) -> list[str]:
    """Run skeptic review on the full report. Returns list of flags."""
    # Serialize report to JSON for review (exclude heavy fields)
    report_dict = report.model_dump()
    # Remove raw snapshot data to keep prompt manageable
    if "source_snapshots" in report_dict:
        del report_dict["source_snapshots"]

    import json
    report_json = json.dumps(report_dict, indent=2, default=str)

    # Truncate if too long for context
    if len(report_json) > 30000:
        report_json = report_json[:30000] + "\n... (truncated)"

    try:
        raw = await llm.complete_json(
            system=SKEPTIC_SYSTEM,
            messages=[{
                "role": "user",
                "content": SKEPTIC_USER.format(report_json=report_json),
            }],
            max_tokens=4096,
        )

        if isinstance(raw, list):
            return [str(flag) for flag in raw if flag]
        return []

    except Exception:
        logger.exception("Skeptic pass failed")
        return ["Skeptic pass could not be completed due to an error."]
