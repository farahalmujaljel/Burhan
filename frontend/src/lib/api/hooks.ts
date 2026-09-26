"use client";

/** SWR data hooks. Views poll only while work is in progress on the backend. */
import useSWR from "swr";

import type { ApiError } from "./client";
import { api } from "./endpoints";
import type { EntityType, PaperRecord, RecordKind } from "./types";

const POLL_MS = 3000;

export const isExtracting = (p?: PaperRecord | null) => p?.extraction_status === "running";

export function useHealth() {
  return useSWR("health", api.health, { refreshInterval: 30_000, shouldRetryOnError: false });
}

export function useTwinSummary() {
  return useSWR("twin/summary", api.twin.summary);
}

export function useTwinUpdates(limit = 100) {
  return useSWR(["twin/updates", limit], () => api.twin.updates(limit));
}

export function usePapers() {
  return useSWR<PaperRecord[], ApiError>("papers", api.papers.list, {
    refreshInterval: (papers) => (papers?.some(isExtracting) ? POLL_MS : 0),
  });
}

export function usePaper(id: string) {
  return useSWR<PaperRecord, ApiError>(["paper", id], () => api.papers.get(id), {
    refreshInterval: (p) => (isExtracting(p) ? POLL_MS : 0),
  });
}

export function usePaperDocument(id: string, enabled: boolean) {
  return useSWR(enabled ? ["paper/document", id] : null, () => api.papers.document(id));
}

export function usePaperKnowledge(id: string, enabled: boolean) {
  return useSWR(enabled ? ["paper/knowledge", id] : null, () => api.papers.knowledge(id));
}

export function useGraph(params: { paperId?: string; types?: EntityType[]; limit?: number } = {}) {
  return useSWR(["graph", params.paperId, params.types?.join(","), params.limit], () =>
    api.graph.view(params),
  );
}

export function useNodeDetail(id: string | null) {
  return useSWR(id ? ["graph/node", id] : null, () => api.graph.node(id as string));
}

export function useEvidenceSearch(params: {
  q: string;
  paperId?: string;
  kind?: RecordKind;
  limit?: number;
}) {
  const enabled = params.q.trim().length >= 2;
  return useSWR(
    enabled ? ["evidence/search", params.q, params.paperId, params.kind, params.limit] : null,
    () => api.evidence.search(params),
    { keepPreviousData: true },
  );
}
