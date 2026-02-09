"use client";

import { useState } from "react";
import type { Citation, PainCluster, ScoredDimension } from "@/lib/types";
import { CitationChip } from "@/components/ui/citation-chip";
import { ScoreGauge } from "@/components/ui/score-gauge";
import { RadarChart } from "@/components/ui/radar-chart";

interface ClusterCardProps {
  cluster: PainCluster;
  citations: Citation[];
  rank: number;
  highlight?: boolean;
}

export function ClusterCard({
  cluster,
  citations,
  rank,
  highlight = false,
}: ClusterCardProps) {
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

  const confPct = Math.round(cluster.confidence * 100);

  return (
    <div
      id={`cluster-${cluster.id}`}
      className={`neu-card overflow-hidden ${highlight ? "scroll-highlight" : ""} ${
        rank <= 3 ? "glow-accent" : ""
      }`}
    >
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
          <p className="text-base text-zinc-200 leading-snug font-medium">
            {cluster.statement.text}
          </p>
          <div className="flex items-center gap-3 mt-1.5">
            <span className="text-xs text-zinc-500">{cluster.who}</span>
            {cluster.category === "context" && (
              <span className="rounded-full bg-zinc-700/50 px-2 py-0.5 text-[10px] text-zinc-500">
                macro driver
              </span>
            )}
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
