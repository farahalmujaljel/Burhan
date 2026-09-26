import type { ReactNode } from "react";

export function PageHeader({
  eyebrow,
  title,
  description,
  actions,
}: {
  eyebrow?: string;
  title: ReactNode;
  description?: ReactNode;
  actions?: ReactNode;
}) {
  return (
    <header className="mb-8 flex flex-wrap items-end justify-between gap-4 animate-fade-up">
      <div className="max-w-2xl">
        {eyebrow && (
          <p className="mb-2 text-[11px] font-medium tracking-[0.16em] text-brass uppercase">
            {eyebrow}
          </p>
        )}
        <h1 className="font-display text-4xl leading-[1.1] tracking-tight text-ink">{title}</h1>
        {description && <p className="mt-3 text-[15px] leading-relaxed text-muted">{description}</p>}
      </div>
      {actions && <div className="flex items-center gap-2">{actions}</div>}
    </header>
  );
}
