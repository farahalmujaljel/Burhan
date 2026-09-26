"use client";

import { ReactFlowProvider } from "@xyflow/react";
import { useRouter, useSearchParams } from "next/navigation";
import { useMemo, useState } from "react";

import { PageHeader } from "@/components/layout/PageHeader";
import { Card } from "@/components/ui/Card";
import { EmptyState } from "@/components/ui/EmptyState";
import { ErrorState } from "@/components/ui/ErrorState";
import { useGraph, usePapers } from "@/lib/api/hooks";
import type { EntityType, GraphView } from "@/lib/api/types";
import { GRAPH_TYPES } from "@/lib/entities";
import { displayTitle } from "@/lib/paper-status";

import { GraphToolbar } from "./GraphToolbar";
import { KnowledgeGraphCanvas } from "./KnowledgeGraphCanvas";
import { NodeDetailPanel } from "./NodeDetailPanel";

const GRAPH_LIMIT = 3000;

export function KnowledgeGraphView() {
  const router = useRouter();
  const selectedId = useSearchParams().get("focus");
  const { data: graph, error, isLoading } = useGraph({ limit: GRAPH_LIMIT });
  const { data: papers } = usePapers();

  const [types, setTypes] = useState<Set<EntityType>>(() => new Set(GRAPH_TYPES));
  const [paperId, setPaperId] = useState("");
  const [query, setQuery] = useState("");

  const select = (id: string | null) =>
    router.replace(id ? `/graph?focus=${encodeURIComponent(id)}` : "/graph", { scroll: false });

  const counts = useMemo(() => {
    const c: Record<string, number> = {};
    for (const n of graph?.nodes ?? []) c[n.type] = (c[n.type] ?? 0) + 1;
    return c;
  }, [graph]);

  const visible: GraphView | null = useMemo(() => {
    if (!graph) return null;
    const nodes = graph.nodes.filter(
      (n) => types.has(n.type) && (!paperId || (n.paper_ids ?? []).includes(paperId)),
    );
    const ids = new Set(nodes.map((n) => n.id));
    return { nodes, edges: graph.edges.filter((e) => ids.has(e.source_id) && ids.has(e.target_id)) };
  }, [graph, types, paperId]);

  const matchIds = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (q.length < 2 || !visible) return null;
    return new Set(
      visible.nodes
        .filter((n) => [n.name, ...(n.aliases ?? [])].some((s) => s.toLowerCase().includes(q)))
        .map((n) => n.id),
    );
  }, [query, visible]);

  const paperTitles = useMemo(
    () => new Map((papers ?? []).map((p) => [p.paper_id, displayTitle(p)])),
    [papers],
  );
  const layoutKey = `${[...types].sort().join(",")}|${paperId}|${graph?.nodes.length}|${graph?.edges.length}`;

  return (
    <div className="flex h-[calc(100vh-5rem)] flex-col">
      <PageHeader
        eyebrow="Scientific Knowledge Graph"
        title="Knowledge Graph"
        description="Papers, the concepts they share, and the claims they make. Click any node to see its connections and the exact quotes that support it."
      />
      {error && <ErrorState error={error} className="mb-4" />}
      <Card className="relative flex min-h-0 flex-1 overflow-hidden">
        <div className="relative min-w-0 flex-1 bg-dots">
          <div className="absolute top-3 left-3 z-10 right-3">
            <GraphToolbar
              types={types}
              onToggleType={(t) =>
                setTypes((prev) => {
                  const next = new Set(prev);
                  if (next.has(t)) next.delete(t);
                  else next.add(t);
                  return next;
                })
              }
              counts={counts}
              papers={papers ?? []}
              paperId={paperId}
              onPaperChange={setPaperId}
              query={query}
              onQueryChange={setQuery}
            />
          </div>
          {isLoading && (
            <div className="flex h-full items-center justify-center">
              <div className="size-48 rounded-full border border-dashed border-line-strong animate-pulse-soft" />
            </div>
          )}
          {visible && visible.nodes.length === 0 && (
            <EmptyState
              className="h-full"
              title={graph?.nodes.length ? "Nothing matches these filters" : "The graph is empty"}
              description={
                graph?.nodes.length
                  ? "Re-enable some entity types or choose all papers."
                  : "Extract knowledge from a paper to build the first nodes."
              }
            />
          )}
          {visible && visible.nodes.length > 0 && (
            <ReactFlowProvider>
              <KnowledgeGraphCanvas
                key={layoutKey}
                graph={visible}
                selectedId={selectedId}
                matchIds={matchIds}
                onSelect={select}
              />
            </ReactFlowProvider>
          )}
        </div>
        {selectedId && (
          <NodeDetailPanel
            nodeId={selectedId}
            paperTitles={paperTitles}
            onSelect={select}
            onClose={() => select(null)}
          />
        )}
      </Card>
    </div>
  );
}
