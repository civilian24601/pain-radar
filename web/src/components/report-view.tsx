"use client";

import { useState } from "react";
import { getExportUrl } from "@/lib/api-client";
import type {
  Citation,
  Competitor,
  EvidencedClaim,
  PainCluster,
  ResearchReport,
  ScoredDimension,
} from "@/lib/types";

interface Props {
  report: ResearchReport;
}

const VERDICT_STYLES: Record<string, string> = {
  KILL: "bg-red-950 border-red-700 text-red-300",
  NARROW: "bg-yellow-950 border-yellow-700 text-yellow-300",
  ADVANCE: "bg-green-950 border-green-700 text-green-300",
  INSUFFICIENT_EVIDENCE: "bg-zinc-900 border-zinc-600 text-zinc-300",
};

const VERDICT_LABELS: Record<string, string> = {
  KILL: "KILL",
  NARROW: "NARROW",
  ADVANCE: "ADVANCE",
  INSUFFICIENT_EVIDENCE: "INSUFFICIENT EVIDENCE",
};

export function ReportView({ report }: Props) {
  return (
    <div className="w-full max-w-4xl space-y-4">
      {/* Executive Summary */}
      <Section title="Executive Summary" defaultOpen>
        <VerdictBadge decision={report.verdict.decision} />
        <div className="mt-4 space-y-3">
          <div>
            <h4 className="text-sm font-medium text-zinc-400 mb-1">Top Reasons</h4>
            <ClaimList claims={report.verdict.reasons} citations={report.evidence_pack} />
          </div>
          <div>
            <h4 className="text-sm font-medium text-zinc-400 mb-1">Top Risks</h4>
            <ClaimList claims={report.verdict.risks} citations={report.evidence_pack} />
          </div>
          <div>
            <h4 className="text-sm font-medium text-zinc-400 mb-1">Narrowest Wedge</h4>
            <p className="text-sm text-zinc-300">{report.verdict.narrowest_wedge}</p>
          </div>
          <div>
            <h4 className="text-sm font-medium text-zinc-400 mb-1">What Would Change This Verdict</h4>
            <p className="text-sm text-zinc-300">{report.verdict.what_would_change}</p>
          </div>
        </div>

        {/* Conflicts */}
        {report.conflicts.length > 0 && (
          <div className="mt-4 border-t border-zinc-800 pt-3">
            <h4 className="text-sm font-medium text-amber-400 mb-2">
              Conflicts Detected ({report.conflicts.length})
            </h4>
            {report.conflicts.filter(c => c.relevance === "strong").map((c, i) => (
              <div key={`strong-${i}`} className="mb-2 text-sm bg-amber-950/30 border border-amber-900/50 rounded p-3">
                <p className="text-zinc-300 mb-1">{c.description}</p>
                <p className="text-zinc-500">A: {c.side_a.text}</p>
                <p className="text-zinc-500">B: {c.side_b.text}</p>
              </div>
            ))}
            {report.conflicts.filter(c => c.relevance !== "strong").length > 0 && (
              <details className="mt-2">
                <summary className="text-xs text-zinc-600 cursor-pointer hover:text-zinc-400">
                  {report.conflicts.filter(c => c.relevance !== "strong").length} weak conflict(s)
                </summary>
                {report.conflicts.filter(c => c.relevance !== "strong").map((c, i) => (
                  <div key={`weak-${i}`} className="mb-2 mt-2 text-sm bg-zinc-900/30 border border-zinc-800/50 rounded p-3">
                    <p className="text-zinc-500 mb-1">{c.description}</p>
                    <p className="text-zinc-600">A: {c.side_a.text}</p>
                    <p className="text-zinc-600">B: {c.side_b.text}</p>
                  </div>
                ))}
              </details>
            )}
          </div>
        )}

        {/* Skeptic flags */}
        {report.skeptic_flags.length > 0 && (
          <div className="mt-4 border-t border-zinc-800 pt-3">
            <h4 className="text-sm font-medium text-orange-400 mb-2">
              Skeptic Flags ({report.skeptic_flags.length})
            </h4>
            <ul className="list-disc list-inside space-y-1">
              {report.skeptic_flags.map((flag, i) => (
                <li key={i} className="text-sm text-zinc-400">{flag}</li>
              ))}
            </ul>
          </div>
        )}
      </Section>

      {/* Pain Map */}
      <Section title={`Pain Map (${report.pain_map.length} clusters)`}>
        {[...report.pain_map]
          .sort((a, b) => {
            const scoreSum = (c: PainCluster) =>
              c.scores.frequency.score + c.scores.severity.score + c.scores.payability.score;
            return scoreSum(b) - scoreSum(a);
          })
          .map((cluster, i) => (
            <ClusterCard key={cluster.id} cluster={cluster} citations={report.evidence_pack} rank={i + 1} />
          ))}
      </Section>

      {/* Competitor Table */}
      <Section title={`Competitors (${report.competitors.length})`}>
        {report.competitors.length === 0 ? (
          <p className="text-sm text-zinc-500">No competitors identified in evidence.</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left text-zinc-500 border-b border-zinc-800">
                  <th className="pb-2 pr-4">Name</th>
                  <th className="pb-2 pr-4">Pricing Page</th>
                  <th className="pb-2 pr-4">Min Price</th>
                  <th className="pb-2 pr-4">Onboarding</th>
                  <th className="pb-2">Positioning</th>
                </tr>
              </thead>
              <tbody>
                {report.competitors.map((comp) => (
                  <CompetitorRow key={comp.name} competitor={comp} />
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Section>

      {/* Payability Signals */}
      <Section title="Payability Signals">
        <div className="mb-3">
          <span className={`inline-block rounded-full px-3 py-1 text-xs font-medium ${
            report.payability.overall_strength === "strong" ? "bg-green-950 text-green-300" :
            report.payability.overall_strength === "moderate" ? "bg-yellow-950 text-yellow-300" :
            report.payability.overall_strength === "weak" ? "bg-orange-950 text-orange-300" :
            "bg-zinc-800 text-zinc-400"
          }`}>
            {report.payability.overall_strength}
          </span>
          <p className="mt-2 text-sm text-zinc-400">{report.payability.summary}</p>
        </div>
        {report.payability.hiring_signals.length > 0 && (
          <div className="mb-2">
            <h4 className="text-xs font-medium text-zinc-500 mb-1">Hiring Signals</h4>
            <ClaimList claims={report.payability.hiring_signals} citations={report.evidence_pack} />
          </div>
        )}
        {report.payability.outsourcing_signals.length > 0 && (
          <div className="mb-2">
            <h4 className="text-xs font-medium text-zinc-500 mb-1">Outsourcing Signals</h4>
            <ClaimList claims={report.payability.outsourcing_signals} citations={report.evidence_pack} />
          </div>
        )}
      </Section>

      {/* 7-Day Validation Plan */}
      <Section title="7-Day Validation Plan" defaultOpen>
        <div className="space-y-4">
          <div>
            <h4 className="text-sm font-medium text-zinc-400">Objective</h4>
            <p className="text-sm text-zinc-300">{report.validation_plan.objective}</p>
          </div>

          {report.validation_plan.channels.length > 0 && (
            <div>
              <h4 className="text-sm font-medium text-zinc-400">Channels</h4>
              <ul className="list-disc list-inside text-sm text-zinc-300">
                {report.validation_plan.channels.map((ch, i) => <li key={i}>{ch}</li>)}
              </ul>
            </div>
          )}

          {report.validation_plan.outreach_targets.length > 0 && (
            <div>
              <h4 className="text-sm font-medium text-zinc-400">Outreach Targets</h4>
              <ul className="list-disc list-inside text-sm text-zinc-300">
                {report.validation_plan.outreach_targets.map((t, i) => <li key={i}>{t}</li>)}
              </ul>
            </div>
          )}

          {report.validation_plan.interview_script && (
            <div>
              <h4 className="text-sm font-medium text-zinc-400">Interview Script</h4>
              <pre className="text-sm text-zinc-300 whitespace-pre-wrap bg-zinc-900 rounded p-3 border border-zinc-800">
                {report.validation_plan.interview_script}
              </pre>
            </div>
          )}

          {report.validation_plan.landing_page_hypotheses.length > 0 && (
            <div>
              <h4 className="text-sm font-medium text-zinc-400">Landing Page Hypotheses</h4>
              {report.validation_plan.landing_page_hypotheses.map((h, i) => (
                <p key={i} className="text-sm text-zinc-300 mb-1">{i + 1}. {h}</p>
              ))}
            </div>
          )}

          {report.validation_plan.concierge_procedure && (
            <div>
              <h4 className="text-sm font-medium text-zinc-400">Concierge MVP Procedure</h4>
              <p className="text-sm text-zinc-300">{report.validation_plan.concierge_procedure}</p>
            </div>
          )}

          <div>
            <h4 className="text-sm font-medium text-zinc-400">Success Threshold</h4>
            <p className="text-sm text-zinc-100 font-medium">{report.validation_plan.success_threshold}</p>
          </div>

          {report.validation_plan.reversal_criteria && (
            <div>
              <h4 className="text-sm font-medium text-amber-400">Reversal Criteria</h4>
              <p className="text-sm text-zinc-300">{report.validation_plan.reversal_criteria}</p>
            </div>
          )}
        </div>
      </Section>

      {/* Evidence Appendix */}
      <Section title={`Evidence Appendix (${report.evidence_pack.length} citations)`}>
        <EvidenceList citations={report.evidence_pack} jobId={report.id} />
      </Section>
    </div>
  );
}

// ---- Sub-components ----

function Section({
  title,
  defaultOpen = false,
  children,
}: {
  title: string;
  defaultOpen?: boolean;
  children: React.ReactNode;
}) {
  return (
    <details open={defaultOpen} className="border border-zinc-800 rounded-lg">
      <summary className="cursor-pointer px-4 py-3 font-medium text-zinc-200 hover:bg-zinc-900/50 select-none">
        {title}
      </summary>
      <div className="px-4 pb-4">{children}</div>
    </details>
  );
}

function VerdictBadge({ decision }: { decision: string }) {
  return (
    <div className={`inline-flex items-center rounded-lg border px-4 py-2 text-lg font-bold ${VERDICT_STYLES[decision] || "bg-zinc-800 border-zinc-700 text-zinc-300"}`}>
      {VERDICT_LABELS[decision] || decision}
    </div>
  );
}

function ClaimList({
  claims,
  citations,
}: {
  claims: EvidencedClaim[];
  citations: { url: string }[];
}) {
  return (
    <ul className="space-y-1.5">
      {claims.map((claim, i) => (
        <li key={i} className="text-sm text-zinc-300">
          {claim.text}
          <span className="ml-1 text-zinc-600">
            [{claim.citation_indices.map((idx) => (
              <a
                key={idx}
                href={citations[idx]?.url || "#"}
                target="_blank"
                rel="noopener noreferrer"
                className="text-zinc-500 hover:text-zinc-300 underline"
              >
                {idx}
              </a>
            )).reduce<React.ReactNode[]>((acc, el, i) => {
              if (i > 0) acc.push(", ");
              acc.push(el);
              return acc;
            }, [])}]
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
  const dims: [string, ScoredDimension][] = [
    ["Frequency", cluster.scores.frequency],
    ["Severity", cluster.scores.severity],
    ["Urgency", cluster.scores.urgency],
    ["Payability", cluster.scores.payability],
    ["Workaround Cost", cluster.scores.workaround_cost],
    ["Saturation (inv)", cluster.scores.saturation],
    ["Accessibility", cluster.scores.accessibility],
  ];

  return (
    <details className="mb-3 border border-zinc-800 rounded">
      <summary className="cursor-pointer px-3 py-2 text-sm select-none">
        <div className="flex justify-between items-start">
          <span className="text-zinc-200">
            <span className="text-zinc-600 mr-2">#{rank}</span>
            {cluster.statement.text}
          </span>
          <span className="text-xs text-zinc-500 ml-2 shrink-0">
            conf: {(cluster.confidence * 100).toFixed(0)}%
          </span>
        </div>
        <div className="mt-1 flex gap-2 text-xs text-zinc-600">
          {cluster.citation_indices.slice(0, 2).map((idx) => {
            const cite = citations[idx];
            if (!cite) return null;
            return (
              <a
                key={idx}
                href={cite.url || "#"}
                target="_blank"
                rel="noopener noreferrer"
                className="truncate max-w-[250px] hover:text-zinc-400 underline"
                onClick={(e) => e.stopPropagation()}
              >
                [{idx}] {cite.excerpt?.slice(0, 60) || ""}...
              </a>
            );
          })}
        </div>
      </summary>
      <div className="px-3 pb-3 space-y-2">
        <div className="flex gap-4 text-xs text-zinc-500">
          <span>Who: {cluster.who}</span>
          <span>Trigger: {cluster.trigger}</span>
        </div>
        {cluster.workarounds.length > 0 && (
          <div className="text-xs text-zinc-500">
            Workarounds: {cluster.workarounds.join(", ")}
          </div>
        )}
        <div className="grid grid-cols-4 gap-2 mt-2">
          {dims.map(([label, dim]) => (
            <div key={label} className="text-center">
              <div className="text-xs text-zinc-500">{label}</div>
              <div className="text-lg font-bold text-zinc-200">{dim.score}</div>
            </div>
          ))}
          <div className="text-center">
            <div className="text-xs text-zinc-500">Recency</div>
            <div className="text-lg font-bold text-zinc-200">
              {(cluster.recency_weight * 100).toFixed(0)}%
            </div>
          </div>
        </div>
      </div>
    </details>
  );
}

function CompetitorRow({ competitor }: { competitor: Competitor }) {
  return (
    <tr className="border-b border-zinc-800/50">
      <td className="py-2 pr-4">
        <a href={competitor.url} target="_blank" rel="noopener noreferrer" className="text-zinc-200 hover:underline">
          {competitor.name}
        </a>
      </td>
      <td className="py-2 pr-4">
        {competitor.pricing_page_exists ? (
          <span className="text-green-400">Yes</span>
        ) : (
          <span className="text-zinc-600">No</span>
        )}
      </td>
      <td className="py-2 pr-4 text-zinc-300">
        {competitor.min_price_observed || <span className="text-zinc-600">unknown</span>}
      </td>
      <td className="py-2 pr-4 text-zinc-400">{competitor.onboarding_model}</td>
      <td className="py-2 text-zinc-400">{competitor.positioning}</td>
    </tr>
  );
}

function EvidenceList({
  citations,
  jobId,
}: {
  citations: { url: string; excerpt: string; source_type: string; date_published: string | null }[];
  jobId: string;
}) {
  const [search, setSearch] = useState("");
  const filtered = search
    ? citations.filter(
        (c) =>
          c.excerpt.toLowerCase().includes(search.toLowerCase()) ||
          c.url.toLowerCase().includes(search.toLowerCase())
      )
    : citations;

  return (
    <div className="space-y-3">
      <div className="flex gap-2">
        <input
          type="text"
          placeholder="Search citations..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="flex-1 rounded border border-zinc-700 bg-zinc-900 px-3 py-1.5 text-sm text-zinc-100 placeholder-zinc-600 focus:border-zinc-500 focus:outline-none"
        />
        <a
          href={getExportUrl(jobId, "json")}
          className="rounded border border-zinc-700 px-3 py-1.5 text-sm text-zinc-400 hover:text-zinc-200 hover:border-zinc-500"
        >
          JSON
        </a>
        <a
          href={getExportUrl(jobId, "csv")}
          className="rounded border border-zinc-700 px-3 py-1.5 text-sm text-zinc-400 hover:text-zinc-200 hover:border-zinc-500"
        >
          CSV
        </a>
      </div>
      <div className="max-h-96 overflow-y-auto space-y-2">
        {filtered.map((c, i) => (
          <div key={i} className="border border-zinc-800/50 rounded p-2 text-xs">
            <div className="flex justify-between items-start mb-1">
              <span className="text-zinc-500 font-mono">[{citations.indexOf(c)}]</span>
              <span className="text-zinc-600">{c.source_type}</span>
            </div>
            <p className="text-zinc-400 mb-1">{c.excerpt}</p>
            <a
              href={c.url}
              target="_blank"
              rel="noopener noreferrer"
              className="text-zinc-500 hover:text-zinc-300 underline truncate block"
            >
              {c.url}
            </a>
            {c.date_published && (
              <span className="text-zinc-600">{c.date_published}</span>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
