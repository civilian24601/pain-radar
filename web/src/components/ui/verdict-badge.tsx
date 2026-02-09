"use client";

import { motion } from "framer-motion";
import { TrendingUp, X, Focus, AlertCircle } from "lucide-react";
import type { VerdictDecision } from "@/lib/types";

const VERDICT_CONFIG: Record<
  string,
  {
    icon: typeof TrendingUp;
    label: string;
    textColor: string;
    glowColor: string;
    borderColor: string;
    bgColor: string;
  }
> = {
  ADVANCE: {
    icon: TrendingUp,
    label: "ADVANCE",
    textColor: "text-green-400",
    glowColor: "rgba(34, 197, 94, 0.2)",
    borderColor: "border-green-500/30",
    bgColor: "bg-green-500/5",
  },
  KILL: {
    icon: X,
    label: "KILL",
    textColor: "text-red-400",
    glowColor: "rgba(239, 68, 68, 0.2)",
    borderColor: "border-red-500/30",
    bgColor: "bg-red-500/5",
  },
  NARROW: {
    icon: Focus,
    label: "NARROW",
    textColor: "text-yellow-400",
    glowColor: "rgba(234, 179, 8, 0.2)",
    borderColor: "border-yellow-500/30",
    bgColor: "bg-yellow-500/5",
  },
  INSUFFICIENT_EVIDENCE: {
    icon: AlertCircle,
    label: "INSUFFICIENT EVIDENCE",
    textColor: "text-zinc-400",
    glowColor: "rgba(161, 161, 170, 0.1)",
    borderColor: "border-zinc-600/30",
    bgColor: "bg-zinc-500/5",
  },
};

interface VerdictBadgeProps {
  decision: VerdictDecision | string;
  size?: "default" | "hero";
}

export function VerdictBadge({ decision, size = "default" }: VerdictBadgeProps) {
  const config = VERDICT_CONFIG[decision] || VERDICT_CONFIG.INSUFFICIENT_EVIDENCE;
  const Icon = config.icon;

  const isHero = size === "hero";

  return (
    <motion.div
      initial={{ scale: 0.85, opacity: 0 }}
      animate={{ scale: 1, opacity: 1 }}
      transition={{ type: "spring", stiffness: 200, damping: 20, delay: 0.15 }}
      className={`inline-flex items-center rounded-2xl border ${config.borderColor} ${config.bgColor} ${
        isHero ? "gap-4 px-8 py-5" : "gap-3 px-6 py-3"
      }`}
      style={{ boxShadow: `0 0 ${isHero ? "60px" : "40px"} ${config.glowColor}` }}
    >
      <Icon size={isHero ? 40 : 28} className={config.textColor} />
      <span className={`font-bold tracking-tight ${config.textColor} ${
        isHero ? "text-5xl" : "text-3xl"
      }`}>
        {config.label}
      </span>
    </motion.div>
  );
}
