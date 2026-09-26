"use client";

import { Sparkles } from "lucide-react";
import { useState } from "react";

import { Button } from "@/components/ui/Button";
import { api } from "@/lib/api/endpoints";
import type { PaperRecord } from "@/lib/api/types";
import { canExtract } from "@/lib/paper-status";

/** Starts background extraction; the caller's SWR hook polls until it finishes. */
export function ExtractButton({
  paper,
  onStarted,
  size = "sm",
}: {
  paper: PaperRecord;
  onStarted: (updated: PaperRecord) => void;
  size?: "sm" | "md";
}) {
  const [pending, setPending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const running = paper.extraction_status === "running";
  const done = paper.extraction_status === "completed";

  const start = async () => {
    setPending(true);
    setError(null);
    try {
      onStarted(await api.papers.extract(paper.paper_id));
    } catch (e) {
      setError(e instanceof Error ? e.message : "Could not start extraction");
    } finally {
      setPending(false);
    }
  };

  return (
    <span className="inline-flex flex-col items-end gap-1">
      <Button
        variant={done ? "ghost" : "primary"}
        className={size === "sm" ? "h-8 px-3 text-xs" : undefined}
        icon={<Sparkles className="size-3.5" />}
        loading={pending || running}
        disabled={!canExtract(paper)}
        onClick={start}
      >
        {running ? "Extracting…" : done ? "Re-extract" : "Extract knowledge"}
      </Button>
      {error && <span className="max-w-64 text-right text-[11px] text-flagged">{error}</span>}
    </span>
  );
}
