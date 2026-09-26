"use client";

import { useMemo } from "react";

import { PageHeader } from "@/components/layout/PageHeader";
import { GrowthChart } from "@/components/updates/GrowthChart";
import { UpdateTimelineItem } from "@/components/updates/UpdateTimelineItem";
import { Card, CardHeader } from "@/components/ui/Card";
import { EmptyState } from "@/components/ui/EmptyState";
import { ErrorState } from "@/components/ui/ErrorState";
import { Skeleton } from "@/components/ui/Skeleton";
import { useGraph, usePapers, useTwinUpdates } from "@/lib/api/hooks";
import { displayTitle } from "@/lib/paper-status";
import { CHANGE_KINDS, CHANGE_STYLES } from "@/lib/updates";

export default function UpdatesPage() {
  const { data: updates, error, isLoading } = useTwinUpdates(200);
  const { data: graph } = useGraph({ limit: 3000 });
  const { data: papers } = usePapers();

  const nodes = useMemo(() => new Map((graph?.nodes ?? []).map((n) => [n.id, n])), [graph]);
  const paperTitles = useMemo(
    () => new Map((papers ?? []).map((p) => [p.paper_id, displayTitle(p)])),
    [papers],
  );

  return (
    <>
      <PageHeader
        eyebrow="Living twin"
        title="Twin Evolution"
        description="Each time a paper is merged, the twin records what changed: new knowledge added, existing knowledge strengthened by another paper, entries changed, and knowledge removed because no paper supports it any more."
      />
      {error && <ErrorState error={error} className="mb-6" />}
      {isLoading && <Skeleton className="h-64 rounded-2xl" />}
      {updates && updates.length === 0 && (
        <Card>
          <EmptyState
            title="No history yet"
            description="The first update appears when an extracted paper is merged into the twin."
          />
        </Card>
      )}
      {updates && updates.length > 0 && (
        <div className="space-y-8">
          <Card>
            <CardHeader
              eyebrow={`${updates.length} updates`}
              title="Growth of the twin"
              action={
                <ul className="flex flex-wrap gap-3 text-[11px] text-muted">
                  {CHANGE_KINDS.filter((k) => k !== "changed").map((k) => (
                    <li key={k} className="flex items-center gap-1.5">
                      <span className="size-2 rounded-sm" style={{ backgroundColor: CHANGE_STYLES[k].color }} />
                      {CHANGE_STYLES[k].label}
                    </li>
                  ))}
                  <li className="flex items-center gap-1.5">
                    <span className="h-px w-3 border-t border-dashed border-ink" /> Total entities
                  </li>
                </ul>
              }
            />
            <div className="px-6 pt-2 pb-5">
              <GrowthChart updates={updates} />
            </div>
          </Card>

          <ol className="relative space-y-4 before:absolute before:top-2 before:bottom-2 before:left-[16px] before:w-px before:bg-line">
            {updates.map((u) => (
              <UpdateTimelineItem key={u.id} update={u} nodes={nodes} paperTitles={paperTitles} />
            ))}
          </ol>
        </div>
      )}
    </>
  );
}
