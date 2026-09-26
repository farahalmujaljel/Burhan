import { Card, CardHeader } from "@/components/ui/Card";
import { SkeletonLines } from "@/components/ui/Skeleton";
import type { ParsedDocument } from "@/lib/api/types";

export function DocumentOutline({ doc }: { doc?: ParsedDocument }) {
  return (
    <Card>
      <CardHeader eyebrow="Parsed structure" title="Sections" />
      <div className="px-6 pt-3 pb-5">
        {!doc ? (
          <SkeletonLines lines={6} />
        ) : (
          <ol className="space-y-1">
            {(doc.sections ?? []).map((s) => {
              const sub = /^\d+\.\d/.test(s.title);
              return (
                <li key={s.id} className={`flex items-baseline gap-2 text-sm ${sub ? "pl-4" : ""}`}>
                  <span className={`flex-1 truncate ${sub ? "text-muted" : "text-ink"}`}>{s.title}</span>
                  {s.kind && s.kind !== "other" && !sub && (
                    <span className="rounded bg-paper-2 px-1.5 text-[10px] text-faint">{s.kind.replace("_", " ")}</span>
                  )}
                  <span className="font-mono text-[11px] text-faint">p{s.page_start}</span>
                </li>
              );
            })}
          </ol>
        )}
      </div>
    </Card>
  );
}
