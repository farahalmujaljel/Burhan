import { Check, X } from "lucide-react";

import { cn } from "@/components/ui/cn";
import type { PaperRecord } from "@/lib/api/types";
import { pipelineSteps, type StepState } from "@/lib/paper-status";

const DOT: Record<StepState, string> = {
  done: "bg-ink text-paper border-ink",
  active: "bg-brass-soft text-brass border-brass",
  failed: "bg-flagged-soft text-flagged border-flagged",
  pending: "bg-paper text-faint border-line-strong",
};

function StepDot({ state, size = "sm" }: { state: StepState; size?: "sm" | "lg" }) {
  return (
    <span
      className={cn(
        "flex shrink-0 items-center justify-center rounded-full border",
        size === "sm" ? "size-4" : "size-7",
        DOT[state],
      )}
    >
      {state === "done" && <Check className={size === "sm" ? "size-2.5" : "size-3.5"} />}
      {state === "failed" && <X className={size === "sm" ? "size-2.5" : "size-3.5"} />}
      {state === "active" && <span className="size-1.5 animate-pulse rounded-full bg-current" />}
    </span>
  );
}

/** Compact inline pipeline for table rows. */
export function PipelineDots({ paper }: { paper: PaperRecord }) {
  const steps = pipelineSteps(paper);
  return (
    <div className="flex items-center" aria-label="Processing pipeline">
      {steps.map((s, i) => (
        <div key={s.key} className="flex items-center" title={`${s.label}${s.detail ? ` — ${s.detail}` : ""}`}>
          <StepDot state={s.state} />
          {i < steps.length - 1 && (
            <span className={cn("h-px w-5", s.state === "done" ? "bg-ink/60" : "bg-line-strong")} />
          )}
        </div>
      ))}
    </div>
  );
}

/** Full stepper for the paper detail page. */
export function PipelineStepper({ paper }: { paper: PaperRecord }) {
  const steps = pipelineSteps(paper);
  return (
    <ol className="grid grid-cols-2 gap-4 md:grid-cols-4">
      {steps.map((s, i) => (
        <li key={s.key} className="relative flex gap-3">
          {i < steps.length - 1 && (
            <span
              className={cn(
                "absolute top-3.5 left-9 hidden h-px w-[calc(100%-2.75rem)] md:block",
                s.state === "done" ? "bg-ink/50" : "bg-line-strong",
              )}
            />
          )}
          <StepDot state={s.state} size="lg" />
          <div className="relative z-10 min-w-0 bg-transparent pt-0.5">
            <p className="text-sm font-medium text-ink">{s.label}</p>
            {s.detail && (
              <p className={cn("mt-0.5 text-xs", s.state === "failed" ? "text-flagged" : "text-muted")}>
                {s.detail}
              </p>
            )}
          </div>
        </li>
      ))}
    </ol>
  );
}
