"use client";

import { motion } from "framer-motion";
import type { PainCluster } from "@/lib/types";

interface ClusterPreviewCardProps {
  cluster: PainCluster;
  rank: number;
  onClick: () => void;
}

function scoreColor(score: number): string {
  if (score >= 4) return "bg-green-400";
  if (score >= 3) return "bg-indigo-400";
  if (score >= 2) return "bg-yellow-400";
  return "bg-red-400";
}

const fadeUp = {
  hidden: { opacity: 0, y: 16 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.3, ease: "easeOut" as const } },
};

export function ClusterPreviewCard({
  cluster,
  rank,
  onClick,
}: ClusterPreviewCardProps) {
  const confPct = Math.round(cluster.confidence * 100);
  const dims = [
    { label: "Freq", score: cluster.scores.frequency.score },
    { label: "Sev", score: cluster.scores.severity.score },
    { label: "Pay", score: cluster.scores.payability.score },
  ];

  return (
    <motion.button
      type="button"
      variants={fadeUp}
      onClick={onClick}
      className="glass-card glass-card-hover p-4 text-left w-full relative overflow-hidden cursor-pointer"
    >
      {/* Rank badge */}
      <div className="absolute top-3 right-3 w-7 h-7 rounded-full bg-indigo-400/15 flex items-center justify-center">
        <span className="text-xs font-bold text-indigo-400">#{rank}</span>
      </div>

      {/* Statement */}
      <p className="text-sm font-medium text-zinc-200 leading-snug line-clamp-2 pr-10 mb-2">
        {cluster.statement.text}
      </p>

      {/* Who */}
      <p className="text-xs text-zinc-500 mb-3">{cluster.who}</p>

      {/* Mini score indicators */}
      <div className="flex items-center gap-4 text-[11px] font-mono text-zinc-400">
        {dims.map((d) => (
          <span key={d.label} className="flex items-center gap-1.5">
            <span className={`w-1.5 h-1.5 rounded-full ${scoreColor(d.score)}`} />
            {d.label}: {d.score}
          </span>
        ))}
      </div>

      {/* Confidence bar at bottom */}
      <div className="absolute bottom-0 left-0 right-0 h-[2px] bg-zinc-800">
        <div
          className="h-full bg-indigo-400/50 rounded-full"
          style={{ width: `${confPct}%` }}
        />
      </div>
    </motion.button>
  );
}

export function EmptyClusterSlot() {
  return (
    <div className="glass-card border-dashed border-zinc-700/40 p-4 flex items-center justify-center min-h-[130px]">
      <span className="text-sm text-zinc-600">No more clusters</span>
    </div>
  );
}
