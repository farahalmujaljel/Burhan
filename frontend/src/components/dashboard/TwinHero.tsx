"use client";

import { ArrowUpRight } from "lucide-react";
import Link from "next/link";

import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { EmptyState } from "@/components/ui/EmptyState";
import { Skeleton } from "@/components/ui/Skeleton";
import { useGraph } from "@/lib/api/hooks";
import type { TwinSummary } from "@/lib/api/types";
import { ENTITY_STYLES, GRAPH_TYPES } from "@/lib/entities";

import { TwinConstellation } from "./TwinConstellation";

const HERO_GRAPH_LIMIT = 400;

function domainPhrase(domain: string): string {
  return domain && domain !== "General" ? domain : "your research field";
}

export function TwinHero({ summary }: { summary?: TwinSummary }) {
  const graph = useGraph({ limit: HERO_GRAPH_LIMIT });
  const entities = summary
    ? Object.entries(summary.stats.entity_counts)
        .filter(([t]) => t !== "Paper")
        .reduce((sum, [, n]) => sum + n, 0)
    : 0;
  const evidence = summary
    ? summary.stats.verified_evidence + summary.stats.flagged_evidence + summary.unverified_evidence
    : 0;
  const empty = graph.data && graph.data.nodes.length === 0;

  return (
    <Card className="relative overflow-hidden animate-fade-up">
      <div className="grid min-h-[420px] grid-cols-1 lg:grid-cols-[minmax(0,5fr)_minmax(0,7fr)]">
        <div className="flex flex-col justify-between gap-8 p-8">
          <div>
            <p className="mb-3 text-[11px] font-medium tracking-[0.16em] text-brass uppercase">
              Research Digital Twin
            </p>
            <h1 className="font-display text-[2.6rem] leading-[1.05] tracking-tight text-ink">
              A living model of {summary ? domainPhrase(summary.domain) : "…"}
            </h1>
            <p className="mt-4 max-w-md text-[15px] leading-relaxed text-muted">
              Every paper Burhan reads adds verified methods, datasets, results, and claims to a
              shared knowledge graph. Each fact stays linked to the exact sentence it came from.
            </p>
          </div>

          <dl className="grid grid-cols-3 gap-4 border-t border-line pt-6">
            {[
              ["Papers", summary?.paper_count],
              ["Entities", summary ? entities : undefined],
              ["Evidence", summary ? evidence : undefined],
            ].map(([label, value]) => (
              <div key={label as string}>
                <dt className="text-[11px] tracking-wide text-faint uppercase">{label}</dt>
                <dd className="mt-1 font-display text-3xl text-ink tabular-nums">
                  {value ?? <Skeleton className="mt-2 h-7 w-12" />}
                </dd>
              </div>
            ))}
          </dl>
        </div>

        <div className="relative min-h-[360px] border-t border-line bg-dots lg:border-t-0 lg:border-l">
          {graph.isLoading && (
            <div className="absolute inset-0 flex items-center justify-center">
              <div className="size-40 rounded-full border border-dashed border-line-strong animate-pulse-soft" />
            </div>
          )}
          {empty && (
            <EmptyState
              className="h-full"
              title="The twin is waiting for its first paper"
              description="Upload research papers and run extraction. The twin grows with every paper."
              action={
                <Link href="/papers">
                  <Button variant="primary">Add papers</Button>
                </Link>
              }
            />
          )}
          {graph.data && !empty && (
            <>
              <div className="absolute inset-0 p-4">
                <TwinConstellation graph={graph.data} />
              </div>
              <Link
                href="/graph"
                className="absolute top-4 right-4 inline-flex items-center gap-1 rounded-full border border-line bg-paper/90 px-3 py-1.5 text-xs font-medium text-ink-2 shadow-card backdrop-blur hover:border-ink/30"
              >
                Explore graph <ArrowUpRight className="size-3.5" />
              </Link>
              <ul className="absolute bottom-4 left-4 flex flex-wrap gap-x-3 gap-y-1 rounded-xl bg-paper/85 px-3 py-2 backdrop-blur">
                {GRAPH_TYPES.map((t) => (
                  <li key={t} className="flex items-center gap-1.5 text-[11px] text-muted">
                    <span
                      className={t === "Paper" ? "size-2 rounded-[2px]" : "size-2 rounded-full"}
                      style={{ backgroundColor: ENTITY_STYLES[t].color }}
                    />
                    {ENTITY_STYLES[t].plural}
                  </li>
                ))}
              </ul>
            </>
          )}
        </div>
      </div>
    </Card>
  );
}
