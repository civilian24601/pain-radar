"use client";

import { motion } from "framer-motion";
import {
  FileText,
  Search,
  Database,
  Filter,
  Brain,
  GitCompare,
  Scale,
  Map,
  ShieldAlert,
  Package,
  Check,
} from "lucide-react";

const STAGES = [
  { key: "intake", label: "Parsing idea", icon: FileText },
  { key: "query_generation", label: "Generating search queries", icon: Search },
  { key: "evidence_collection", label: "Collecting evidence", icon: Database },
  { key: "topic_relevance_check", label: "Checking relevance", icon: Filter },
  { key: "analysis", label: "Analyzing pain points", icon: Brain },
  { key: "conflict_detection", label: "Detecting conflicts", icon: GitCompare },
  { key: "verdict", label: "Generating verdict", icon: Scale },
  { key: "validation_plan", label: "Building validation plan", icon: Map },
  { key: "skeptic_pass", label: "Running skeptic review", icon: ShieldAlert },
  { key: "assembly", label: "Assembling report", icon: Package },
] as const;

interface StageTimelineProps {
  currentStage: string;
  currentAction?: string;
}

export function StageTimeline({
  currentStage,
  currentAction,
}: StageTimelineProps) {
  const currentIndex = STAGES.findIndex((s) => s.key === currentStage);

  return (
    <div className="space-y-0">
      {STAGES.map((stage, i) => {
        const isDone = i < currentIndex;
        const isCurrent = i === currentIndex;
        const Icon = stage.icon;

        return (
          <div key={stage.key} className="flex items-stretch gap-3">
            {/* Icon column with connector */}
            <div className="flex flex-col items-center">
              {/* Icon circle */}
              <div
                className={`relative flex h-8 w-8 shrink-0 items-center justify-center rounded-full transition-all duration-300 ${
                  isDone
                    ? "bg-green-500/20"
                    : isCurrent
                      ? "bg-indigo-400/20"
                      : "bg-zinc-800"
                }`}
                style={
                  isCurrent
                    ? { animation: "pulse-ring 2s ease-in-out infinite" }
                    : undefined
                }
              >
                {isDone ? (
                  <Check size={14} className="text-green-400" />
                ) : (
                  <Icon
                    size={14}
                    className={
                      isCurrent ? "text-indigo-400" : "text-zinc-600"
                    }
                  />
                )}
              </div>

              {/* Connector line */}
              {i < STAGES.length - 1 && (
                <div
                  className={`w-px flex-1 min-h-[16px] ${
                    isDone
                      ? "bg-green-500/40"
                      : "border-l border-dashed border-zinc-800"
                  }`}
                />
              )}
            </div>

            {/* Text column */}
            <div className="pb-4 pt-1">
              <span
                className={`text-sm transition-colors duration-300 ${
                  isDone
                    ? "text-zinc-500"
                    : isCurrent
                      ? "text-zinc-100 font-medium"
                      : "text-zinc-600"
                }`}
              >
                {stage.label}
              </span>
              {isCurrent && currentAction && (
                <motion.p
                  initial={{ opacity: 0, y: -4 }}
                  animate={{ opacity: 1, y: 0 }}
                  key={currentAction}
                  className="text-xs text-zinc-500 mt-0.5 max-w-[280px] truncate"
                >
                  {currentAction}
                </motion.p>
              )}
            </div>
          </div>
        );
      })}
    </div>
  );
}
