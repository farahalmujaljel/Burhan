"use client";

import { Search } from "lucide-react";

import { cn } from "@/components/ui/cn";
import type { EntityType, PaperRecord } from "@/lib/api/types";
import { ENTITY_STYLES, GRAPH_TYPES } from "@/lib/entities";
import { displayTitle } from "@/lib/paper-status";

export function GraphToolbar({
  types,
  onToggleType,
  counts,
  papers,
  paperId,
  onPaperChange,
  query,
  onQueryChange,
}: {
  types: Set<EntityType>;
  onToggleType: (t: EntityType) => void;
  counts: Record<string, number>;
  papers: PaperRecord[];
  paperId: string;
  onPaperChange: (id: string) => void;
  query: string;
  onQueryChange: (q: string) => void;
}) {
  return (
    <div className="flex flex-wrap items-center gap-2 rounded-2xl border border-line bg-paper/90 p-2 shadow-card backdrop-blur">
      <label className="flex h-8 items-center gap-2 rounded-lg border border-line bg-white px-2.5">
        <Search className="size-3.5 text-faint" />
        <input
          value={query}
          onChange={(e) => onQueryChange(e.target.value)}
          placeholder="Find an entity…"
          className="w-40 bg-transparent text-sm outline-none placeholder:text-faint"
        />
      </label>
      <select
        value={paperId}
        onChange={(e) => onPaperChange(e.target.value)}
        className="h-8 max-w-56 rounded-lg border border-line bg-white px-2 text-sm text-ink-2 outline-none"
        aria-label="Filter by paper"
      >
        <option value="">All papers</option>
        {papers.map((p) => (
          <option key={p.paper_id} value={p.paper_id}>
            {displayTitle(p)}
          </option>
        ))}
      </select>
      <span className="mx-1 h-5 w-px bg-line" />
      {GRAPH_TYPES.map((t) => {
        const on = types.has(t);
        const s = ENTITY_STYLES[t];
        return (
          <button
            key={t}
            type="button"
            onClick={() => onToggleType(t)}
            aria-pressed={on}
            className={cn(
              "flex h-8 items-center gap-1.5 rounded-lg border px-2.5 text-xs transition-colors",
              on ? "border-line-strong bg-white text-ink" : "border-transparent text-faint line-through",
            )}
          >
            <span
              className={t === "Paper" ? "size-2 rounded-[2px]" : "size-2 rounded-full"}
              style={{ backgroundColor: on ? s.color : "#cfc8bb" }}
            />
            {s.plural}
            <span className="font-mono text-[10px] text-faint">{counts[t] ?? 0}</span>
          </button>
        );
      })}
    </div>
  );
}
