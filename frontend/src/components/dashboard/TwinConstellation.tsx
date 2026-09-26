"use client";

import { useMemo } from "react";

import type { GraphView } from "@/lib/api/types";
import { ENTITY_STYLES } from "@/lib/entities";
import { layoutGraph, nodeDegrees } from "@/lib/graph-layout";

const PAD = 40;

/**
 * The live Research Digital Twin, drawn from the real knowledge graph: papers are hubs,
 * the methods, datasets, metrics, and claims they contribute orbit around them.
 */
export function TwinConstellation({ graph }: { graph: GraphView }) {
  const { nodes, edges, box, positions, degree } = useMemo(() => {
    const positions = layoutGraph(graph.nodes, graph.edges, { spacing: 0.8 });
    const xs = [...positions.values()].map((p) => p.x);
    const ys = [...positions.values()].map((p) => p.y);
    const box = {
      x: Math.min(...xs) - PAD,
      y: Math.min(...ys) - PAD,
      w: Math.max(...xs) - Math.min(...xs) + PAD * 2,
      h: Math.max(...ys) - Math.min(...ys) + PAD * 2,
    };
    return { nodes: graph.nodes, edges: graph.edges, box, positions, degree: nodeDegrees(graph.edges) };
  }, [graph]);

  return (
    <svg
      viewBox={`${box.x} ${box.y} ${Math.max(box.w, 200)} ${Math.max(box.h, 200)}`}
      className="h-full w-full"
      role="img"
      aria-label={`Research twin with ${nodes.length} entities and ${edges.length} relations`}
    >
      <g stroke="#0e0e10" strokeOpacity={0.12} strokeWidth={1}>
        {edges.map((e) => {
          const a = positions.get(e.source_id);
          const b = positions.get(e.target_id);
          if (!a || !b) return null;
          return <line key={e.id} x1={a.x} y1={a.y} x2={b.x} y2={b.y} />;
        })}
      </g>
      {nodes.map((n, i) => {
        const p = positions.get(n.id);
        if (!p) return null;
        const color = ENTITY_STYLES[n.type].color;
        const isPaper = n.type === "Paper";
        const shared = n.paper_ids && n.paper_ids.length > 1;
        const r = isPaper ? 11 : 4 + Math.min(degree.get(n.id) ?? 0, 5);
        return (
          <g key={n.id} transform={`translate(${p.x} ${p.y})`}>
            <title>{`${ENTITY_STYLES[n.type].label}: ${n.name}`}</title>
            {(isPaper || shared) && (
              <circle
                r={r + 7}
                fill="none"
                stroke={color}
                strokeOpacity={0.35}
                className="animate-pulse-soft"
                style={{ animationDelay: `${(i % 7) * 0.4}s` }}
              />
            )}
            {isPaper ? (
              <rect x={-r} y={-r} width={r * 2} height={r * 2} rx={3} fill={color} />
            ) : (
              <circle r={r} fill={color} fillOpacity={0.9} />
            )}
          </g>
        );
      })}
    </svg>
  );
}
