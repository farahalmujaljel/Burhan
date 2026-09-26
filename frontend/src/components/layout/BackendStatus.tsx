"use client";

import { cn } from "@/components/ui/cn";
import { useHealth } from "@/lib/api/hooks";

export function BackendStatus() {
  const { data, error, isLoading } = useHealth();
  const online = !!data && !error;

  return (
    <div className="m-3 rounded-xl border border-line bg-white/60 px-3.5 py-3 text-[11px]">
      <div className="flex items-center gap-2 font-medium text-ink-2">
        <span
          className={cn(
            "size-1.5 rounded-full",
            isLoading ? "bg-faint animate-pulse" : online ? "bg-verified" : "bg-flagged",
          )}
        />
        {isLoading ? "Connecting…" : online ? "Backend online" : "Backend offline"}
      </div>
      {online && (
        <dl className="mt-2 grid grid-cols-2 gap-x-2 gap-y-1 text-faint">
          <dt>LLM</dt>
          <dd className="text-right text-muted">
            {data.llm_provider}
            {!data.llm_configured && " (no key)"}
          </dd>
          <dt>Graph</dt>
          <dd className="text-right text-muted">{data.graph_backend}</dd>
          <dt>Vectors</dt>
          <dd className="text-right text-muted">{data.vector_backend}</dd>
        </dl>
      )}
    </div>
  );
}
