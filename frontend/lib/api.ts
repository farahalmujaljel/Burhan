import type { GroundedAnswer, RunSummary } from "./types";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000";

export async function createRun(files: File[]): Promise<RunSummary> {
  const form = new FormData();
  files.forEach((file) => form.append("files", file));
  const response = await fetch(`${API_URL}/api/runs`, {
    method: "POST",
    body: form
  });
  if (!response.ok) {
    const detail = await response.text();
    throw new Error(detail);
  }
  return response.json();
}

export async function askBurhan(runId: string, question: string): Promise<GroundedAnswer> {
  const response = await fetch(`${API_URL}/api/runs/${runId}/ask`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question })
  });
  if (!response.ok) {
    const detail = await response.text();
    throw new Error(detail);
  }
  return response.json();
}
