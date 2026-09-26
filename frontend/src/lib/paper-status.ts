import type { PaperRecord } from "@/lib/api/types";

export type StepState = "done" | "active" | "failed" | "pending";

export interface PipelineStep {
  key: "uploaded" | "parsed" | "extracted" | "twin";
  label: string;
  state: StepState;
  detail?: string;
}

/** Derive the paper's position in Burhan's pipeline from its ingestion record. */
export function pipelineSteps(p: PaperRecord): PipelineStep[] {
  const parsed: StepState =
    p.status === "parsed" ? "done" : p.status === "failed" ? "failed" : "active";
  const extracted: StepState =
    p.extraction_status === "completed"
      ? "done"
      : p.extraction_status === "failed"
        ? "failed"
        : p.extraction_status === "running"
          ? "active"
          : "pending";
  const twin: StepState = p.twin_updated_at
    ? "done"
    : p.twin_error
      ? "failed"
      : extracted === "done"
        ? "active"
        : "pending";

  return [
    { key: "uploaded", label: "Uploaded", state: "done" },
    {
      key: "parsed",
      label: "Parsed",
      state: parsed,
      detail: p.status === "parsed" ? `${p.page_count} pages · ${p.section_count} sections` : p.error ?? undefined,
    },
    {
      key: "extracted",
      label: "Extracted & verified",
      state: extracted,
      detail:
        extracted === "active"
          ? "Reading with the LLM… (2–3 min)"
          : extracted === "failed"
            ? p.extraction_error ?? "Extraction failed"
            : undefined,
    },
    {
      key: "twin",
      label: "In the twin",
      state: twin,
      detail: twin === "failed" ? p.twin_error ?? "Twin update failed" : undefined,
    },
  ];
}

export function canExtract(p: PaperRecord): boolean {
  return p.status === "parsed" && p.extraction_status !== "running";
}

export function displayTitle(p: Pick<PaperRecord, "title" | "file_name">): string {
  return p.title?.trim() || p.file_name;
}
