"use client";

import { Search } from "lucide-react";

import { cn } from "@/components/ui/cn";
import type { PaperRecord, RecordKind } from "@/lib/api/types";
import { displayTitle } from "@/lib/paper-status";

const KINDS: { value: RecordKind; label: string; hint: string }[] = [
  { value: "evidence", label: "Verified evidence", hint: "Quotes linked to extracted claims" },
  { value: "chunk", label: "Paper passages", hint: "Any section of the parsed text" },
];

export function SearchControls({
  draft,
  onDraftChange,
  onSubmit,
  kind,
  onKindChange,
  paperId,
  onPaperChange,
  papers,
}: {
  draft: string;
  onDraftChange: (q: string) => void;
  onSubmit: () => void;
  kind: RecordKind;
  onKindChange: (k: RecordKind) => void;
  paperId: string;
  onPaperChange: (id: string) => void;
  papers: PaperRecord[];
}) {
  return (
    <div className="space-y-3">
      <form
        onSubmit={(e) => {
          e.preventDefault();
          onSubmit();
        }}
        className="flex items-center gap-3 rounded-2xl border border-line-strong bg-white px-5 py-3.5 shadow-card focus-within:border-ink/40"
      >
        <Search className="size-5 text-muted" />
        <input
          value={draft}
          onChange={(e) => onDraftChange(e.target.value)}
          placeholder="Ask about the field, e.g. “which optimizer was used for training?”"
          className="flex-1 bg-transparent font-display text-lg outline-none placeholder:font-sans placeholder:text-base placeholder:text-faint"
          aria-label="Search evidence"
        />
        <kbd className="hidden rounded border border-line px-1.5 font-mono text-[10px] text-faint sm:block">↵</kbd>
      </form>
      <div className="flex flex-wrap items-center gap-2">
        {KINDS.map((k) => (
          <button
            key={k.value}
            type="button"
            title={k.hint}
            onClick={() => onKindChange(k.value)}
            className={cn(
              "h-8 rounded-lg border px-3 text-xs transition-colors",
              kind === k.value ? "border-ink bg-ink text-paper" : "border-line bg-white text-ink-2 hover:border-ink/30",
            )}
          >
            {k.label}
          </button>
        ))}
        <select
          value={paperId}
          onChange={(e) => onPaperChange(e.target.value)}
          className="h-8 max-w-72 rounded-lg border border-line bg-white px-2 text-xs text-ink-2 outline-none"
          aria-label="Filter by paper"
        >
          <option value="">All papers</option>
          {papers.map((p) => (
            <option key={p.paper_id} value={p.paper_id}>
              {displayTitle(p)}
            </option>
          ))}
        </select>
      </div>
    </div>
  );
}
