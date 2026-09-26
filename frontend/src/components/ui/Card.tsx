import type { ReactNode } from "react";

import { cn } from "./cn";

export function Card({
  children,
  className,
  as: Tag = "section",
}: {
  children: ReactNode;
  className?: string;
  as?: "section" | "div" | "article";
}) {
  return (
    <Tag
      className={cn(
        "rounded-2xl border border-line bg-white/70 shadow-card backdrop-blur-[2px]",
        className,
      )}
    >
      {children}
    </Tag>
  );
}

export function CardHeader({
  eyebrow,
  title,
  action,
  className,
}: {
  eyebrow?: string;
  title: ReactNode;
  action?: ReactNode;
  className?: string;
}) {
  return (
    <header className={cn("flex items-start justify-between gap-4 px-6 pt-5", className)}>
      <div>
        {eyebrow && (
          <p className="mb-1 text-[11px] font-medium tracking-[0.14em] text-faint uppercase">
            {eyebrow}
          </p>
        )}
        <h2 className="font-display text-xl leading-tight text-ink">{title}</h2>
      </div>
      {action}
    </header>
  );
}
