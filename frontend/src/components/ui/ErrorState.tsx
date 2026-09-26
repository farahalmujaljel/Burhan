import { PlugZap } from "lucide-react";

import { API_BASE_URL, ApiError } from "@/lib/api/client";

import { cn } from "./cn";

export function ErrorState({ error, className }: { error: unknown; className?: string }) {
  const network = error instanceof ApiError && error.isNetworkError;
  const message = error instanceof Error ? error.message : "Something went wrong.";
  return (
    <div
      role="alert"
      className={cn(
        "flex items-start gap-3 rounded-xl border border-flagged/25 bg-flagged-soft/60 px-4 py-3 text-sm",
        className,
      )}
    >
      <PlugZap className="mt-0.5 size-4 shrink-0 text-flagged" />
      <div>
        <p className="font-medium text-ink">
          {network ? "The Burhan backend is not reachable" : "Request failed"}
        </p>
        <p className="mt-0.5 text-muted">
          {network ? (
            <>
              Start it with <code className="font-mono text-ink">make dev</code> (expected at{" "}
              <code className="font-mono text-ink">{API_BASE_URL}</code>).
            </>
          ) : (
            message
          )}
        </p>
      </div>
    </div>
  );
}
