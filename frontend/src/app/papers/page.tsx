"use client";

import { PageHeader } from "@/components/layout/PageHeader";
import { PapersTable, PapersTableSkeleton } from "@/components/papers/PapersTable";
import { UploadDropzone } from "@/components/papers/UploadDropzone";
import { Card, CardHeader } from "@/components/ui/Card";
import { EmptyState } from "@/components/ui/EmptyState";
import { ErrorState } from "@/components/ui/ErrorState";
import { isExtracting, usePapers } from "@/lib/api/hooks";

export default function PapersPage() {
  const { data: papers, error, isLoading, mutate } = usePapers();
  const running = papers?.filter(isExtracting).length ?? 0;

  return (
    <>
      <PageHeader
        eyebrow="Ingestion"
        title="Papers"
        description="Upload papers from your field. Burhan parses each one into page-aware sections, then extracts and verifies its scientific knowledge before merging it into the twin."
      />
      <div className="space-y-8">
        <Card>
          <CardHeader eyebrow="Step 1" title="Add papers" />
          <div className="p-6">
            <UploadDropzone onUploaded={() => mutate()} />
          </div>
        </Card>

        <section className="min-w-0 space-y-3">
          <div className="flex items-baseline justify-between">
            <h2 className="font-display text-xl text-ink">
              Library {papers && <span className="text-muted">· {papers.length}</span>}
            </h2>
            {running > 0 && (
              <span className="text-xs text-brass">
                {running} extraction{running === 1 ? "" : "s"} in progress. This page refreshes automatically.
              </span>
            )}
          </div>
          {error && <ErrorState error={error} />}
          {isLoading && <PapersTableSkeleton />}
          {papers && papers.length === 0 && (
            <Card>
              <EmptyState
                title="No papers yet"
                description="Upload a few PDFs from one research area. The twin becomes more informative with each paper."
              />
            </Card>
          )}
          {papers && papers.length > 0 && (
            <PapersTable papers={[...papers].reverse()} onChange={() => mutate()} />
          )}
        </section>
      </div>
    </>
  );
}
