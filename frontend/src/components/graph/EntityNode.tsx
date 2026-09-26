"use client";

import { Handle, type Node, type NodeProps, Position } from "@xyflow/react";
import { memo } from "react";

import { cn } from "@/components/ui/cn";
import { Diamond } from "@/components/ui/Motifs";
import type { GraphNode } from "@/lib/api/types";
import { CLAIM_TYPES, ENTITY_STYLES } from "@/lib/entities";

export type EntityNodeData = {
  node: GraphNode;
  dimmed: boolean;
  highlighted: boolean;
};
export type EntityFlowNode = Node<EntityNodeData, "entity">;

// Invisible, centred handles: edges meet at the node centre for an organic network look.
const HANDLE = "!pointer-events-none !top-1/2 !left-1/2 !size-px !min-w-0 !border-0 !bg-transparent !opacity-0";

function EntityNodeView({ data, selected }: NodeProps<EntityFlowNode>) {
  const { node, dimmed, highlighted } = data;
  const style = ENTITY_STYLES[node.type];
  const Icon = style.icon;
  const papers = node.paper_ids?.length ?? 0;
  const ring = selected || highlighted;

  const frame = cn(
    "relative transition-all duration-300",
    dimmed && "opacity-20 saturate-50",
    ring && "scale-[1.04]",
  );

  let body: React.ReactNode;
  if (node.type === "Paper") {
    body = (
      <div
        className={cn(
          "w-56 rounded-xl bg-ink px-3.5 py-3 text-paper shadow-lift",
          ring && "ring-2 ring-brass ring-offset-2 ring-offset-paper",
        )}
      >
        <div className="mb-1 flex items-center gap-1.5 text-[10px] tracking-[0.14em] text-paper/60 uppercase">
          <Icon className="size-3" /> Paper
        </div>
        <p className="line-clamp-2 font-display text-[15px] leading-snug">{node.name}</p>
      </div>
    );
  } else if (CLAIM_TYPES.includes(node.type)) {
    body = (
      <div
        className={cn(
          "w-52 rounded-lg border bg-white px-3 py-2 shadow-card",
          ring ? "border-ink" : "border-line",
        )}
        style={{ borderTop: `3px solid ${style.color}` }}
      >
        <div className="mb-1 flex items-center gap-1.5 text-[10px] font-medium tracking-wide uppercase" style={{ color: style.color }}>
          <Diamond size={6} /> {style.label}
        </div>
        <p className="line-clamp-3 text-[12px] leading-snug text-ink-2">{node.name}</p>
      </div>
    );
  } else {
    body = (
      <div
        className={cn(
          "flex max-w-60 items-center gap-2 rounded-full border bg-white py-1.5 pr-3.5 pl-1.5 shadow-card",
          ring ? "border-ink" : "border-line",
        )}
      >
        <span
          className="flex size-6 shrink-0 items-center justify-center rounded-full"
          style={{ backgroundColor: `${style.color}1a`, color: style.color }}
        >
          <Icon className="size-3.5" />
        </span>
        <span className="truncate text-[13px] font-medium text-ink">{node.name}</span>
        {papers > 1 && (
          <span
            title={`Shared by ${papers} papers`}
            className="shrink-0 rounded-full px-1.5 font-mono text-[10px] text-paper"
            style={{ backgroundColor: style.color }}
          >
            {papers}
          </span>
        )}
      </div>
    );
  }

  return (
    <div className={frame}>
      <Handle type="target" position={Position.Top} className={HANDLE} isConnectable={false} />
      {body}
      <Handle type="source" position={Position.Bottom} className={HANDLE} isConnectable={false} />
    </div>
  );
}

export const EntityNode = memo(EntityNodeView);
