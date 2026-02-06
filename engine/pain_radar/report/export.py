"""Export evidence pack as CSV or JSON."""

from __future__ import annotations

import csv
import io
import json

from pain_radar.core.models import Citation, ResearchReport


def export_json(citations: list[Citation]) -> str:
    """Export citations as JSON string."""
    return json.dumps(
        [c.model_dump() for c in citations],
        indent=2,
        default=str,
    )


def export_csv(citations: list[Citation]) -> str:
    """Export citations as CSV string."""
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "url", "excerpt", "source_type", "date_published",
        "date_retrieved", "recency_months", "snapshot_hash",
    ])
    for c in citations:
        writer.writerow([
            c.url, c.excerpt, c.source_type.value, c.date_published or "",
            c.date_retrieved, c.recency_months or "", c.snapshot_hash,
        ])
    return output.getvalue()


def export_full_report_json(report: ResearchReport) -> str:
    """Export the full report as JSON."""
    return report.model_dump_json(indent=2)
