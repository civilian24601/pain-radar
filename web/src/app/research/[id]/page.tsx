"use client";

import { use } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { useResearch } from "@/hooks/use-research";
import { ClarificationStep } from "@/components/clarification-step";
import { ResearchProgress } from "@/components/research-progress";
import { ReportView } from "@/components/report-view";
import type { JobStatus } from "@/lib/types";

export default function ResearchPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = use(params);
  const { status, report, error, activityLog, startTime } = useResearch(id);

  const currentView = report?.report
    ? "report"
    : status?.status === "clarifying"
      ? "clarifying"
      : status && isActiveStatus(status.status)
        ? "progress"
        : status?.status === "failed"
          ? "failed"
          : "loading";

  return (
    <main className="min-h-screen flex flex-col items-center px-4 py-12">
      <a
        href="/"
        className="inline-flex items-center gap-1.5 text-sm text-zinc-500 hover:text-zinc-300 transition-colors mb-8 glass-card px-4 py-2 rounded-full"
      >
        &larr; Pain Radar
      </a>

      {error && (
        <motion.div
          initial={{ opacity: 0, y: -8 }}
          animate={{ opacity: 1, y: 0 }}
          className="w-full max-w-2xl text-red-400 text-sm bg-red-950/50 border border-red-800/60 rounded-xl px-4 py-3 mb-4"
        >
          {error}
        </motion.div>
      )}

      <AnimatePresence mode="wait">
        {/* Loading */}
        {currentView === "loading" && !error && (
          <motion.div
            key="loading"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="text-zinc-500"
          >
            Loading...
          </motion.div>
        )}

        {/* Clarification state */}
        {currentView === "clarifying" &&
          status?.clarification_questions && (
            <motion.div
              key="clarifying"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.98 }}
              transition={{ duration: 0.3 }}
            >
              <ClarificationStep
                jobId={id}
                questions={status.clarification_questions}
                onComplete={() => window.location.reload()}
              />
            </motion.div>
          )}

        {/* Active research */}
        {currentView === "progress" && status && (
          <motion.div
            key="progress"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.98 }}
            transition={{ duration: 0.3 }}
            className="w-full flex justify-center"
          >
            <ResearchProgress
              status={status.status}
              progress={status.progress}
              activityLog={activityLog}
              startTime={startTime}
            />
          </motion.div>
        )}

        {/* Complete — show report */}
        {currentView === "report" && report?.report && (
          <motion.div
            key="report"
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4 }}
            className="w-full flex justify-center"
          >
            <ReportView report={report.report} />
          </motion.div>
        )}

        {/* Failed */}
        {currentView === "failed" && !error && (
          <motion.div
            key="failed"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="text-center"
          >
            <p className="text-zinc-400 mb-4">
              Research could not be completed.
            </p>
            <a
              href="/"
              className="inline-block rounded-xl bg-zinc-800 px-6 py-2.5 text-sm text-zinc-300 hover:bg-zinc-700 transition-colors"
            >
              Try another idea
            </a>
          </motion.div>
        )}
      </AnimatePresence>
    </main>
  );
}

function isActiveStatus(status: JobStatus): boolean {
  return ["created", "researching", "analyzing", "reviewing"].includes(status);
}
