"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { getReport, getStatus } from "@/lib/api-client";
import type { ReportResponse, StatusResponse } from "@/lib/types";
import type { FeedEntry } from "@/components/ui/live-feed";

const POLL_INTERVAL = 2000; // 2 seconds

export interface StageEntry {
  stage: string;
  timestamp: number;
}

export function useResearch(jobId: string) {
  const [status, setStatus] = useState<StatusResponse | null>(null);
  const [report, setReport] = useState<ReportResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Enhanced tracking
  const [stageHistory, setStageHistory] = useState<StageEntry[]>([]);
  const [activityLog, setActivityLog] = useState<FeedEntry[]>([]);
  const [startTime] = useState(() => Date.now());

  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const retryCountRef = useRef(0);
  const lastActionRef = useRef("");
  const feedIdRef = useRef(0);
  const lastStageRef = useRef("");
  const MAX_RETRIES = 3;

  const stopPolling = useCallback(() => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }
  }, []);

  const poll = useCallback(async () => {
    try {
      const s = await getStatus(jobId);
      setStatus(s);
      retryCountRef.current = 0;

      // Track stage transitions
      const currentStage = s.progress?.stage;
      if (currentStage && currentStage !== lastStageRef.current) {
        lastStageRef.current = currentStage;
        setStageHistory((prev) => [
          ...prev,
          { stage: currentStage, timestamp: Date.now() },
        ]);
      }

      // Track unique activity actions
      const action = s.progress?.current_action;
      if (action && action !== lastActionRef.current) {
        lastActionRef.current = action;
        feedIdRef.current += 1;
        const now = new Date();
        const time = [now.getHours(), now.getMinutes(), now.getSeconds()]
          .map((n) => String(n).padStart(2, "0"))
          .join(":");
        setActivityLog((prev) => [
          ...prev,
          { id: feedIdRef.current, text: action, time },
        ]);
      }

      if (s.status === "complete") {
        stopPolling();
        const r = await getReport(jobId);
        setReport(r);
      } else if (s.status === "failed") {
        stopPolling();
        setError("Research failed. Check engine logs for details.");
      }
    } catch (e) {
      retryCountRef.current += 1;
      if (retryCountRef.current >= MAX_RETRIES) {
        setError(e instanceof Error ? e.message : "Unknown error");
        stopPolling();
      }
    }
  }, [jobId, stopPolling]);

  useEffect(() => {
    // Start polling immediately
    poll();
    intervalRef.current = setInterval(poll, POLL_INTERVAL);

    return () => {
      stopPolling();
    };
  }, [poll, stopPolling]);

  return { status, report, error, stopPolling, stageHistory, activityLog, startTime };
}
