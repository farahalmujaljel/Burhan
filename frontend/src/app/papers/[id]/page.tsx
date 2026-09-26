"use client";

import { ArrowLeft } from "lucide-react";
import Link from "next/link";
import { use } from "react";

import { PageHeader } from "@/components/layout/PageHeader";
import { ApplyToTwinButton } from "@/components/papers/ApplyToTwinButton";
import { DocumentOutline } from "@/components/papers/DocumentOutline";
import { ExtractButton } from "@/components/papers/ExtractButton";
import { ExtractionReport } from "@/components/papers/ExtractionReport";
import { KnowledgePanel } from "@/components/papers/KnowledgePanel";
import { PipelineStepper } from "@/components/papers/PipelineSteps";
import { Card } from "@/components/ui/Card";
import { EmptyState } from "@/components/ui/EmptyState";
import { ErrorState } from "@/components/ui/ErrorState";
import { Skeleton, SkeletonLines } from "@/components/ui/Skeleton";
import { usePaper, usePaperDocument, usePaperKnowledge } from "@/lib/api/hooks";
import { formatBytes, timeAgo } from "@/lib/format";
import { displayTitle } from "@/lib/paper-status";

export default function PaperDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const paper = usePaper(id);
  const p = paper.data;
  const doc = usePaperDocument(id, p?.status === "parsed");
  const knowledge = usePaperKnowledge(id, p?.extraction_status === "completed");

  return (
    <>
      <Link href="/papers" className="mb-6 inline-flex items-center gap-1.5 text-sm text-muted hover:text-ink">
        <ArrowLeft className="size-4" /> All papers
      </Link>

      {paper.error && <ErrorState error={paper.error} />}
      {!p && !paper.error && (
        <div className="space-y-4">
          <Skeleton className="h-10 w-2/3" />
          <Skeleton className="h-24 w-full" />
        </div>
      )}

      {p && (
        <>
          <PageHeader
            eyebrow="Paper"
            title={displayTitle(p)}
            description={`${p.file_name} · ${formatBytes(p.size_bytes)} · added ${timeAgo(p.created_at)}`}
            actions={
              <>
                {p.extraction_status === "completed" && (
                  <ApplyToTwinButton paperId={id} onDone={() => paper.mutate()} />
                )}
                <ExtractButton paper={p} size="md" onStarted={(u) => paper.mutate(u, false)} />
              </>
            }
          />

          <Card className="mb-6 px-6 py-5">
            <PipelineStepper paper={p} />
          </Card>

          <div className="grid grid-cols-1 gap-6 xl:grid-cols-[minmax(0,1fr)_340px]">
            <div className="min-w-0">
              {p.extraction_status === "completed" ? (
                knowledge.error ? (
                  <ErrorState error={knowledge.error} />
                ) : knowledge.data ? (
                  <KnowledgePanel knowledge={knowledge.data} />
                ) : (
                  <Card className="p-6">
                    <SkeletonLines lines={8} />
                  </Card>
                )
              ) : (
                <Card>
                  <EmptyState
                    title={
                      p.extraction_status === "running"
                        ? "Burhan is reading this paper"
                        : p.status === "failed"
                          ? "This PDF could not be parsed"
                          : "Knowledge not extracted yet"
                    }
                    description={
                      p.extraction_status === "running"
                        ? "Extracting methods, datasets, results, and claims, then verifying each quote against the source. This usually takes 2–3 minutes."
                        : p.status === "failed"
                          ? p.error
                          : "Run extraction to turn this paper into verified, structured knowledge."
                    }
                  />
                </Card>
              )}
            </div>
            <aside className="space-y-6">
              {p.status === "parsed" && <DocumentOutline doc={doc.data} />}
              {knowledge.data && <ExtractionReport meta={knowledge.data.meta} />}
            </aside>
          </div>
        </>
      )}
    </>
  );
}
