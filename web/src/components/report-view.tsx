"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import {
  Download,
  Zap,
  AlertTriangle,
  MessageSquare,
  Globe,
  Star,
  Briefcase,
  ExternalLink,
  Check,
  X as XIcon,
  Copy,
  Swords,
} from "lucide-react";
import { getExportUrl } from "@/lib/api-client";
import type {
  Citation,
  Competitor,
  EvidencedClaim,
  PainCluster,
  ResearchReport,
  ScoredDimension,
  SourceType,
} from "@/lib/types";
import { GlassCard } from "@/components/ui/glass-card";
import { AnimatedCollapsible } from "@/components/ui/animated-collapsible";
import { VerdictBadge } from "@/components/ui/verdict-badge";
import { CitationChip } from "@/components/ui/citation-chip";
import { StrengthBadge } from "@/components/ui/strength-badge";
import { ScoreGauge } from "@/components/ui/score-gauge";
import { RadarChart } from "@/components/ui/radar-chart";

interface Props {
  report: ResearchReport;
}

const stagger = {
  hidden: {},
  visible: { transition: { staggerChildren: 0.08 } },
};

const fadeUp = {
  hidden: { opacity: 0, y: 24 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.4, ease: "easeOut" as const } },
};

// ─── Source type icon mapping ────────────────────────
const SOURCE_ICONS: Record<SourceType, typeof Globe> = {
  reddit: MessageSquare,
  review: Star,
  web: Globe,
  job_post: Briefcase,
  competitor: Swords,
};

// ─── Main component ─────────────────────────────────
export function ReportView({ report }: Props) {
  return (
    <motion.div
      className="w-full max-w-4xl space-y-5"
      variants={stagger}
      initial="hidden"
      animate="visible"
    >
      {/* Header */}
      <motion.div variants={fadeUp} className="flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-bold text-zinc-100">
            Research Report
          </h1>
          <p className="text-sm text-zinc-500 mt-1">
            {report.idea_brief.one_liner}
          </p>
        </div>
        <div className="flex gap-2 shrink-0">
          <a
            href={getExportUrl(report.id, "json")}
            className="glass-card glass-card-hover inline-flex items-center gap-1.5 rounded-full px-3 py-1.5 text-xs text-zinc-400 hover:text-zinc-200"
          >
            <Download size={12} /> JSON
          </a>
          <a
            href={getExportUrl(report.id, "csv")}
            className="glass-card glass-card-hover inline-flex items-center gap-1.5 rounded-full px-3 py-1.5 text-xs text-zinc-400 hover:text-zinc-200"
          >
            <Download size={12} /> CSV
          </a>
        </div>
      </motion.div>

      {/* ─── Verdict Hero ─────────────────────────────── */}
      <motion.div variants={fadeUp}>
        <GlassCard>
          <div className="text-center mb-6">
            <VerdictBadge decision={report.verdict.decision} />
          </div>

          <div className="grid md:grid-cols-2 gap-6">
            <div>
              <h3 className="text-sm font-medium text-zinc-400 mb-2">
                Top Reasons
              </h3>
              <ClaimList
                claims={report.verdict.reasons}
                citations={report.evidence_pack}
              />
            </div>
            <div>
              <h3 className="text-sm font-medium text-zinc-400 mb-2">
                Top Risks
              </h3>
              <ClaimList
                claims={report.verdict.risks}
                citations={report.evidence_pack}
              />
            </div>
          </div>

          {/* Narrowest wedge */}
          <div className="mt-5 flex items-start gap-2.5 rounded-xl bg-indigo-400/5 border border-indigo-400/15 px-4 py-3">
            <Zap size={16} className="text-indigo-400 mt-0.5 shrink-0" />
            <div>
              <p className="text-xs font-medium text-indigo-400 mb-0.5">
                Narrowest Wedge
              </p>
              <p className="text-sm text-zinc-300">
                {report.verdict.narrowest_wedge}
              </p>
            </div>
          </div>

          {/* What would change */}
          <div className="mt-3">
            <h4 className="text-xs font-medium text-zinc-500 mb-1">
              What Would Change This Verdict
            </h4>
            <p className="text-sm text-zinc-400">
              {report.verdict.what_would_change}
            </p>
          </div>

          {/* Evidence quality notes */}
          {report.verdict.evidence_quality_notes?.length > 0 && (
            <div className="mt-4 neu-inset px-4 py-3">
              <h4 className="text-[10px] uppercase tracking-widest text-zinc-600 mb-1.5">
                Evidence Quality
              </h4>
              <ul className="space-y-0.5">
                {report.verdict.evidence_quality_notes.map((note, i) => (
                  <li key={i} className="text-xs text-zinc-500">
                    {note}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Conflicts */}
          {report.conflicts.length > 0 && (
            <div className="mt-5 pt-4 border-t border-zinc-800/60">
              <h4 className="text-sm font-medium text-amber-400 mb-3">
                Conflicts ({report.conflicts.length})
              </h4>
              {report.conflicts
                .filter((c) => c.relevance === "strong")
                .map((c, i) => (
                  <div
                    key={`strong-${i}`}
                    className="mb-2 rounded-xl bg-amber-500/5 border border-amber-500/15 p-3"
                  >
                    <p className="text-sm text-zinc-300 mb-2">
                      {c.description}
                    </p>
                    <div className="grid grid-cols-2 gap-3 text-xs">
                      <div className="rounded-lg bg-zinc-900/50 p-2">
                        <span className="text-zinc-500 font-medium">
                          Side A:
                        </span>{" "}
                        <span className="text-zinc-400">{c.side_a.text}</span>
                      </div>
                      <div className="rounded-lg bg-zinc-900/50 p-2">
                        <span className="text-zinc-500 font-medium">
                          Side B:
                        </span>{" "}
                        <span className="text-zinc-400">{c.side_b.text}</span>
                      </div>
                    </div>
                  </div>
                ))}
              {report.conflicts.filter((c) => c.relevance !== "strong").length >
                0 && (
                <AnimatedCollapsible
                  title={
                    <span className="text-xs text-zinc-600">
                      {
                        report.conflicts.filter(
                          (c) => c.relevance !== "strong"
                        ).length
                      }{" "}
                      weak conflict(s)
                    </span>
                  }
                  className="mt-1"
                >
                  {report.conflicts
                    .filter((c) => c.relevance !== "strong")
                    .map((c, i) => (
                      <div
                        key={`weak-${i}`}
                        className="mb-2 rounded-lg bg-zinc-900/30 border border-zinc-800/50 p-3 text-xs"
                      >
                        <p className="text-zinc-500 mb-1">{c.description}</p>
                        <p className="text-zinc-600">A: {c.side_a.text}</p>
                        <p className="text-zinc-600">B: {c.side_b.text}</p>
                      </div>
                    ))}
                </AnimatedCollapsible>
              )}
            </div>
          )}

          {/* Skeptic flags */}
          {report.skeptic_flags.length > 0 && (
            <div className="mt-4 pt-4 border-t border-zinc-800/60">
              <h4 className="text-sm font-medium text-orange-400 mb-2">
                Skeptic Flags ({report.skeptic_flags.length})
              </h4>
              <ul className="space-y-1.5">
                {report.skeptic_flags.map((flag, i) => (
                  <li
                    key={i}
                    className="flex items-start gap-2 text-sm text-zinc-400"
                  >
                    <AlertTriangle
                      size={14}
                      className="text-orange-400 mt-0.5 shrink-0"
                    />
                    {flag}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </GlassCard>
      </motion.div>

      {/* ─── Pain Map ─────────────────────────────────── */}
      <motion.div variants={fadeUp}>
        <GlassCard padding={false}>
          <AnimatedCollapsible
            title={`Pain Map (${report.pain_map.length} clusters)`}
            defaultOpen
          >
            <div className="space-y-3">
              {[...report.pain_map]
                .sort((a, b) => {
                  const s = (c: PainCluster) =>
                    c.scores.frequency.score +
                    c.scores.severity.score +
                    c.scores.payability.score;
                  return s(b) - s(a);
                })
                .map((cluster, i) => (
                  <ClusterCard
                    key={cluster.id}
                    cluster={cluster}
                    citations={report.evidence_pack}
                    rank={i + 1}
                  />
                ))}
            </div>
          </AnimatedCollapsible>
        </GlassCard>
      </motion.div>

      {/* ─── Competitors ──────────────────────────────── */}
      <motion.div variants={fadeUp}>
        <GlassCard padding={false}>
          <AnimatedCollapsible
            title={`Competitors (${report.competitors.length})`}
          >
            {report.competitors.length === 0 ? (
              <p className="text-sm text-zinc-500">
                No competitors identified in evidence.
              </p>
            ) : (
              <div className="grid gap-3 sm:grid-cols-2">
                {report.competitors.map((comp) => (
                  <CompetitorCard
                    key={comp.name}
                    competitor={comp}
                    citations={report.evidence_pack}
                  />
                ))}
              </div>
            )}
          </AnimatedCollapsible>
        </GlassCard>
      </motion.div>

      {/* ─── Payability ───────────────────────────────── */}
      <motion.div variants={fadeUp}>
        <GlassCard padding={false}>
          <AnimatedCollapsible title="Payability Signals">
            <div className="mb-3">
              <StrengthBadge strength={report.payability.overall_strength} />
              <p className="mt-2 text-sm text-zinc-400">
                {report.payability.summary}
              </p>
            </div>
            {report.payability.hiring_signals.length > 0 && (
              <div className="mb-3">
                <h4 className="text-xs font-medium text-zinc-500 mb-1.5">
                  Hiring Signals
                </h4>
                <ClaimList
                  claims={report.payability.hiring_signals}
                  citations={report.evidence_pack}
                />
              </div>
            )}
            {report.payability.outsourcing_signals.length > 0 && (
              <div className="mb-3">
                <h4 className="text-xs font-medium text-zinc-500 mb-1.5">
                  Outsourcing Signals
                </h4>
                <ClaimList
                  claims={report.payability.outsourcing_signals}
                  citations={report.evidence_pack}
                />
              </div>
            )}
            {report.payability.template_sop_signals.length > 0 && (
              <div>
                <h4 className="text-xs font-medium text-zinc-500 mb-1.5">
                  Template / SOP Signals
                </h4>
                <ClaimList
                  claims={report.payability.template_sop_signals}
                  citations={report.evidence_pack}
                />
              </div>
            )}
          </AnimatedCollapsible>
        </GlassCard>
      </motion.div>

      {/* ─── 7-Day Validation Plan ────────────────────── */}
      <motion.div variants={fadeUp}>
        <GlassCard padding={false}>
          <AnimatedCollapsible title="7-Day Validation Plan" defaultOpen>
            <ValidationPlanView plan={report.validation_plan} />
          </AnimatedCollapsible>
        </GlassCard>
      </motion.div>

      {/* ─── Evidence Appendix ────────────────────────── */}
      <motion.div variants={fadeUp}>
        <GlassCard padding={false}>
          <AnimatedCollapsible
            title={`Evidence Appendix (${report.evidence_pack.length} citations)`}
          >
            <EvidenceList
              citations={report.evidence_pack}
              jobId={report.id}
            />
          </AnimatedCollapsible>
        </GlassCard>
      </motion.div>
    </motion.div>
  );
}

// ─── Sub-components ──────────────────────────────────

function ClaimList({
  claims,
  citations,
}: {
  claims: EvidencedClaim[];
  citations: Citation[];
}) {
  return (
    <ul className="space-y-2">
      {claims.map((claim, i) => (
        <li key={i} className="text-sm text-zinc-300 leading-relaxed">
          {claim.text}
          <span className="ml-1.5 inline-flex gap-1">
            {claim.citation_indices.map((idx) => (
              <CitationChip
                key={idx}
                index={idx}
                url={citations[idx]?.url || "#"}
                excerpt={citations[idx]?.excerpt}
              />
            ))}
          </span>
        </li>
      ))}
    </ul>
  );
}

function ClusterCard({
  cluster,
  citations,
  rank,
}: {
  cluster: PainCluster;
  citations: Citation[];
  rank: number;
}) {
  const [expanded, setExpanded] = useState(rank <= 3);

  const dims: { key: string; label: string; dim: ScoredDimension }[] = [
    { key: "freq", label: "Frequency", dim: cluster.scores.frequency },
    { key: "sev", label: "Severity", dim: cluster.scores.severity },
    { key: "urg", label: "Urgency", dim: cluster.scores.urgency },
    { key: "pay", label: "Payability", dim: cluster.scores.payability },
    { key: "wac", label: "Workaround", dim: cluster.scores.workaround_cost },
    { key: "sat", label: "Saturation", dim: cluster.scores.saturation },
    { key: "acc", label: "Access", dim: cluster.scores.accessibility },
  ];

  const radarData = dims.map((d) => ({
    dimension: d.label,
    score: d.dim.score,
  }));

  // Confidence bar width
  const confPct = Math.round(cluster.confidence * 100);

  return (
    <div className="neu-card overflow-hidden">
      {/* Header — always visible */}
      <button
        type="button"
        onClick={() => setExpanded(!expanded)}
        className="w-full text-left px-4 py-3 flex items-start gap-3"
      >
        <span className="text-xs font-mono text-zinc-600 mt-0.5">
          #{rank}
        </span>
        <div className="flex-1 min-w-0">
          <p className="text-sm text-zinc-200 leading-snug">
            {cluster.statement.text}
          </p>
          <div className="flex items-center gap-3 mt-1.5">
            <span className="text-xs text-zinc-500">{cluster.who}</span>
            {/* Confidence bar */}
            <div className="flex items-center gap-1.5 flex-1 max-w-[120px]">
              <div className="flex-1 h-1 rounded-full bg-zinc-800 overflow-hidden">
                <div
                  className="h-full rounded-full bg-indigo-400/60"
                  style={{ width: `${confPct}%` }}
                />
              </div>
              <span className="text-[10px] font-mono text-zinc-600">
                {confPct}%
              </span>
            </div>
          </div>
        </div>
      </button>

      {/* Expanded content */}
      {expanded && (
        <div className="px-4 pb-4 space-y-4 border-t border-zinc-800/40">
          {/* Radar chart + score gauges */}
          <div className="pt-4 flex flex-col sm:flex-row items-center gap-4">
            <div className="w-full sm:w-1/2">
              <RadarChart data={radarData} />
            </div>
            <div className="grid grid-cols-4 gap-3 w-full sm:w-1/2">
              {dims.map((d) => (
                <ScoreGauge
                  key={d.key}
                  score={d.dim.score}
                  label={d.label}
                />
              ))}
              <ScoreGauge
                score={Math.round(cluster.recency_weight * 5)}
                label="Recency"
              />
            </div>
          </div>

          {/* Meta */}
          <div className="flex flex-wrap gap-2 text-xs">
            <span className="rounded-full bg-zinc-800 px-2.5 py-1 text-zinc-400">
              Trigger: {cluster.trigger}
            </span>
            {cluster.workarounds.map((w, i) => (
              <span
                key={i}
                className="rounded-full bg-zinc-800 px-2.5 py-1 text-zinc-500"
              >
                {w}
              </span>
            ))}
          </div>

          {/* Citation excerpts */}
          <div className="flex flex-wrap gap-1">
            {cluster.citation_indices.slice(0, 5).map((idx) => (
              <CitationChip
                key={idx}
                index={idx}
                url={citations[idx]?.url || "#"}
                excerpt={citations[idx]?.excerpt}
              />
            ))}
            {cluster.citation_indices.length > 5 && (
              <span className="text-[10px] text-zinc-600 self-center">
                +{cluster.citation_indices.length - 5} more
              </span>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

function CompetitorCard({
  competitor,
  citations,
}: {
  competitor: Competitor;
  citations: Citation[];
}) {
  const [expanded, setExpanded] = useState(false);

  return (
    <div className="neu-card p-4">
      <div className="flex items-start justify-between mb-2">
        <a
          href={competitor.url}
          target="_blank"
          rel="noopener noreferrer"
          className="text-sm font-medium text-zinc-200 hover:text-indigo-400 inline-flex items-center gap-1 transition-colors"
        >
          {competitor.name}
          <ExternalLink size={12} />
        </a>
        <span
          className={`inline-flex items-center gap-1 text-[10px] font-medium ${competitor.pricing_page_exists ? "text-green-400" : "text-zinc-600"}`}
        >
          {competitor.pricing_page_exists ? (
            <>
              <Check size={10} /> Pricing
            </>
          ) : (
            <>
              <XIcon size={10} /> No pricing
            </>
          )}
        </span>
      </div>
      <p className="text-xs text-zinc-500 mb-2 line-clamp-2">
        {competitor.positioning}
      </p>
      <div className="flex items-center gap-2 text-xs">
        {competitor.min_price_observed && (
          <span className="rounded-full bg-zinc-800 px-2 py-0.5 text-zinc-400">
            {competitor.min_price_observed}
          </span>
        )}
        <span className="rounded-full bg-zinc-800 px-2 py-0.5 text-zinc-500 capitalize">
          {competitor.onboarding_model.replace("_", " ")}
        </span>
      </div>

      {(competitor.strengths.length > 0 ||
        competitor.weaknesses.length > 0) && (
        <button
          type="button"
          onClick={() => setExpanded(!expanded)}
          className="text-[10px] text-zinc-600 hover:text-zinc-400 mt-2 transition-colors"
        >
          {expanded ? "Hide details" : "Show strengths & weaknesses"}
        </button>
      )}

      {expanded && (
        <div className="mt-2 space-y-2 text-xs">
          {competitor.strengths.length > 0 && (
            <div>
              <span className="text-green-400/80 font-medium">Strengths:</span>
              <ClaimList claims={competitor.strengths} citations={citations} />
            </div>
          )}
          {competitor.weaknesses.length > 0 && (
            <div>
              <span className="text-red-400/80 font-medium">Weaknesses:</span>
              <ClaimList claims={competitor.weaknesses} citations={citations} />
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function ValidationPlanView({
  plan,
}: {
  plan: ResearchReport["validation_plan"];
}) {
  const [copied, setCopied] = useState(false);

  function copyScript() {
    navigator.clipboard.writeText(plan.interview_script);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  }

  const sections = [
    { label: "Objective", content: plan.objective },
    plan.channels.length > 0
      ? { label: "Channels", list: plan.channels }
      : null,
    plan.outreach_targets.length > 0
      ? { label: "Outreach Targets", list: plan.outreach_targets }
      : null,
    plan.interview_script
      ? { label: "Interview Script", script: plan.interview_script }
      : null,
    plan.landing_page_hypotheses.length > 0
      ? {
          label: "Landing Page Hypotheses",
          list: plan.landing_page_hypotheses,
        }
      : null,
    plan.concierge_procedure
      ? { label: "Concierge MVP", content: plan.concierge_procedure }
      : null,
  ].filter(Boolean) as Array<{
    label: string;
    content?: string;
    list?: string[];
    script?: string;
  }>;

  return (
    <div className="space-y-0">
      {sections.map((sec, i) => (
        <div key={sec.label} className="flex gap-4">
          {/* Step number */}
          <div className="flex flex-col items-center">
            <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-indigo-400/10 text-xs font-bold text-indigo-400">
              {i + 1}
            </div>
            {i < sections.length - 1 && (
              <div className="w-px flex-1 bg-zinc-800/60" />
            )}
          </div>

          {/* Content */}
          <div className="pb-5 flex-1 min-w-0">
            <h4 className="text-sm font-medium text-zinc-400 mb-1">
              {sec.label}
            </h4>
            {sec.content && (
              <p className="text-sm text-zinc-300">{sec.content}</p>
            )}
            {sec.list && (
              <ul className="list-disc list-inside text-sm text-zinc-300 space-y-0.5">
                {sec.list.map((item, j) => (
                  <li key={j}>{item}</li>
                ))}
              </ul>
            )}
            {sec.script && (
              <div className="relative">
                <pre className="text-sm text-zinc-300 whitespace-pre-wrap bg-zinc-900/60 rounded-xl p-4 border border-zinc-800/60 mt-1 max-h-64 overflow-y-auto">
                  {sec.script}
                </pre>
                <button
                  type="button"
                  onClick={copyScript}
                  className="absolute top-3 right-3 rounded-lg bg-zinc-800 p-1.5 text-zinc-500 hover:text-zinc-300 transition-colors"
                >
                  {copied ? <Check size={14} /> : <Copy size={14} />}
                </button>
              </div>
            )}
          </div>
        </div>
      ))}

      {/* Success threshold */}
      <div className="rounded-xl bg-green-500/5 border border-green-500/15 px-4 py-3 mt-2">
        <h4 className="text-xs font-medium text-green-400 mb-0.5">
          Success Threshold
        </h4>
        <p className="text-sm text-zinc-200 font-medium">
          {plan.success_threshold}
        </p>
      </div>

      {/* Reversal criteria */}
      {plan.reversal_criteria && (
        <div className="rounded-xl bg-red-500/5 border border-red-500/15 px-4 py-3 mt-2">
          <h4 className="text-xs font-medium text-red-400 mb-0.5">
            Reversal Criteria
          </h4>
          <p className="text-sm text-zinc-300">{plan.reversal_criteria}</p>
        </div>
      )}
    </div>
  );
}

function EvidenceList({
  citations,
  jobId,
}: {
  citations: Citation[];
  jobId: string;
}) {
  const [search, setSearch] = useState("");
  const [filterType, setFilterType] = useState<string>("all");

  const filtered = citations.filter((c, _idx) => {
    const matchesSearch =
      !search ||
      c.excerpt.toLowerCase().includes(search.toLowerCase()) ||
      c.url.toLowerCase().includes(search.toLowerCase());
    const matchesType =
      filterType === "all" || c.source_type === filterType;
    return matchesSearch && matchesType;
  });

  const sourceTypes: { key: string; label: string }[] = [
    { key: "all", label: "All" },
    { key: "reddit", label: "Reddit" },
    { key: "web", label: "Web" },
    { key: "review", label: "Reviews" },
    { key: "job_post", label: "Jobs" },
    { key: "competitor", label: "Competitors" },
  ];

  return (
    <div className="space-y-3">
      {/* Search + export */}
      <div className="flex gap-2">
        <input
          type="text"
          placeholder="Search citations..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="flex-1 rounded-xl border border-zinc-700/60 bg-zinc-900/60 px-3 py-2 text-sm text-zinc-100 placeholder-zinc-600 focus:border-indigo-400/60 focus:outline-none focus:ring-1 focus:ring-indigo-400/30"
        />
        <a
          href={getExportUrl(jobId, "json")}
          className="glass-card glass-card-hover rounded-xl px-3 py-2 text-xs text-zinc-400 hover:text-zinc-200"
        >
          JSON
        </a>
        <a
          href={getExportUrl(jobId, "csv")}
          className="glass-card glass-card-hover rounded-xl px-3 py-2 text-xs text-zinc-400 hover:text-zinc-200"
        >
          CSV
        </a>
      </div>

      {/* Filter pills */}
      <div className="flex flex-wrap gap-1.5">
        {sourceTypes.map((st) => (
          <button
            key={st.key}
            type="button"
            onClick={() => setFilterType(st.key)}
            className={`rounded-full px-3 py-1 text-xs transition-colors ${
              filterType === st.key
                ? "bg-indigo-400/15 text-indigo-400 border border-indigo-400/30"
                : "bg-zinc-800/60 text-zinc-500 border border-zinc-700/40 hover:text-zinc-300"
            }`}
          >
            {st.label}
          </button>
        ))}
      </div>

      {/* Citation cards */}
      <div className="max-h-96 overflow-y-auto space-y-2 pr-1">
        {filtered.map((c) => {
          const globalIdx = citations.indexOf(c);
          const Icon = SOURCE_ICONS[c.source_type] || Globe;

          return (
            <div
              key={globalIdx}
              className="rounded-xl border border-zinc-800/50 bg-zinc-900/30 p-3 text-xs"
            >
              <div className="flex items-start justify-between mb-1.5">
                <span className="font-mono text-indigo-400/80">
                  [{globalIdx}]
                </span>
                <span className="inline-flex items-center gap-1 text-zinc-600 capitalize">
                  <Icon size={11} />
                  {c.source_type.replace("_", " ")}
                </span>
              </div>
              <p className="text-zinc-400 mb-1.5 leading-relaxed">
                {c.excerpt}
              </p>
              <div className="flex items-center justify-between">
                <a
                  href={c.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-zinc-500 hover:text-indigo-400 underline truncate max-w-[300px] transition-colors"
                >
                  {c.url}
                </a>
                {c.date_published && (
                  <span className="text-zinc-600 shrink-0 ml-2">
                    {c.date_published}
                  </span>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
