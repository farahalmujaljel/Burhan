import { type Edge, MarkerType } from "@xyflow/react";

import type { GraphEdge, GraphView } from "@/lib/api/types";
import { layoutGraph } from "@/lib/graph-layout";

import type { EntityFlowNode } from "./EntityNode";

// Approximate rendered sizes, so layout coordinates (centres) become React Flow top-left positions.
const SIZE: Record<string, [number, number]> = {
  Paper: [224, 72],
  Finding: [208, 84],
  Limitation: [208, 84],
  FutureWork: [208, 84],
};
const DEFAULT_SIZE: [number, number] = [170, 36];

export function buildNodes(graph: GraphView): EntityFlowNode[] {
  const positions = layoutGraph(graph.nodes, graph.edges, { spacing: 1.7 });
  return graph.nodes.map((node) => {
    const p = positions.get(node.id) ?? { x: 0, y: 0 };
    const [w, h] = SIZE[node.type] ?? DEFAULT_SIZE;
    return {
      id: node.id,
      type: "entity",
      position: { x: p.x - w / 2, y: p.y - h / 2 },
      data: { node, dimmed: false, highlighted: false },
    };
  });
}

export function buildEdge(edge: GraphEdge, state: "normal" | "active" | "dimmed"): Edge {
  const active = state === "active";
  return {
    id: edge.id,
    source: edge.source_id,
    target: edge.target_id,
    type: "straight",
    label: active ? edge.type.toLowerCase() : undefined,
    labelStyle: { fontSize: 10, fill: "#6f6b64", fontFamily: "var(--font-mono)" },
    labelBgStyle: { fill: "#faf9f6" },
    style: {
      stroke: "#0e0e10",
      strokeOpacity: active ? 0.7 : state === "dimmed" ? 0.05 : 0.16,
      strokeWidth: active ? 1.6 : 1,
    },
    markerEnd: active ? { type: MarkerType.ArrowClosed, width: 14, height: 14, color: "#0e0e10" } : undefined,
    zIndex: active ? 1 : 0,
  };
}
