import type {
  ReportResponse,
  RunRequest,
  RunResponse,
  StatusResponse,
} from "./types";

const ENGINE_BASE = "/api/engine/research";

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${ENGINE_BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) {
    const body = await res.text();
    throw new Error(`API error ${res.status}: ${body}`);
  }
  return res.json();
}

export async function startResearch(req: RunRequest): Promise<RunResponse> {
  return request<RunResponse>("/run", {
    method: "POST",
    body: JSON.stringify(req),
  });
}

export async function getStatus(jobId: string): Promise<StatusResponse> {
  return request<StatusResponse>(`/${jobId}/status`);
}

export async function getReport(jobId: string): Promise<ReportResponse> {
  return request<ReportResponse>(`/${jobId}/report`);
}

export async function submitClarification(
  jobId: string,
  answers: { question: string; answer: string }[]
): Promise<StatusResponse> {
  return request<StatusResponse>(`/${jobId}/clarify`, {
    method: "POST",
    body: JSON.stringify({ answers }),
  });
}

export function getExportUrl(jobId: string, format: "json" | "csv"): string {
  return `${ENGINE_BASE}/${jobId}/export?format=${format}`;
}
