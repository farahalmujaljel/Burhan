/**
 * Friendly aliases over the types generated from the backend's OpenAPI schema
 * (`npm run gen:api` regenerates `schema.d.ts` from the FastAPI/Pydantic contracts).
 */
import type { components } from "./schema";

type S = components["schemas"];

export type EntityType = S["EntityType"];
export type RelationType = S["RelationType"];
export type VerificationStatus = S["VerificationStatus"];
export type PaperStatus = S["PaperStatus"];
export type ExtractionStatus = S["ExtractionStatus"];

export type Evidence = S["Evidence"];
export type PaperRecord = S["PaperRecord"];
export type ParsedDocument = S["ParsedDocument"];
export type Section = S["Section"];
export type UploadResponse = S["UploadResponse"];
export type UploadResult = S["UploadResult"];
export type PaperKnowledge = S["PaperKnowledge"];
export type ResearchStatement = S["ResearchStatement"];
export type ExtractionMeta = S["ExtractionMeta"];

export type GraphNode = S["GraphNode"];
export type GraphEdge = S["GraphEdge"];
export type GraphView = S["GraphView"];
export type NodeDetail = S["NodeDetail"];

export type TwinSummary = S["TwinSummary"];
export type TwinUpdate = S["TwinUpdate"];
export type RankedEntity = S["RankedEntity"];
export type ResolutionDecision = S["ResolutionDecision"];

export type VectorHit = S["VectorHit"];
export type VectorPayload = S["VectorPayload"];
export type RecordKind = VectorPayload["kind"];

export type HealthResponse = S["HealthResponse"];
/** Mirrors backend `app.schemas.api.ErrorResponse` (rendered by the exception handler, so it is
 * not part of any route's OpenAPI response model). */
export interface ErrorResponse {
  error: { code: string; message: string; details?: Record<string, unknown> };
}
