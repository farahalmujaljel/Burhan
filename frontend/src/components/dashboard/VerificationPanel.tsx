import { ShieldCheck } from "lucide-react";

import { Card, CardHeader } from "@/components/ui/Card";
import { cn } from "@/components/ui/cn";
import { SkeletonLines } from "@/components/ui/Skeleton";
import type { TwinSummary, VerificationStatus } from "@/lib/api/types";
import { VERIFICATION_STYLES } from "@/lib/entities";
import { pct } from "@/lib/format";

export function VerificationPanel({ summary }: { summary?: TwinSummary }) {
  const counts: Record<VerificationStatus, number> = {
    verified: summary?.stats.verified_evidence ?? 0,
    flagged: summary?.stats.flagged_evidence ?? 0,
    unverified: summary?.unverified_evidence ?? 0,
  };
  const total = counts.verified + counts.flagged + counts.unverified;
  const order: VerificationStatus[] = ["verified", "flagged", "unverified"];

  return (
    <Card className="flex flex-col">
      <CardHeader
        eyebrow="Evidence integrity"
        title="Verification"
        action={<ShieldCheck className="size-5 text-verified" />}
      />
      <div className="flex-1 px-6 pt-4 pb-6">
        {!summary ? (
          <SkeletonLines lines={4} />
        ) : total === 0 ? (
          <p className="text-sm text-muted">No evidence yet. It appears after the first extraction.</p>
        ) : (
          <>
            <p className="font-display text-4xl text-ink tabular-nums">
              {pct(counts.verified, total)}%
              <span className="ml-2 font-sans text-sm text-muted">of {total} quotes verified</span>
            </p>
            <div className="mt-5 flex h-2.5 overflow-hidden rounded-full bg-paper-3">
              {order.map((s) =>
                counts[s] ? (
                  <div
                    key={s}
                    className={cn("h-full transition-all", VERIFICATION_STYLES[s].dot)}
                    style={{ width: `${pct(counts[s], total)}%` }}
                  />
                ) : null,
              )}
            </div>
            <ul className="mt-5 space-y-2.5">
              {order.map((s) => (
                <li key={s} className="flex items-start justify-between gap-3 text-sm">
                  <span className="flex items-start gap-2">
                    <span className={cn("mt-1.5 size-2 rounded-full", VERIFICATION_STYLES[s].dot)} />
                    <span>
                      <span className="font-medium text-ink">{VERIFICATION_STYLES[s].label}</span>
                      <span className="block text-xs text-faint">{VERIFICATION_STYLES[s].description}</span>
                    </span>
                  </span>
                  <span className="font-mono text-sm text-ink-2 tabular-nums">{counts[s]}</span>
                </li>
              ))}
            </ul>
          </>
        )}
      </div>
    </Card>
  );
}
