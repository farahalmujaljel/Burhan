"use client";

import { EntityStats } from "@/components/dashboard/EntityStats";
import { LatestUpdateCard } from "@/components/dashboard/LatestUpdateCard";
import { PipelineStrip } from "@/components/dashboard/PipelineStrip";
import { TopEntities } from "@/components/dashboard/TopEntities";
import { TwinHero } from "@/components/dashboard/TwinHero";
import { VerificationPanel } from "@/components/dashboard/VerificationPanel";
import { ErrorState } from "@/components/ui/ErrorState";
import { useTwinSummary } from "@/lib/api/hooks";

export default function DashboardPage() {
  const { data: summary, error, isLoading } = useTwinSummary();

  return (
    <div className="space-y-6">
      {error && <ErrorState error={error} />}
      <TwinHero summary={summary} />
      <EntityStats summary={summary} />
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        <VerificationPanel summary={summary} />
        <LatestUpdateCard update={summary?.last_update} loading={isLoading} />
        <TopEntities type="Method" items={summary?.top_methods} paperCount={summary?.paper_count ?? 0} />
      </div>
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        <TopEntities
          type="Dataset"
          items={summary?.top_datasets}
          paperCount={summary?.paper_count ?? 0}
        />
        <TopEntities type="Metric" items={summary?.top_metrics} paperCount={summary?.paper_count ?? 0} />
        <div className="flex flex-col justify-center rounded-2xl border border-dashed border-line-strong px-6 py-5">
          <p className="text-[11px] font-medium tracking-[0.14em] text-faint uppercase">How Burhan works</p>
          <p className="mt-2 text-sm leading-relaxed text-muted">
            Burhan is not a chat-with-PDF tool. It builds a structured, evidence-backed model of a
            research field, and each new paper refines it.
          </p>
        </div>
      </div>
      <PipelineStrip />
    </div>
  );
}
