"use client";

import type { JobProgress, JobStatus } from "@/lib/types";

const STAGE_LABELS: Record<string, string> = {
  intake: "Parsing idea",
  query_generation: "Generating search queries",
  evidence_collection: "Collecting evidence",
  topic_relevance_check: "Checking evidence relevance",
  analysis: "Analyzing pain points",
  conflict_detection: "Detecting conflicts",
  verdict: "Generating verdict",
  validation_plan: "Building validation plan",
  skeptic_pass: "Running skeptic review",
  assembly: "Assembling report",
  complete: "Complete",
  failed: "Failed",
};

const STAGE_ORDER = [
  "intake",
  "query_generation",
  "evidence_collection",
  "topic_relevance_check",
  "analysis",
  "conflict_detection",
  "verdict",
  "validation_plan",
  "skeptic_pass",
  "assembly",
];

interface Props {
  status: JobStatus;
  progress: JobProgress | null;
}

export function ResearchProgress({ status, progress }: Props) {
  const currentStage = progress?.stage || "intake";
  const currentIndex = STAGE_ORDER.indexOf(currentStage);

  return (
    <div className="w-full max-w-2xl space-y-6">
      <div className="text-center">
        <div className="inline-flex items-center gap-2 text-zinc-300">
          <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24" fill="none">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
          </svg>
          <span className="text-lg font-medium">
            {progress?.current_action || STAGE_LABELS[currentStage] || "Processing..."}
          </span>
        </div>
      </div>

      {/* Stage progress */}
      <div className="space-y-2">
        {STAGE_ORDER.map((stage, i) => {
          const isDone = i < currentIndex;
          const isCurrent = i === currentIndex;
          return (
            <div key={stage} className="flex items-center gap-3 text-sm">
              <div
                className={`w-2 h-2 rounded-full ${
                  isDone
                    ? "bg-green-500"
                    : isCurrent
                    ? "bg-zinc-100 animate-pulse"
                    : "bg-zinc-700"
                }`}
              />
              <span className={isDone ? "text-zinc-400" : isCurrent ? "text-zinc-100" : "text-zinc-600"}>
                {STAGE_LABELS[stage]}
              </span>
            </div>
          );
        })}
      </div>

      {/* Citation counter */}
      {progress && progress.citations_found > 0 && (
        <div className="text-center text-sm text-zinc-500">
          {progress.citations_found} citation{progress.citations_found !== 1 ? "s" : ""} collected
          {progress.source_packs_total > 0 && (
            <> | {progress.source_packs_done}/{progress.source_packs_total} source packs</>
          )}
        </div>
      )}
    </div>
  );
}
