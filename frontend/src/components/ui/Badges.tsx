import type { EntityType, VerificationStatus } from "@/lib/api/types";
import { ENTITY_STYLES, VERIFICATION_STYLES } from "@/lib/entities";

import { cn } from "./cn";

export function VerificationBadge({
  status,
  className,
}: {
  status: VerificationStatus;
  className?: string;
}) {
  const s = VERIFICATION_STYLES[status];
  return (
    <span
      title={s.description}
      className={cn(
        "inline-flex items-center gap-1.5 rounded-full px-2 py-0.5 text-[11px] font-medium",
        s.bg,
        s.text,
        className,
      )}
    >
      <span className={cn("size-1.5 rounded-full", s.dot)} />
      {s.label}
    </span>
  );
}

export function EntityBadge({ type, className }: { type: EntityType; className?: string }) {
  const s = ENTITY_STYLES[type];
  const Icon = s.icon;
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1 rounded-md px-1.5 py-0.5 text-[11px] font-medium",
        className,
      )}
      style={{ color: s.color, backgroundColor: `${s.color}14` }}
    >
      <Icon className="size-3" />
      {s.label}
    </span>
  );
}

type Tone = "neutral" | "busy" | "ok" | "error" | "brass";

const TONES: Record<Tone, string> = {
  neutral: "bg-paper-2 text-muted",
  busy: "bg-brass-soft text-brass",
  ok: "bg-verified-soft text-verified",
  error: "bg-flagged-soft text-flagged",
  brass: "bg-brass-soft text-brass",
};

export function StatusPill({
  tone,
  children,
  pulse,
}: {
  tone: Tone;
  children: React.ReactNode;
  pulse?: boolean;
}) {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 rounded-full px-2 py-0.5 text-[11px] font-medium whitespace-nowrap",
        TONES[tone],
      )}
    >
      <span className={cn("size-1.5 rounded-full bg-current", pulse && "animate-pulse")} />
      {children}
    </span>
  );
}

export function ConfidenceMeter({ value }: { value: number }) {
  const pctValue = Math.round(value * 100);
  return (
    <span className="inline-flex items-center gap-2" title={`Confidence ${pctValue}%`}>
      <span className="h-1 w-14 overflow-hidden rounded-full bg-paper-3">
        <span className="block h-full rounded-full bg-ink/70" style={{ width: `${pctValue}%` }} />
      </span>
      <span className="font-mono text-[11px] text-muted tabular-nums">{pctValue}%</span>
    </span>
  );
}
