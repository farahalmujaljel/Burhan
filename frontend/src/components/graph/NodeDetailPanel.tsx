"use client";

import { X } from "lucide-react";

import { EvidenceQuote } from "@/components/evidence/EvidenceQuote";
import { EntityBadge } from "@/components/ui/Badges";
import { ErrorState } from "@/components/ui/ErrorState";
import { SkeletonLines } from "@/components/ui/Skeleton";
import { useNodeDetail } from "@/lib/api/hooks";
import type { GraphEdge, GraphNode } from "@/lib/api/types";
import { ENTITY_STYLES, RELATION_LABELS } from "@/lib/entities";

interface Connection {
  edge: GraphEdge;
  other: GraphNode;
  outgoing: boolean;
}

export function NodeDetailPanel({
  nodeId,
  paperTitles,
  onSelect,
  onClose,
}: {
  nodeId: string;
  paperTitles: Map<string, string>;
  onSelect: (id: string) => void;
  onClose: () => void;
}) {
  const { data, error, isLoading } = useNodeDetail(nodeId);
  const neighbors = new Map((data?.neighbors ?? []).map((n) => [n.id, n]));

  const connections = (data?.edges ?? [])
    .map((e) => {
      const outgoing = e.source_id === nodeId;
      const other = neighbors.get(outgoing ? e.target_id : e.source_id);
      return other ? { edge: e, other, outgoing } : null;
    })
    .filter((c): c is Connection => c !== null);

  return (
    <aside className="flex h-full w-[400px] shrink-0 flex-col border-l border-line bg-paper animate-fade-up">
      <div className="flex items-start justify-between gap-3 border-b border-line px-5 py-4">
        {data ? (
          <div className="min-w-0">
            <EntityBadge type={data.node.type} />
            <h2 className="mt-2 font-display text-xl leading-snug text-ink">{data.node.name}</h2>
            {(data.node.aliases?.length ?? 0) > 0 && (
              <p className="mt-1 text-xs text-muted">Also called: {data.node.aliases!.join(" · ")}</p>
            )}
          </div>
        ) : (
          <div className="w-full">
            <SkeletonLines lines={2} />
          </div>
        )}
        <button onClick={onClose} aria-label="Close details" className="rounded-md p-1 text-faint hover:bg-paper-2 hover:text-ink">
          <X className="size-4" />
        </button>
      </div>

      <div className="flex-1 space-y-6 overflow-y-auto px-5 py-5">
        {error && <ErrorState error={error} />}
        {isLoading && <SkeletonLines lines={6} />}
        {data && (
          <>
            {data.node.description && <p className="text-sm text-ink-2">{data.node.description}</p>}

            <section>
              <h3 className="mb-2 text-[11px] font-medium tracking-wide text-faint uppercase">
                Supported by {data.node.paper_ids?.length ?? 0} paper{data.node.paper_ids?.length === 1 ? "" : "s"}
              </h3>
              <ul className="space-y-1">
                {(data.node.paper_ids ?? []).map((pid) => (
                  <li key={pid}>
                    <button onClick={() => onSelect(pid)} className="text-left text-sm text-ink hover:underline">
                      {paperTitles.get(pid) ?? pid}
                    </button>
                  </li>
                ))}
              </ul>
            </section>

            <section>
              <h3 className="mb-2 text-[11px] font-medium tracking-wide text-faint uppercase">
                Connected entities · {connections.length}
              </h3>
              <ul className="space-y-1">
                {connections.map(({ edge, other, outgoing }) => (
                  <li key={edge.id}>
                    <button
                      onClick={() => onSelect(other.id)}
                      className="flex w-full items-center gap-2 rounded-lg px-2 py-1.5 text-left hover:bg-paper-2"
                    >
                      <span className="size-2 shrink-0 rounded-full" style={{ backgroundColor: ENTITY_STYLES[other.type].color }} />
                      <span className="shrink-0 font-mono text-[10px] text-faint">
                        {outgoing ? "" : "← "}
                        {RELATION_LABELS[edge.type] ?? edge.type}
                        {edge.type === "REPORTS" && edge.properties?.value != null ? ` ${edge.properties.value}` : ""}
                      </span>
                      <span className="truncate text-sm text-ink">{other.name}</span>
                    </button>
                  </li>
                ))}
              </ul>
            </section>

            <section>
              <h3 className="mb-3 text-[11px] font-medium tracking-wide text-faint uppercase">
                Supporting evidence · {data.evidence.length}
              </h3>
              {data.evidence.length === 0 ? (
                <p className="text-sm text-faint">No direct quotes for this entity.</p>
              ) : (
                <div className="space-y-4">
                  {data.evidence.map((ev) => (
                    <EvidenceQuote
                      key={ev.id}
                      source={{ ...ev, page: ev.span?.page, paperTitle: paperTitles.get(ev.paper_id) }}
                    />
                  ))}
                </div>
              )}
            </section>
          </>
        )}
      </div>
    </aside>
  );
}
