"use client";

import "@xyflow/react/dist/style.css";

import {
  applyNodeChanges,
  Background,
  BackgroundVariant,
  Controls,
  MiniMap,
  type NodeChange,
  ReactFlow,
} from "@xyflow/react";
import { useMemo, useState } from "react";

import type { GraphView } from "@/lib/api/types";
import { ENTITY_STYLES } from "@/lib/entities";

import { buildEdge, buildNodes } from "./build-flow";
import { EntityNode, type EntityFlowNode } from "./EntityNode";

const NODE_TYPES = { entity: EntityNode };

/**
 * Interactive knowledge graph. Mount with a `key` that changes when the graph data changes:
 * node positions are local state (so nodes stay draggable) seeded from the force layout.
 */
export function KnowledgeGraphCanvas({
  graph,
  selectedId,
  matchIds,
  onSelect,
}: {
  graph: GraphView;
  selectedId: string | null;
  matchIds: Set<string> | null;
  onSelect: (id: string | null) => void;
}) {
  const [nodes, setNodes] = useState<EntityFlowNode[]>(() => buildNodes(graph));

  const neighborIds = useMemo(() => {
    if (!selectedId) return null;
    const ids = new Set([selectedId]);
    for (const e of graph.edges) {
      if (e.source_id === selectedId) ids.add(e.target_id);
      if (e.target_id === selectedId) ids.add(e.source_id);
    }
    return ids;
  }, [graph.edges, selectedId]);

  const focus = neighborIds ?? matchIds;
  const displayNodes = useMemo(
    () =>
      nodes.map((n) => ({
        ...n,
        selected: n.id === selectedId,
        data: {
          ...n.data,
          dimmed: !!focus && !focus.has(n.id),
          highlighted: !!matchIds && matchIds.has(n.id),
        },
      })),
    [nodes, focus, matchIds, selectedId],
  );

  const edges = useMemo(
    () =>
      graph.edges.map((e) => {
        const touches = selectedId && (e.source_id === selectedId || e.target_id === selectedId);
        return buildEdge(e, touches ? "active" : focus ? "dimmed" : "normal");
      }),
    [graph.edges, selectedId, focus],
  );

  return (
    <ReactFlow
      nodes={displayNodes}
      edges={edges}
      nodeTypes={NODE_TYPES}
      onNodesChange={(changes: NodeChange<EntityFlowNode>[]) =>
        setNodes((ns) => applyNodeChanges(changes, ns))
      }
      onNodeClick={(_, node) => onSelect(node.id)}
      onPaneClick={() => onSelect(null)}
      nodesConnectable={false}
      edgesFocusable={false}
      fitView
      fitViewOptions={{ padding: 0.15 }}
      minZoom={0.1}
      maxZoom={2}
      proOptions={{ hideAttribution: true }}
    >
      <Background variant={BackgroundVariant.Dots} gap={18} size={1} color="#d8d2c6" />
      <Controls showInteractive={false} position="bottom-left" />
      <MiniMap
        pannable
        zoomable
        position="bottom-right"
        nodeColor={(n) => ENTITY_STYLES[(n as EntityFlowNode).data.node.type].color}
        nodeStrokeWidth={0}
        maskColor="rgb(250 249 246 / 0.75)"
        style={{ width: 160, height: 110 }}
      />
    </ReactFlow>
  );
}
