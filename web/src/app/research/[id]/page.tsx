"use client";

import { use } from "react";
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
  const { status, report, error } = useResearch(id);

  return (
    <main className="min-h-screen bg-zinc-950 flex flex-col items-center px-4 py-12">
      <a href="/" className="text-sm text-zinc-500 hover:text-zinc-300 mb-8">
        &larr; Pain Radar
      </a>

      {error && (
        <div className="w-full max-w-2xl text-red-400 text-sm bg-red-950/50 border border-red-800 rounded px-4 py-3 mb-4">
          {error}
        </div>
      )}

      {!status && !error && (
        <div className="text-zinc-500">Loading...</div>
      )}

      {/* Clarification state */}
      {status?.status === "clarifying" && status.clarification_questions && (
        <ClarificationStep
          jobId={id}
          questions={status.clarification_questions}
          onComplete={() => window.location.reload()}
        />
      )}

      {/* Active research */}
      {status && isActiveStatus(status.status) && (
        <ResearchProgress
          status={status.status}
          progress={status.progress}
        />
      )}

      {/* Complete — show report */}
      {report?.report && (
        <ReportView report={report.report} />
      )}

      {/* Failed */}
      {status?.status === "failed" && !error && (
        <div className="text-center">
          <p className="text-zinc-400 mb-4">Research could not be completed.</p>
          <a
            href="/"
            className="rounded-lg bg-zinc-800 px-6 py-2.5 text-sm text-zinc-300 hover:bg-zinc-700"
          >
            Try another idea
          </a>
        </div>
      )}
    </main>
  );
}

function isActiveStatus(status: JobStatus): boolean {
  return ["created", "researching", "analyzing", "reviewing"].includes(status);
}
