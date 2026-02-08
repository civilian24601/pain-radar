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
                progress_callback=None,
            )

            if not citations:
                await self._db.update_job_status(job_id, JobStatus.FAILED.value)
                await self._update_progress(
                    job_id, "failed",
                    current_action="No evidence found. Try a different idea or broader keywords.",
                )
                return

            # Stage 3a: URL DEDUP — collapse same-URL citations
            from pain_radar.pipeline.relevance import deduplicate_citations
            citations = deduplicate_citations(citations)

            # Stage 3b: TOPIC RELEVANCE CHECK
            await self._update_progress(
                job_id, "topic_relevance_check",
                citations_found=len(citations),
                current_action="Checking evidence relevance",
            )
            from pain_radar.pipeline.relevance import compute_topic_relevance
            keywords = queries.get("_keywords") or []
            snapshot_rows = await self._db.get_snapshots_for_job(job_id)
            relevance_result = compute_topic_relevance(citations, snapshot_rows, keywords)
            relevance_ratio = relevance_result.ratio
            logger.info(f"Topic relevance ratio: {relevance_ratio:.2f} ({len(citations)} citations)")

            relevance_threshold = 0.60
            if relevance_ratio < relevance_threshold:
                logger.warning(
                    f"Off-topic evidence: {relevance_ratio:.0%} relevant "
                    f"(threshold {relevance_threshold:.0%}). Short-circuiting to "
                    f"INSUFFICIENT_EVIDENCE."
                )
                from pain_radar.core.models import (
                    EvidencedClaim,
                    EvidenceQualityMetrics,
                    IdeaBrief,
                    PayabilityAssessment,
                    ResearchReport,
                    ValidationPlan,
                    Verdict,
                    VerdictDecision,
                )

                # Use the first on-topic citation as an honest anchor
                anchor_indices = relevance_result.on_topic_indices[:1] or [0]

                ie_verdict = Verdict(
                    decision=VerdictDecision.INSUFFICIENT_EVIDENCE,
                    reasons=[EvidencedClaim(
                        text="Collected evidence is dominated by off-topic results unrelated to the target problem domain",
                        citation_indices=anchor_indices,
                    )],
                    risks=[EvidencedClaim(
                        text="Any analysis would be driven by signals unrelated to the target workflow",
                        citation_indices=anchor_indices,
                    )],
                    evidence_quality_notes=[
                        f"Topic relevance: {relevance_ratio:.0%} on-topic (threshold: {relevance_threshold:.0%})",
                        f"On-topic: {len(relevance_result.on_topic_indices)}, off-topic: {len(relevance_result.off_topic_indices)}",
                    ],
                    narrowest_wedge="Re-run with more specific keywords or niche constraints",
                    what_would_change=(
                        f"Collecting evidence where >{relevance_threshold:.0%} of citations "
                        f"are topically relevant to the core idea"
                    ),
                )

                eq_metrics = EvidenceQualityMetrics(
                    total_citations=len(citations),
                    topic_relevance_ratio=relevance_ratio,
                    gate_triggered="relevance",
                )

                ie_plan = ValidationPlan(
                    verdict_context=VerdictDecision.INSUFFICIENT_EVIDENCE,
                    objective="Collect topic-specific evidence to re-evaluate this idea",
                    channels=["Niche subreddits", "Industry-specific forums", "Targeted web search"],
                    outreach_targets=[
                        "Identify 10 communities where the target users discuss this specific problem",
                        "Search for exact tool names, workflow descriptions, and role titles",
                    ],
                    interview_script=(
                        "What specific tools/processes do you use for [exact workflow]? "
                        "What's the most frustrating part?"
                    ),
                    landing_page_hypotheses=[],
                    concierge_procedure="",
                    success_threshold=(
                        f"Re-run produces >{relevance_threshold:.0%} topically relevant citations"
                    ),
                    reversal_criteria=(
                        f"Evidence collection with >{relevance_threshold:.0%} relevance ratio "
                        "showing real pain signals in the target domain"
                    ),
                )

                idea_brief = IdeaBrief(
                    raw_idea=idea,
                    one_liner=idea[:200],
                    buyer_persona=options.get("buyer_role") or "Unknown",
                    workflow_replaced="Unknown",
                    moment_of_pain="Unknown",
                    keywords=keywords or ["unknown"],
                )

                report = ResearchReport(
                    id=job_id,
                    idea_brief=idea_brief,
                    pain_map=[],
                    payability=PayabilityAssessment(
                        hiring_signals=[],
                        outsourcing_signals=[],
                        template_sop_signals=[],
                        overall_strength="none",
                        summary="Analysis skipped due to off-topic evidence mix.",
                    ),
                    competitors=[],
                    verdict=ie_verdict,
                    validation_plan=ie_plan,
                    evidence_pack=citations,
                    skeptic_flags=[
                        f"Topic relevance: {relevance_ratio:.0%} "
                        f"(below {relevance_threshold:.0%} threshold)"
                    ],
                    conflicts=[],
                    evidence_quality=eq_metrics,
                )

                await self._db.store_report(job_id, report.model_dump_json())
                await self._db.update_job_status(job_id, JobStatus.COMPLETE.value)
                await self._update_progress(
                    job_id, "complete", citations_found=len(citations)
                )
                return

            # Reorder citations: on-topic first, off-topic at the end.
            # Analysis stages only see on-topic citations; the full list
            # (on-topic + off-topic) goes into evidence_pack for transparency.
            on_topic_citations = [citations[i] for i in relevance_result.on_topic_indices]
            off_topic_citations = [citations[i] for i in relevance_result.off_topic_indices]
            citations = on_topic_citations + off_topic_citations
            on_topic_count = len(on_topic_citations)

            # Guard: if too few on-topic, use all citations for analysis
            if on_topic_count < 3:
                logger.warning(
                    f"Only {on_topic_count} on-topic citations; using all for analysis"
                )
                analysis_citations = citations
            else:
                analysis_citations = citations[:on_topic_count]

            logger.info(
                f"Using {len(analysis_citations)}/{len(citations)} on-topic citations "
                f"for analysis"
            )

            # Stage 4: ANALYSIS
            await self._db.update_job_status(job_id, JobStatus.ANALYZING.value)
            await self._update_progress(
                job_id, "analysis",
                citations_found=len(citations),
                current_action="Clustering pain points",
            )

            from pain_radar.analysis.clustering import cluster_evidence
            clusters = await cluster_evidence(analysis_citations, idea, options, llm)

            await self._update_progress(
                job_id, "analysis",
                citations_found=len(citations),
                current_action="Scoring clusters",
            )
            from pain_radar.analysis.scoring import score_clusters
            scored_clusters = await score_clusters(clusters, analysis_citations, llm)

            # Post-scoring evidence quality check
            await self._update_progress(
                job_id, "analysis",
                citations_found=len(citations),
                current_action="Checking evidence quality",
            )
            if scored_clusters:
                from urllib.parse import urlparse
                confidences = [c.confidence for c in scored_clusters]
                median_confidence = sorted(confidences)[len(confidences) // 2]
                high_conf_count = sum(1 for c in confidences if c >= 0.45)

                # Gather citation-level metrics
                all_cluster_indices: set[int] = set()
                for cl in scored_clusters:
                    all_cluster_indices.update(cl.citation_indices)
                cluster_citations = [
                    analysis_citations[i]
                    for i in all_cluster_indices
                    if 0 <= i < len(analysis_citations)
                ]
                unique_domains = len({urlparse(c.url).netloc for c in cluster_citations})
                unique_source_types = len({c.source_type for c in cluster_citations})

                if median_confidence < 0.35 or high_conf_count < 2:
                    logger.warning(
                        f"Insufficient evidence quality: "
                        f"median_confidence={median_confidence:.2f}, "
                        f"high_confidence_clusters(>=0.45)={high_conf_count}"
                    )
                    from pain_radar.core.models import (
                        EvidencedClaim,
                        EvidenceQualityMetrics,
                        IdeaBrief,
                        PayabilityAssessment,
                        ResearchReport,
                        ValidationPlan,
                        Verdict,
                        VerdictDecision,
                    )

                    best = max(scored_clusters, key=lambda c: c.confidence)
                    anchor_indices = best.citation_indices[:1] or [0]

                    ie_verdict = Verdict(
                        decision=VerdictDecision.INSUFFICIENT_EVIDENCE,
                        reasons=[EvidencedClaim(
                            text="Evidence does not demonstrate the target workflow pain from multiple independent sources",
                            citation_indices=anchor_indices,
                        )],
                        risks=[EvidencedClaim(
                            text="Clusters may reflect adjacent or tangential signals rather than direct user pain",
                            citation_indices=anchor_indices,
                        )],
                        evidence_quality_notes=[
                            f"Median cluster confidence: {median_confidence:.2f} (threshold: 0.35)",
                            f"High-confidence clusters (>= 0.45): {high_conf_count} (minimum: 2)",
                            f"Unique domains: {unique_domains}, source types: {unique_source_types}",
                            "Confidence = f(citation count, domain diversity, source type diversity, recency)",
                        ],
                        narrowest_wedge="Collect more targeted evidence in the specific problem domain",
                        what_would_change=(
                            "Evidence with median cluster confidence >= 0.35 and at "
                            "least 2 clusters with confidence >= 0.45"
                        ),
                    )

                    eq_metrics = EvidenceQualityMetrics(
                        cluster_confidences=confidences,
                        median_confidence=median_confidence,
                        high_confidence_count=high_conf_count,
                        total_clusters=len(scored_clusters),
                        total_citations=len(analysis_citations),
                        unique_domains=unique_domains,
                        unique_source_types=unique_source_types,
                        topic_relevance_ratio=relevance_ratio,
                        gate_triggered="confidence",
                    )

                    ie_plan = ValidationPlan(
                        verdict_context=VerdictDecision.INSUFFICIENT_EVIDENCE,
                        objective="Collect targeted evidence to determine if real pain exists",
                        channels=["Niche subreddits", "Industry forums", "Targeted outreach"],
                        outreach_targets=[
                            "Identify communities where target users discuss this exact problem",
                        ],
                        interview_script=(
                            "What specific tools/processes do you use for [workflow]? "
                            "What's most frustrating?"
                        ),
                        success_threshold=(
                            "Collect evidence achieving median cluster confidence >= 0.35"
                        ),
                        reversal_criteria=(
                            "Targeted evidence from 3+ independent sources showing "
                            "clear pain signals"
                        ),
                    )

                    idea_brief = IdeaBrief(
                        raw_idea=idea,
                        one_liner=idea[:200],
                        buyer_persona=options.get("buyer_role") or "Unknown",
                        workflow_replaced="Unknown",
                        moment_of_pain="Unknown",
                        keywords=keywords or ["unknown"],
                    )

                    report = ResearchReport(
                        id=job_id,
                        idea_brief=idea_brief,
                        pain_map=scored_clusters,
                        payability=PayabilityAssessment(
                            hiring_signals=[],
                            outsourcing_signals=[],
                            template_sop_signals=[],
                            overall_strength="none",
                            summary="Evidence insufficient for payability assessment.",
                        ),
                        competitors=[],
                        verdict=ie_verdict,
                        validation_plan=ie_plan,
                        evidence_pack=citations,
                        skeptic_flags=[],
                        conflicts=[],
                        evidence_quality=eq_metrics,
                    )

                    await self._db.store_report(job_id, report.model_dump_json())
                    await self._db.update_job_status(job_id, JobStatus.COMPLETE.value)
                    await self._update_progress(
                        job_id, "complete", citations_found=len(citations)
                    )
                    return

            await self._update_progress(
                job_id, "analysis",
                citations_found=len(citations),
                current_action="Analyzing competitors",
            )
            from pain_radar.analysis.clustering import extract_competitors
            competitors = await extract_competitors(analysis_citations, idea, options, llm)

            from pain_radar.analysis.scoring import assess_payability
            payability = await assess_payability(analysis_citations, idea, llm)

            # Stage 5: CONFLICT DETECTION
            await self._update_progress(
                job_id, "conflict_detection",
                citations_found=len(citations),
                current_action="Detecting conflicts",
            )
            from pain_radar.analysis.conflict import detect_conflicts
            conflicts = await detect_conflicts(
                scored_clusters, competitors, analysis_citations, llm
            )

            # Stage 6: VERDICT
            await self._update_progress(
                job_id, "verdict",
                citations_found=len(citations),
                current_action="Generating verdict",
            )
            from pain_radar.analysis.verdict import generate_verdict
            verdict = await generate_verdict(
                scored_clusters, competitors, payability, conflicts,
                analysis_citations, llm,
            )

            # Enforce verdict ↔ payability consistency
            from pain_radar.analysis.verdict import enforce_verdict_payability_consistency
            payability = enforce_verdict_payability_consistency(verdict, payability)

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
                buyer_persona=options.get("buyer_role") or "Unknown",
                workflow_replaced="Unknown",
                moment_of_pain="Unknown",
                keywords=queries.get("_keywords") or ["unknown"],
            )

            # Assemble report for skeptic pass (full citations in evidence_pack)
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
            tb = traceback.format_exc()
            logger.error(f"Pipeline failed for job {job_id}:\n{tb}")
            await self._db.update_job_status(job_id, JobStatus.FAILED.value)
            await self._update_progress(
                job_id, "failed",
                current_action=f"Pipeline error: {tb[:1000]}",
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
