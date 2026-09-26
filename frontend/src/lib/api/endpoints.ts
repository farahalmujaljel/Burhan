/** Typed functions for every backend endpoint the frontend uses. */
import { request } from "./client";
import type {
  EntityType,
  GraphView,
  HealthResponse,
  NodeDetail,
  PaperKnowledge,
  PaperRecord,
  ParsedDocument,
  RecordKind,
  TwinSummary,
  TwinUpdate,
  UploadResponse,
  VectorHit,
} from "./types";

const enc = encodeURIComponent;

export const api = {
  health: () => request<HealthResponse>("/health"),

  papers: {
    list: () => request<PaperRecord[]>("/papers"),
    get: (id: string) => request<PaperRecord>(`/papers/${enc(id)}`),
    document: (id: string) => request<ParsedDocument>(`/papers/${enc(id)}/document`),
    knowledge: (id: string) => request<PaperKnowledge>(`/papers/${enc(id)}/knowledge`),
    upload: (files: File[]) => {
      const body = new FormData();
      files.forEach((f) => body.append("files", f, f.name));
      return request<UploadResponse>("/papers", { method: "POST", body });
    },
    /** Starts extraction in the background (202); poll the record for `extraction_status`. */
    extract: (id: string) => request<PaperRecord>(`/papers/${enc(id)}/extract`, { method: "POST" }),
    reprocess: (id: string) =>
      request<PaperRecord>(`/papers/${enc(id)}/process`, { method: "POST" }),
  },

  twin: {
    summary: () => request<TwinSummary>("/twin/summary"),
    updates: (limit = 100) => request<TwinUpdate[]>("/twin/updates", { query: { limit } }),
    applyPaper: (id: string) =>
      request<TwinUpdate>(`/twin/papers/${enc(id)}`, { method: "POST" }),
  },

  graph: {
    view: (params: { paperId?: string; types?: EntityType[]; limit?: number } = {}) =>
      request<GraphView>("/graph", {
        query: { paper_id: params.paperId, type: params.types, limit: params.limit },
      }),
    node: (id: string) => request<NodeDetail>(`/graph/nodes/${enc(id)}`),
  },

  evidence: {
    search: (params: { q: string; paperId?: string; kind?: RecordKind; limit?: number }) =>
      request<VectorHit[]>("/evidence/search", {
        query: { q: params.q, paper_id: params.paperId, kind: params.kind, limit: params.limit },
      }),
  },
};
