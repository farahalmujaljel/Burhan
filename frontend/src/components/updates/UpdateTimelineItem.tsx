"use client";

import { ChevronDown, GitMerge, ScanSearch } from "lucide-react";
import { useState } from "react";

import { cn } from "@/components/ui/cn";
import { Diamond } from "@/components/ui/Motifs";
import type { GraphNode, TwinUpdate } from "@/lib/api/types";
import { ENTITY_STYLES } from "@/lib/entities";
import { formatDateTime, timeAgo } from "@/lib/format";
import { CHANGE_KINDS, CHANGE_STYLES, entityIds, isNoop, relationIds } from "@/lib/updates";

import { ChangeChips } from "./ChangeChips";

export function UpdateTimelineItem({
  update,
  nodes,
  paperTitles,
}: {
  update: TwinUpdate;
  nodes: Map<string, GraphNode>;
  paperTitles: Map<string, string>;
}) {
  const noop = isNoop(update);
  const [open, setOpen] = useState(false);
  const papers = (update.paper_ids ?? []).map((id) => paperTitles.get(id) ?? id);

  return (
    <li className="relative pl-10">
      <span className="absolute top-1.5 left-[11px] flex size-3 items-center justify-center">
        <Diamond size={12} className={noop ? "text-line-strong" : update.operation === "remove" ? "text-flagged" : "text-ink"} />
      </span>
      <div className={cn("rounded-2xl border bg-white/70 px-5 py-4 shadow-card", noop ? "border-line/70" : "border-line")}>
        <div className="flex flex-wrap items-center gap-x-3 gap-y-1 text-xs text-muted">
          <span title={formatDateTime(update.created_at)}>{timeAgo(update.created_at)}</span>
          <span className="rounded-full bg-paper-2 px-2 py-0.5 text-[11px]">
            {update.operation === "remove" ? "Paper removed" : "Paper merged"}
          </span>
          <span className="truncate font-medium text-ink-2">{papers.join(", ")}</span>
        </div>
        <p className={cn("mt-2 font-display text-lg leading-snug", noop ? "text-muted" : "text-ink")}>{update.summary}</p>
        {!noop && (
          <div className="mt-3 flex flex-wrap items-center justify-between gap-3">
            <ChangeChips update={update} />
            <button
              onClick={() => setOpen((o) => !o)}
              className="inline-flex items-center gap-1 text-xs text-muted hover:text-ink"
              aria-expanded={open}
            >
              Details <ChevronDown className={cn("size-3.5 transition-transform", open && "rotate-180")} />
            </button>
          </div>
        )}

        {open && (
          <div className="mt-4 space-y-4 border-t border-line pt-4 animate-fade-up">
            <div className="grid gap-4 md:grid-cols-4">
              {CHANGE_KINDS.map((kind) => {
                const ids = entityIds(update, kind);
                const rels = relationIds(update, kind).length;
                const s = CHANGE_STYLES[kind];
                return (
                  <div key={kind}>
                    <p className="mb-2 text-[11px] font-medium tracking-wide uppercase" style={{ color: s.color }}>
                      {s.label} <span className="text-faint normal-case">· {ids.length} entities, {rels} relations</span>
                    </p>
                    <ul className="space-y-1">
                      {ids.slice(0, 12).map((id) => {
                        const n = nodes.get(id);
                        return (
                          <li key={id} className="flex items-center gap-1.5 text-xs">
                            <span
                              className="size-1.5 shrink-0 rounded-full"
                              style={{ backgroundColor: n ? ENTITY_STYLES[n.type].color : "#cfc8bb" }}
                            />
                            <span className={cn("truncate", n ? "text-ink-2" : "font-mono text-faint")}>
                              {n?.name ?? id}
                            </span>
                          </li>
                        );
                      })}
                      {ids.length > 12 && <li className="text-xs text-faint">+{ids.length - 12} more</li>}
                    </ul>
                  </div>
                );
              })}
            </div>
            {(update.resolutions?.length ?? 0) > 0 && (
              <div>
                <p className="mb-1.5 flex items-center gap-1.5 text-[11px] font-medium tracking-wide text-brass uppercase">
                  <GitMerge className="size-3.5" /> Entity resolution
                </p>
                <ul className="flex flex-wrap gap-1.5">
                  {update.resolutions!.map((r) => (
                    <li key={`${r.original_name}-${r.canonical_id}`} className="rounded-lg bg-brass-soft/60 px-2 py-1 text-xs text-ink-2" title={`${r.method} match · confidence ${r.confidence}`}>
                      “{r.original_name}” → <span className="font-medium">{r.canonical_name}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}
            {(update.possible_duplicates?.length ?? 0) > 0 && (
              <p className="flex items-start gap-1.5 text-xs text-muted">
                <ScanSearch className="mt-0.5 size-3.5 shrink-0" />
                Possible duplicates kept separate for review:{" "}
                {update.possible_duplicates!.map((d) => `“${d.name}” ~ “${d.candidate_name}”`).join(", ")}
              </p>
            )}
            <p className="text-[11px] text-faint">
              Indexed {update.evidence_indexed ?? 0} evidence quotes and {update.chunks_indexed ?? 0} passages for search.
            </p>
          </div>
        )}
      </div>
    </li>
  );
}
