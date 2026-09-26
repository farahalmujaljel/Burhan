"use client";

import { useMemo, useState } from "react";

import { EvidenceResultCard } from "@/components/evidence/EvidenceResultCard";
import { SearchControls } from "@/components/evidence/SearchControls";
import { PageHeader } from "@/components/layout/PageHeader";
import { Card } from "@/components/ui/Card";
import { EmptyState } from "@/components/ui/EmptyState";
import { ErrorState } from "@/components/ui/ErrorState";
import { Skeleton } from "@/components/ui/Skeleton";
import { useEvidenceSearch, usePapers } from "@/lib/api/hooks";
import type { RecordKind } from "@/lib/api/types";
import { displayTitle } from "@/lib/paper-status";

const EXAMPLES = [
  "Which datasets were used for evaluation?",
  "What are the main limitations?",
  "How was the model regularized?",
  "What future work do the authors propose?",
];

export default function EvidencePage() {
  const [draft, setDraft] = useState("");
  const [query, setQuery] = useState("");
  const [kind, setKind] = useState<RecordKind>("evidence");
  const [paperId, setPaperId] = useState("");
  const { data: papers } = usePapers();
  const { data: hits, error, isLoading, isValidating } = useEvidenceSearch({
    q: query,
    kind,
    paperId: paperId || undefined,
    limit: 12,
  });
  const titles = useMemo(
    () => new Map((papers ?? []).map((p) => [p.paper_id, displayTitle(p)])),
    [papers],
  );
  const run = (q: string) => {
    setDraft(q);
    setQuery(q.trim());
  };

  return (
    <>
      <PageHeader
        eyebrow="Evidence retrieval"
        title="Evidence Search"
        description="Semantic search over every verified quote and passage in the twin, using a local embedding model. Each result shows the page, section, and verification status of its source."
      />
      <div className="mx-auto max-w-4xl space-y-6">
        <SearchControls
          draft={draft}
          onDraftChange={setDraft}
          onSubmit={() => run(draft)}
          kind={kind}
          onKindChange={setKind}
          paperId={paperId}
          onPaperChange={setPaperId}
          papers={papers ?? []}
        />

        {error && <ErrorState error={error} />}

        {!query && (
          <Card>
            <EmptyState
              title="Search what the field knows"
              description="Results are evidence quotes, not generated answers. Each one traces back to its source sentence."
              action={
                <div className="flex flex-wrap justify-center gap-2">
                  {EXAMPLES.map((q) => (
                    <button
                      key={q}
                      onClick={() => run(q)}
                      className="rounded-full border border-line bg-white px-3 py-1.5 text-xs text-ink-2 hover:border-ink/30"
                    >
                      {q}
                    </button>
                  ))}
                </div>
              }
            />
          </Card>
        )}

        {query && isLoading && (
          <div className="space-y-3">
            {Array.from({ length: 3 }, (_, i) => (
              <Skeleton key={i} className="h-36 rounded-2xl" />
            ))}
          </div>
        )}

        {query && hits && (
          <section aria-busy={isValidating} className={isValidating ? "opacity-60 transition-opacity" : ""}>
            <p className="mb-3 text-xs text-muted">
              {hits.length} result{hits.length === 1 ? "" : "s"} for “{query}”
            </p>
            {hits.length === 0 ? (
              <Card>
                <EmptyState
                  title="No matching evidence"
                  description="Try different wording, switch to paper passages, or extract more papers."
                />
              </Card>
            ) : (
              <div className="space-y-3">
                {hits.map((hit, i) => (
                  <EvidenceResultCard
                    key={`${hit.payload.evidence_id ?? hit.payload.chunk_id}-${i}`}
                    hit={hit}
                    rank={i + 1}
                    paperTitle={titles.get(hit.payload.paper_id)}
                  />
                ))}
              </div>
            )}
          </section>
        )}
      </div>
    </>
  );
}
