import {
  forceCollide,
  forceLink,
  forceManyBody,
  forceSimulation,
  forceX,
  forceY,
  type SimulationLinkDatum,
  type SimulationNodeDatum,
} from "d3-force";

import type { GraphEdge, GraphNode } from "@/lib/api/types";

export interface Positioned {
  x: number;
  y: number;
}

interface SimNode extends SimulationNodeDatum {
  id: string;
  weight: number;
  radius: number;
}

// Collision radius per node type, in layout units (claims render as wide cards).
const RADIUS: Partial<Record<GraphNode["type"], number>> = {
  Paper: 70,
  Finding: 64,
  Limitation: 64,
  FutureWork: 64,
};
const DEFAULT_RADIUS = 44;

/**
 * Deterministic force-directed layout (d3 seeds nodes on a phyllotaxis spiral, so the same
 * graph always lays out the same way). Papers act as heavy hubs their entities orbit around.
 */
export function layoutGraph(
  nodes: GraphNode[],
  edges: GraphEdge[],
  { spacing = 1, iterations = 300 }: { spacing?: number; iterations?: number } = {},
): Map<string, Positioned> {
  const degree = nodeDegrees(edges);
  const simNodes: SimNode[] = nodes.map((n) => ({
    id: n.id,
    weight: n.type === "Paper" ? 3 : 1 + Math.min(degree.get(n.id) ?? 0, 6) / 3,
    radius: (RADIUS[n.type] ?? DEFAULT_RADIUS) * spacing,
  }));
  const ids = new Set(simNodes.map((n) => n.id));
  const links: SimulationLinkDatum<SimNode>[] = edges
    .filter((e) => ids.has(e.source_id) && ids.has(e.target_id))
    .map((e) => ({ source: e.source_id, target: e.target_id }));

  const sim = forceSimulation(simNodes)
    .force(
      "link",
      forceLink<SimNode, SimulationLinkDatum<SimNode>>(links)
        .id((d) => d.id)
        .distance(90 * spacing)
        .strength(0.6),
    )
    .force("charge", forceManyBody<SimNode>().strength((d) => -260 * spacing * d.weight))
    .force("collide", forceCollide<SimNode>().radius((d) => d.radius).strength(0.9))
    // Unconnected nodes (e.g. a metric with no reported result) are pulled in harder so they
    // stay near the cluster instead of drifting to the edge.
    .force("x", forceX<SimNode>(0).strength((d) => (degree.get(d.id) ? 0.04 : 0.3)))
    .force("y", forceY<SimNode>(0).strength((d) => (degree.get(d.id) ? 0.06 : 0.3)))
    .stop();

  for (let i = 0; i < iterations; i++) sim.tick();
  return new Map(simNodes.map((n) => [n.id, { x: n.x ?? 0, y: n.y ?? 0 }]));
}

export function nodeDegrees(edges: GraphEdge[]): Map<string, number> {
  const degree = new Map<string, number>();
  for (const e of edges) {
    degree.set(e.source_id, (degree.get(e.source_id) ?? 0) + 1);
    degree.set(e.target_id, (degree.get(e.target_id) ?? 0) + 1);
  }
  return degree;
}
