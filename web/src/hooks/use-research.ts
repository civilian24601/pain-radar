"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { getReport, getStatus } from "@/lib/api-client";
import type { ReportResponse, StatusResponse } from "@/lib/types";

const POLL_INTERVAL = 2000; // 2 seconds

export function useResearch(jobId: string) {
  const [status, setStatus] = useState<StatusResponse | null>(null);
  const [report, setReport] = useState<ReportResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

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

      if (s.status === "complete") {
        stopPolling();
        const r = await getReport(jobId);
        setReport(r);
      } else if (s.status === "failed") {
        stopPolling();
        setError("Research failed. Check engine logs for details.");
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : "Unknown error");
      stopPolling();
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

  return { status, report, error, stopPolling };
}
