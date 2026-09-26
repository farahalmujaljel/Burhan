import { ArrowRight, GitMerge } from "lucide-react";
import Link from "next/link";

import { ChangeChips } from "@/components/updates/ChangeChips";
import { Card, CardHeader } from "@/components/ui/Card";
import { SkeletonLines } from "@/components/ui/Skeleton";
import type { TwinUpdate } from "@/lib/api/types";
import { timeAgo } from "@/lib/format";

export function LatestUpdateCard({ update, loading }: { update?: TwinUpdate | null; loading: boolean }) {
  return (
    <Card className="flex flex-col">
      <CardHeader
        eyebrow="Twin evolution"
        title="Latest update"
        action={
          <Link href="/updates" className="inline-flex items-center gap-1 text-xs text-muted hover:text-ink">
            History <ArrowRight className="size-3.5" />
          </Link>
        }
      />
      <div className="flex-1 px-6 pt-4 pb-6">
        {loading ? (
          <SkeletonLines lines={4} />
        ) : !update ? (
          <p className="text-sm text-muted">No updates yet. The twin changes each time a paper is merged.</p>
        ) : (
          <div className="space-y-4">
            <p className="text-xs text-faint">
              {timeAgo(update.created_at)} · {update.operation === "remove" ? "paper removed" : "paper merged"}
            </p>
            <p className="font-display text-lg leading-snug text-ink">{update.summary}</p>
            <ChangeChips update={update} />
            {(update.resolutions?.length ?? 0) > 0 && (
              <p className="flex items-start gap-2 text-xs text-muted">
                <GitMerge className="mt-0.5 size-3.5 shrink-0 text-brass" />
                <span>
                  {update.resolutions!.slice(0, 3).map((r, i) => (
                    <span key={r.original_name}>
                      {i > 0 && ", "}“{r.original_name}” → {r.canonical_name}
                    </span>
                  ))}
                  {update.resolutions!.length > 3 && ` and ${update.resolutions!.length - 3} more`}
                </span>
              </p>
            )}
          </div>
        )}
      </div>
    </Card>
  );
}
