import type { ReactNode } from "react";

import { cn } from "./cn";
import { Diamond, StarMark } from "./Motifs";

export function EmptyState({
  title,
  description,
  action,
  className,
}: {
  title: string;
  description?: ReactNode;
  action?: ReactNode;
  className?: string;
}) {
  return (
    <div
      className={cn(
        "flex flex-col items-center justify-center px-6 py-12 text-center animate-fade-up",
        className,
      )}
    >
      <div className="relative mb-5 flex size-16 items-center justify-center">
        <div className="absolute inset-0 rounded-full border border-dashed border-line-strong" />
        <Diamond size={6} className="absolute -top-0.5 text-faint" />
        <Diamond size={6} className="absolute -bottom-0.5 text-faint" />
        <StarMark size={20} className="text-ink/70" />
      </div>
      <h3 className="font-display text-lg text-ink">{title}</h3>
      {description && <p className="mt-1.5 max-w-sm text-sm text-muted">{description}</p>}
      {action && <div className="mt-5">{action}</div>}
    </div>
  );
}
