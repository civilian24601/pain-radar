"""Research pipeline orchestrator — coordinates all stages of a research run."""

from __future__ import annotations

import asyncio
import json
import logging
import traceback
from typing import TYPE_CHECKING

from pain_radar.core.models import (
    ClarificationAnswer,
    JobProgress,
    JobStatus,
)

if TYPE_CHECKING:
    from pain_radar.core.config import Settings
    from pain_radar.db import Database

logger = logging.getLogger(__name__)


class ResearchOrchestrator:
    def __init__(self, db: Database, settings: Settings) -> None:
        self._db = db
        self._settings = settings
        self._tasks: dict[str, asyncio.Task] = {}

    def launch(self, job_id: str, idea: str, options: dict) -> None:
        """Start a research pipeline as a background asyncio task."""
        task = asyncio.create_task(self._run_pipeline(job_id, idea, options))
        self._tasks[job_id] = task
        task.add_done_callback(lambda t: self._tasks.pop(job_id, None))

    def resume_after_clarification(
        self, job_id: str, answers: list[ClarificationAnswer]
    ) -> None:
        """Resume pipeline after user provides clarification answers."""
        task = asyncio.create_task(
            self._run_pipeline_after_clarification(job_id, answers)
        )
        self._tasks[job_id] = task
        task.add_done_callback(lambda t: self._tasks.pop(job_id, None))

    async def _update_progress(
        self, job_id: str, stage: str, **kwargs: int | str
    ) -> None:
        progress = JobProgress(stage=stage, **kwargs)
        await self._db.update_job_progress(job_id, progress.model_dump())

    async def _run_pipeline(
        self, job_id: str, idea: str, options: dict
    ) -> None:
        """Execute the full 9-stage research pipeline."""
        try:
            # Stage 1: INTAKE
            await self._db.update_job_status(job_id, JobStatus.RESEARCHING.value)
            await self._update_progress(job_id, "intake", current_action="Parsing idea")

            # Initialize LLM provider
            from pain_radar.llm.base import create_provider
            llm = create_provider(self._settings)

            # Stage 2: QUERY GENERATION
            await self._update_progress(
                job_id, "query_generation", current_action="Generating search queries"
            )
            from pain_radar.pipeline.query_templates import generate_queries
            queries = await generate_queries(idea, options, llm)

            # Stage 3: EVIDENCE COLLECTION
            await self._update_progress(
                job_id, "evidence_collection",
                source_packs_total=4,
                source_packs_done=0,
                current_action="Collecting evidence from sources",
            )
            from pain_radar.sources.base import collect_all_evidence
            citations, snapshots = await collect_all_evidence(
                job_id=job_id,
                queries=queries,
                db=self._db,
                settings=self._settings,
                progress_callback=lambda done, found: asyncio.create_task(
                    self._update_progress(
                        job_id, "evidence_collection",
                        source_packs_total=4,
                        source_packs_done=done,
                        citations_found=found,
                    )
                ),
            )

            if not citations:
                await self._db.update_job_status(job_id, JobStatus.FAILED.value)
                await self._update_progress(
                    job_id, "failed",
                    current_action="No evidence found. Try a different idea or broader keywords.",
                )
                return

            # Stage 4: ANALYSIS
            await self._db.update_job_status(job_id, JobStatus.ANALYZING.value)
            await self._update_progress(
                job_id, "analysis",
                citations_found=len(citations),
                current_action="Clustering pain points",
            )

            from pain_radar.analysis.clustering import cluster_evidence
            clusters = await cluster_evidence(citations, idea, options, llm)

            await self._update_progress(
                job_id, "analysis",
                citations_found=len(citations),
                current_action="Scoring clusters",
            )
            from pain_radar.analysis.scoring import score_clusters
            scored_clusters = await score_clusters(clusters, citations, llm)

            await self._update_progress(
                job_id, "analysis",
                citations_found=len(citations),
                current_action="Analyzing competitors",
            )
            from pain_radar.analysis.clustering import extract_competitors
            competitors = await extract_competitors(citations, idea, options, llm)

            from pain_radar.analysis.scoring import assess_payability
            payability = await assess_payability(citations, idea, llm)

            # Stage 5: CONFLICT DETECTION
            await self._update_progress(
                job_id, "conflict_detection",
                citations_found=len(citations),
                current_action="Detecting conflicts",
            )
            from pain_radar.analysis.conflict import detect_conflicts
            conflicts = await detect_conflicts(scored_clusters, competitors, citations, llm)

            # Stage 6: VERDICT
            await self._update_progress(
                job_id, "verdict",
                citations_found=len(citations),
                current_action="Generating verdict",
            )
            from pain_radar.analysis.verdict import generate_verdict
            verdict = await generate_verdict(
                scored_clusters, competitors, payability, conflicts, citations, llm
            )

            # Stage 7: VALIDATION PLAN
            await self._update_progress(
                job_id, "validation_plan",
                citations_found=len(citations),
                current_action="Building 7-day validation plan",
            )
            from pain_radar.analysis.verdict import generate_validation_plan
            validation_plan = await generate_validation_plan(
                verdict, scored_clusters, idea, options, llm
            )

            # Stage 8: SKEPTIC PASS
            await self._db.update_job_status(job_id, JobStatus.REVIEWING.value)
            await self._update_progress(
                job_id, "skeptic_pass",
                citations_found=len(citations),
                current_action="Running skeptic review",
            )
            from pain_radar.analysis.skeptic import run_skeptic_pass

            # Build idea brief
            from pain_radar.core.models import IdeaBrief, ResearchReport
            idea_brief = IdeaBrief(
                raw_idea=idea,
                one_liner=idea[:200],
                buyer_persona=options.get("buyer_role", "Unknown"),
                workflow_replaced="Unknown",
                moment_of_pain="Unknown",
                keywords=queries.get("_keywords", ["unknown"]),
            )

            # Assemble report for skeptic pass
            report = ResearchReport(
                id=job_id,
                idea_brief=idea_brief,
                pain_map=scored_clusters,
                payability=payability,
                competitors=competitors,
                verdict=verdict,
                validation_plan=validation_plan,
                evidence_pack=citations,
                skeptic_flags=[],
                conflicts=conflicts,
            )

            skeptic_flags = await run_skeptic_pass(report, citations, llm)
            report.skeptic_flags = skeptic_flags

            # Stage 9: ASSEMBLY
            await self._update_progress(
                job_id, "assembly",
                citations_found=len(citations),
                current_action="Assembling final report",
            )
            await self._db.store_report(job_id, report.model_dump_json())
            await self._db.update_job_status(job_id, JobStatus.COMPLETE.value)
            await self._update_progress(
                job_id, "complete", citations_found=len(citations)
            )

        except Exception:
            logger.exception(f"Pipeline failed for job {job_id}")
            await self._db.update_job_status(job_id, JobStatus.FAILED.value)
            await self._update_progress(
                job_id, "failed",
                current_action=f"Pipeline error: {traceback.format_exc()[:200]}",
            )

    async def _run_pipeline_after_clarification(
        self, job_id: str, answers: list[ClarificationAnswer]
    ) -> None:
        """Resume pipeline with clarification answers."""
        job = await self._db.get_job(job_id)
        if not job:
            return

        options = json.loads(job["options_json"]) if job["options_json"] else {}
        # Merge clarification answers into options
        for a in answers:
            options[f"clarification_{a.question}"] = a.answer

        await self._run_pipeline(job_id, job["idea_text"], options)
