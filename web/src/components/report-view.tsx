"use client";

import { useState, useCallback } from "react";
import { motion } from "framer-motion";
import {
  Download,
  Zap,
  AlertTriangle,
  MessageSquare,
  Globe,
  Star,
  Briefcase,
  FileText,
  Layers,
  TrendingUp,
  Swords,
  Shield,
  Target,
  DollarSign,
  Clipboard,
  BookOpen,
  Check,
  Copy,
} from "lucide-react";
import { getExportUrl } from "@/lib/api-client";
import type {
  Citation,
  PainCluster,
  ResearchReport,
  SourceType,
} from "@/lib/types";
import { GlassCard } from "@/components/ui/glass-card";
import { AnimatedCollapsible } from "@/components/ui/animated-collapsible";
import { VerdictBadge } from "@/components/ui/verdict-badge";
import { StrengthBadge } from "@/components/ui/strength-badge";
import { MetricTile } from "@/components/ui/metric-tile";
import { SectionHeader } from "@/components/ui/section-header";
import { SkepticFlagCard, classifyFlagSeverity } from "@/components/ui/skeptic-flag-card";
import { ClusterPreviewCard, EmptyClusterSlot } from "@/components/ui/cluster-preview-card";
import { ClaimList } from "@/components/ui/claim-list";
import { ClusterCard } from "@/components/ui/cluster-card";
import { CompetitorCard } from "@/components/ui/competitor-card";

interface Props {
  report: ResearchReport;
}

const stagger = {
  hidden: {},
  visible: { transition: { staggerChildren: 0.06 } },
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

// ─── Helpers ─────────────────────────────────────────
function sortByScore(a: PainCluster, b: PainCluster) {
  const s = (c: PainCluster) =>
    c.scores.frequency.score + c.scores.severity.score + c.scores.payability.score;
  return s(b) - s(a);
}

function confidenceColor(median: number): "green" | "yellow" | "red" | "zinc" {
  if (median >= 0.5) return "green";
  if (median >= 0.35) return "yellow";
  if (median >= 0.2) return "red";
  return "zinc";
}

// ─── Main component ─────────────────────────────────
export function ReportView({ report }: Props) {
  const [highlightedCluster, setHighlightedCluster] = useState<string | null>(null);

  const coreClusters = report.pain_map
    .filter((c) => c.category !== "context")
    .sort(sortByScore);
  const contextClusters = report.pain_map
    .filter((c) => c.category === "context")
    .sort(sortByScore);
  const top3 = coreClusters.slice(0, 3);

  const totalCitations = report.evidence_pack.length;
  const uniqueDomains = report.evidence_quality?.unique_domains ?? 0;
  const medianConf = report.evidence_quality?.median_confidence ?? 0;
  const medianConfPct = Math.round(medianConf * 100);

  const scrollToCluster = useCallback((clusterId: string) => {
    setHighlightedCluster(clusterId);
    const el = document.getElementById(`cluster-${clusterId}`);
    if (el) {
      el.scrollIntoView({ behavior: "smooth", block: "center" });
      setTimeout(() => setHighlightedCluster(null), 1500);
    }
  }, []);

  return (
    <motion.div
      className="w-full max-w-7xl"
      variants={stagger}
      initial="hidden"
      animate="visible"
    >
      {/* ─── Dashboard Header ──────────────────────────── */}
      <motion.div variants={fadeUp} className="flex items-start justify-between mb-8">
        <div>
          <h1 className="text-3xl font-bold text-zinc-100 tracking-tight">
            {report.idea_brief.one_liner}
          </h1>
          <div className="flex items-center gap-2 mt-2 flex-wrap">
            <span className="rounded-full bg-indigo-400/10 border border-indigo-400/20 px-3 py-1 text-xs text-indigo-400">
              {report.idea_brief.buyer_persona}
            </span>
            {report.idea_brief.keywords.slice(0, 4).map((kw) => (
              <span
                key={kw}
                className="rounded-full bg-zinc-800/60 border border-zinc-700/40 px-2.5 py-0.5 text-[11px] text-zinc-500"
              >
                {kw}
              </span>
            ))}
          </div>
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

      {/* ═══════════════════════════════════════════════════
          ABOVE THE FOLD — Bento Grid
          ═══════════════════════════════════════════════════ */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-5 mb-10">
        {/* ─── Row 1: Verdict Hero (8 cols) ─────────────── */}
        <motion.div variants={fadeUp} className="lg:col-span-8">
          <GlassCard className="h-full flex flex-col justify-center" glow="accent">
            <div className="text-center mb-5">
              <VerdictBadge decision={report.verdict.decision} size="hero" />
            </div>

            {/* Narrowest wedge */}
            <div className="flex items-start gap-2.5 rounded-xl bg-indigo-400/5 border border-indigo-400/15 px-4 py-3">
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
          </GlassCard>
        </motion.div>

        {/* ─── Row 1: Metrics Stack (4 cols) ────────────── */}
        <motion.div
          variants={stagger}
          className="lg:col-span-4 grid grid-cols-2 lg:grid-cols-1 gap-4"
        >
          <MetricTile
            value={totalCitations}
            label="Citations"
            icon={FileText}
            color="accent"
          />
          <MetricTile
            value={uniqueDomains}
            label="Sources"
            icon={Globe}
            color="green"
          />
          <MetricTile
            value={coreClusters.length}
            label="Pain Clusters"
            icon={Layers}
            color="yellow"
          />
          <MetricTile
            value={`${medianConfPct}%`}
            label="Med. Confidence"
            icon={TrendingUp}
            color={confidenceColor(medianConf)}
          />
        </motion.div>

        {/* ─── Row 2: Top 3 Cluster Previews ────────────── */}
        {top3.map((cluster, i) => (
          <motion.div key={cluster.id} variants={fadeUp} className="lg:col-span-4">
            <ClusterPreviewCard
              cluster={cluster}
              rank={i + 1}
              onClick={() => scrollToCluster(cluster.id)}
            />
          </motion.div>
        ))}
        {Array.from({ length: Math.max(0, 3 - top3.length) }).map((_, i) => (
          <motion.div key={`empty-${i}`} variants={fadeUp} className="lg:col-span-4">
            <EmptyClusterSlot />
          </motion.div>
        ))}

        {/* ─── Row 3: Quick Stats ───────────────────────── */}
        <motion.div variants={fadeUp} className="lg:col-span-3">
          <GlassCard hover className="h-full flex flex-col items-center justify-center text-center py-4">
            <Swords size={18} className="text-zinc-400 opacity-60 mb-2" />
            <span className="text-2xl font-bold text-zinc-100">{report.competitors.length}</span>
            <span className="text-[11px] text-zinc-500 uppercase tracking-widest mt-1">Competitors</span>
          </GlassCard>
        </motion.div>
        <motion.div variants={fadeUp} className="lg:col-span-3">
          <GlassCard hover className="h-full flex flex-col items-center justify-center text-center py-4">
            <DollarSign size={18} className="text-zinc-400 opacity-60 mb-2" />
            <div className="mt-1">
              <StrengthBadge strength={report.payability.overall_strength} />
            </div>
            <span className="text-[11px] text-zinc-500 uppercase tracking-widest mt-2">Payability</span>
          </GlassCard>
        </motion.div>
        <motion.div variants={fadeUp} className="lg:col-span-3">
          <GlassCard hover className="h-full flex flex-col items-center justify-center text-center py-4">
            <AlertTriangle size={18} className="text-orange-400 opacity-60 mb-2" />
            <span className="text-2xl font-bold text-zinc-100">{report.skeptic_flags.length}</span>
            <span className="text-[11px] text-zinc-500 uppercase tracking-widest mt-1">Skeptic Flags</span>
          </GlassCard>
        </motion.div>
        <motion.div variants={fadeUp} className="lg:col-span-3">
          <GlassCard hover className="h-full flex flex-col items-center justify-center text-center py-4">
            <Shield size={18} className="text-zinc-400 opacity-60 mb-2" />
            <span className="text-2xl font-bold text-zinc-100">
              {report.evidence_quality?.topic_relevance_ratio != null
                ? `${Math.round(report.evidence_quality.topic_relevance_ratio * 100)}%`
                : "N/A"}
            </span>
            <span className="text-[11px] text-zinc-500 uppercase tracking-widest mt-1">Relevance</span>
          </GlassCard>
        </motion.div>
      </div>

      {/* ═══════════════════════════════════════════════════
          BELOW THE FOLD — Detail Sections
          ═══════════════════════════════════════════════════ */}
      <div className="space-y-10">
        {/* ─── 1. Verdict Details ───────────────────────── */}
        <motion.section variants={fadeUp}>
          <SectionHeader icon={Target} title="Verdict Details" color="accent" />
          <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
            <GlassCard>
              <h3 className="text-sm font-medium text-zinc-400 mb-3">Top Reasons</h3>
              <ClaimList claims={report.verdict.reasons} citations={report.evidence_pack} />
            </GlassCard>
            <GlassCard>
              <h3 className="text-sm font-medium text-zinc-400 mb-3">Top Risks</h3>
              <ClaimList claims={report.verdict.risks} citations={report.evidence_pack} />
            </GlassCard>
          </div>

          {/* Evidence quality notes */}
          {report.verdict.evidence_quality_notes?.length > 0 && (
            <div className="mt-4 neu-inset px-4 py-3 rounded-xl">
              <h4 className="text-[10px] uppercase tracking-widest text-zinc-600 mb-1.5">
                Evidence Quality
              </h4>
              <ul className="space-y-0.5">
                {report.verdict.evidence_quality_notes.map((note, i) => (
                  <li key={i} className="text-xs text-zinc-500">{note}</li>
                ))}
              </ul>
            </div>
          )}

          {/* Conflicts */}
          {report.conflicts.length > 0 && (
            <div className="mt-5">
              <h4 className="text-sm font-medium text-amber-400 mb-3">
                Conflicts ({report.conflicts.length})
              </h4>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {report.conflicts
                  .filter((c) => c.relevance === "strong")
                  .map((c, i) => (
                    <div
                      key={`strong-${i}`}
                      className="rounded-xl bg-amber-500/5 border border-amber-500/15 p-3"
                    >
                      <p className="text-sm text-zinc-300 mb-2">{c.description}</p>
                      <div className="grid grid-cols-2 gap-3 text-xs">
                        <div className="rounded-lg bg-zinc-900/50 p-2">
                          <span className="text-zinc-500 font-medium">Side A:</span>{" "}
                          <span className="text-zinc-400">{c.side_a.text}</span>
                        </div>
                        <div className="rounded-lg bg-zinc-900/50 p-2">
                          <span className="text-zinc-500 font-medium">Side B:</span>{" "}
                          <span className="text-zinc-400">{c.side_b.text}</span>
                        </div>
                      </div>
                    </div>
                  ))}
              </div>
              {report.conflicts.filter((c) => c.relevance !== "strong").length > 0 && (
                <AnimatedCollapsible
                  title={
                    <span className="text-xs text-zinc-600">
                      {report.conflicts.filter((c) => c.relevance !== "strong").length}{" "}
                      weak conflict(s)
                    </span>
                  }
                  className="mt-2"
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
        </motion.section>

        {/* ─── 2. Pain Map ──────────────────────────────── */}
        <motion.section variants={fadeUp}>
          <SectionHeader
            icon={Layers}
            title="Pain Map"
            count={coreClusters.length}
            subtitle="core clusters"
            color="yellow"
          />
          <div className="space-y-3">
            {coreClusters.map((cluster, i) => (
              <ClusterCard
                key={cluster.id}
                cluster={cluster}
                citations={report.evidence_pack}
                rank={i + 1}
                highlight={highlightedCluster === cluster.id}
              />
            ))}
            {coreClusters.length === 0 && (
              <GlassCard>
                <p className="text-sm text-zinc-500">
                  No idea-specific pain clusters found.
                </p>
              </GlassCard>
            )}
          </div>

          {contextClusters.length > 0 && (
            <div className="mt-6">
              <h3 className="text-sm font-medium text-zinc-500 mb-3">
                Macro Drivers ({contextClusters.length})
              </h3>
              <p className="text-xs text-zinc-600 mb-3">
                Cross-domain pains that inform urgency and payability but are not product wedges.
              </p>
              <div className="space-y-3 opacity-80">
                {contextClusters.map((cluster, i) => (
                  <ClusterCard
                    key={cluster.id}
                    cluster={cluster}
                    citations={report.evidence_pack}
                    rank={coreClusters.length + i + 1}
                  />
                ))}
              </div>
            </div>
          )}
        </motion.section>

        {/* ─── 3. Competitors ───────────────────────────── */}
        <motion.section variants={fadeUp}>
          <SectionHeader
            icon={Swords}
            title="Competitors"
            count={report.competitors.length}
            color="red"
          />
          {report.competitors.length === 0 ? (
            <GlassCard>
              <p className="text-sm text-zinc-500">No competitors identified in evidence.</p>
            </GlassCard>
          ) : (
            <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
              {report.competitors.map((comp) => (
                <CompetitorCard
                  key={comp.name}
                  competitor={comp}
                  citations={report.evidence_pack}
                />
              ))}
            </div>
          )}
        </motion.section>

        {/* ─── 4. Skeptic Flags ─────────────────────────── */}
        {report.skeptic_flags.length > 0 && (
          <motion.section variants={fadeUp}>
            <SectionHeader
              icon={AlertTriangle}
              title="Skeptic Flags"
              count={report.skeptic_flags.length}
              color="orange"
            />
            {/* Severity summary badges */}
            {(() => {
              const flags = report.skeptic_flags.map((f) => ({
                text: f,
                severity: classifyFlagSeverity(f),
              }));
              const highCount = flags.filter((f) => f.severity === "high").length;
              const medCount = flags.filter((f) => f.severity === "medium").length;
              const lowCount = flags.filter((f) => f.severity === "low").length;

              return (
                <>
                  <div className="flex gap-2 mb-4">
                    {highCount > 0 && (
                      <span className="rounded-full bg-red-500/10 border border-red-500/20 px-3 py-1 text-xs text-red-400 font-medium">
                        {highCount} high
                      </span>
                    )}
                    {medCount > 0 && (
                      <span className="rounded-full bg-amber-500/10 border border-amber-500/20 px-3 py-1 text-xs text-amber-400 font-medium">
                        {medCount} medium
                      </span>
                    )}
                    {lowCount > 0 && (
                      <span className="rounded-full bg-zinc-700/50 border border-zinc-600/30 px-3 py-1 text-xs text-zinc-500 font-medium">
                        {lowCount} low
                      </span>
                    )}
                  </div>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                    {flags.map((f, i) => (
                      <SkepticFlagCard key={i} flag={f.text} severity={f.severity} />
                    ))}
                  </div>
                </>
              );
            })()}
          </motion.section>
        )}

        {/* ─── 5. Payability ────────────────────────────── */}
        <motion.section variants={fadeUp}>
          <SectionHeader icon={DollarSign} title="Payability Signals" color="green" />
          <GlassCard>
            <div className="mb-3">
              <StrengthBadge strength={report.payability.overall_strength} />
              <p className="mt-2 text-sm text-zinc-400">{report.payability.summary}</p>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {report.payability.hiring_signals.length > 0 && (
                <div>
                  <h4 className="text-xs font-medium text-zinc-500 mb-1.5">Hiring Signals</h4>
                  <ClaimList claims={report.payability.hiring_signals} citations={report.evidence_pack} />
                </div>
              )}
              {report.payability.outsourcing_signals.length > 0 && (
                <div>
                  <h4 className="text-xs font-medium text-zinc-500 mb-1.5">Outsourcing Signals</h4>
                  <ClaimList claims={report.payability.outsourcing_signals} citations={report.evidence_pack} />
                </div>
              )}
              {report.payability.template_sop_signals.length > 0 && (
                <div>
                  <h4 className="text-xs font-medium text-zinc-500 mb-1.5">Template / SOP Signals</h4>
                  <ClaimList claims={report.payability.template_sop_signals} citations={report.evidence_pack} />
                </div>
              )}
            </div>
          </GlassCard>
        </motion.section>

        {/* ─── 6. Validation Plan ───────────────────────── */}
        <motion.section variants={fadeUp}>
          <SectionHeader icon={Clipboard} title="7-Day Validation Plan" color="accent" />
          <div className="max-w-4xl mx-auto">
            <GlassCard>
              <ValidationPlanView plan={report.validation_plan} />
            </GlassCard>
          </div>
        </motion.section>

        {/* ─── 7. Evidence Appendix ─────────────────────── */}
        <motion.section variants={fadeUp}>
          <SectionHeader
            icon={BookOpen}
            title="Evidence Appendix"
            count={report.evidence_pack.length}
            subtitle="citations"
            color="accent"
          />
          <GlassCard padding={false}>
            <AnimatedCollapsible title="Browse citations" defaultOpen={false}>
              <EvidenceList citations={report.evidence_pack} jobId={report.id} />
            </AnimatedCollapsible>
          </GlassCard>
        </motion.section>
      </div>
    </motion.div>
  );
}

// ─── Validation Plan ──────────────────────────────────

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
      ? { label: "Landing Page Hypotheses", list: plan.landing_page_hypotheses }
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
          <div className="flex flex-col items-center">
            <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-indigo-400/10 text-xs font-bold text-indigo-400">
              {i + 1}
            </div>
            {i < sections.length - 1 && (
              <div className="w-px flex-1 bg-zinc-800/60" />
            )}
          </div>
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

      <div className="rounded-xl bg-green-500/5 border border-green-500/15 px-4 py-3 mt-2">
        <h4 className="text-xs font-medium text-green-400 mb-0.5">
          Success Threshold
        </h4>
        <p className="text-sm text-zinc-200 font-medium">
          {plan.success_threshold}
        </p>
      </div>

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

// ─── Evidence List ────────────────────────────────────

function EvidenceList({
  citations,
  jobId,
}: {
  citations: Citation[];
  jobId: string;
}) {
  const [search, setSearch] = useState("");
  const [filterType, setFilterType] = useState<string>("all");

  const filtered = citations.filter((c) => {
    const matchesSearch =
      !search ||
      c.excerpt.toLowerCase().includes(search.toLowerCase()) ||
      c.url.toLowerCase().includes(search.toLowerCase());
    const matchesType = filterType === "all" || c.source_type === filterType;
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
                <span className="font-mono text-indigo-400/80">[{globalIdx}]</span>
                <span className="inline-flex items-center gap-1 text-zinc-600 capitalize">
                  <Icon size={11} />
                  {c.source_type.replace("_", " ")}
                </span>
              </div>
              <p className="text-zinc-400 mb-1.5 leading-relaxed">{c.excerpt}</p>
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
                  <span className="text-zinc-600 shrink-0 ml-2">{c.date_published}</span>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
