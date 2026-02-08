"use client";

import { useEffect, useState } from "react";
import { Database, Layers, Clock } from "lucide-react";
import type { JobProgress, JobStatus } from "@/lib/types";
import type { FeedEntry } from "@/components/ui/live-feed";
import { GlassCard } from "@/components/ui/glass-card";
import { ScanAnimation } from "@/components/ui/scan-animation";
import { StageTimeline } from "@/components/ui/stage-timeline";
import { AnimatedCounter } from "@/components/ui/animated-counter";
import { LiveFeed } from "@/components/ui/live-feed";
import { FactCarousel } from "@/components/ui/fact-carousel";

interface Props {
  status: JobStatus;
  progress: JobProgress | null;
  activityLog: FeedEntry[];
  startTime: number;
}

function ElapsedTime({ startTime }: { startTime: number }) {
  const [elapsed, setElapsed] = useState(0);

  useEffect(() => {
    const tick = () => setElapsed(Math.floor((Date.now() - startTime) / 1000));
    tick();
    const id = setInterval(tick, 1000);
    return () => clearInterval(id);
  }, [startTime]);

  const mins = Math.floor(elapsed / 60);
  const secs = elapsed % 60;

  return (
    <span className="font-mono tabular-nums">
      {String(mins).padStart(2, "0")}:{String(secs).padStart(2, "0")}
    </span>
  );
}

export function ResearchProgress({
  status,
  progress,
  activityLog,
  startTime,
}: Props) {
  const currentStage = progress?.stage || "intake";
  const citations = progress?.citations_found || 0;

  return (
    <div className="w-full max-w-3xl space-y-6">
      {/* Radar scan hero */}
      <div className="flex flex-col items-center gap-4">
        <ScanAnimation citationsFound={citations} />

        {/* Citation counter */}
        <div className="text-center">
          <div className="text-2xl text-indigo-400 font-mono">
            <AnimatedCounter value={citations} className="text-indigo-400" />
          </div>
          <p className="text-sm text-zinc-500 mt-1">
            pieces of evidence collected
          </p>
        </div>
      </div>

      {/* Stage timeline + stats */}
      <GlassCard>
        <StageTimeline
          currentStage={currentStage}
          currentAction={progress?.current_action}
        />

        {/* Stats bar */}
        <div className="grid grid-cols-3 gap-3 mt-5 pt-5 border-t border-zinc-800/60">
          <div className="neu-inset flex flex-col items-center py-3 px-2">
            <Database size={14} className="text-zinc-500 mb-1" />
            <span className="text-lg font-mono text-zinc-100">
              <AnimatedCounter value={citations} />
            </span>
            <span className="text-[10px] uppercase tracking-widest text-zinc-600">
              Citations
            </span>
          </div>
          <div className="neu-inset flex flex-col items-center py-3 px-2">
            <Layers size={14} className="text-zinc-500 mb-1" />
            <span className="text-lg font-mono text-zinc-100">
              {progress?.source_packs_done || 0}/{progress?.source_packs_total || 4}
            </span>
            <span className="text-[10px] uppercase tracking-widest text-zinc-600">
              Sources
            </span>
          </div>
          <div className="neu-inset flex flex-col items-center py-3 px-2">
            <Clock size={14} className="text-zinc-500 mb-1" />
            <span className="text-lg text-zinc-100">
              <ElapsedTime startTime={startTime} />
            </span>
            <span className="text-[10px] uppercase tracking-widest text-zinc-600">
              Elapsed
            </span>
          </div>
        </div>
      </GlassCard>

      {/* Live activity feed */}
      {activityLog.length > 0 && (
        <GlassCard>
          <LiveFeed entries={activityLog} />
        </GlassCard>
      )}

      {/* Fact carousel */}
      <FactCarousel />
    </div>
  );
}
