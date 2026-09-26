import { Card, CardHeader } from "@/components/ui/Card";
import type { ExtractionMeta } from "@/lib/api/types";
import { formatDateTime } from "@/lib/format";

/** Transparency: how extraction ran, and what was rejected and why. */
export function ExtractionReport({ meta }: { meta: ExtractionMeta }) {
  const s = meta.stats;
  const stats: [string, number | undefined][] = [
    ["Proposed", s?.items_proposed],
    ["Kept", s?.items_kept],
    ["Dropped", s?.items_dropped],
    ["LLM calls", s?.llm_calls],
  ];
  return (
    <Card>
      <CardHeader eyebrow="Provenance" title="Extraction report" />
      <div className="space-y-4 px-6 pt-3 pb-5 text-sm">
        <dl className="grid grid-cols-4 gap-2">
          {stats.map(([label, value]) => (
            <div key={label} className="rounded-lg bg-paper-2/70 px-2 py-2 text-center">
              <dd className="font-display text-xl text-ink tabular-nums">{value ?? 0}</dd>
              <dt className="text-[10px] tracking-wide text-faint uppercase">{label}</dt>
            </div>
          ))}
        </dl>
        <p className="text-xs text-muted">
          {(meta.models ?? []).join(", ")} · prompts {meta.prompt_version} · {formatDateTime(meta.finished_at)}
        </p>
        {(meta.dropped ?? []).length > 0 && (
          <details className="group">
            <summary className="cursor-pointer text-xs font-medium text-ink-2 select-none">
              {meta.dropped!.length} item{meta.dropped!.length === 1 ? "" : "s"} rejected during grounding
            </summary>
            <ul className="mt-2 space-y-2">
              {meta.dropped!.map((d, i) => (
                <li key={i} className="rounded-lg border border-line px-3 py-2 text-xs">
                  <span className="text-faint">{d.kind.replace("_", " ")} · </span>
                  <span className="text-ink-2">{d.text}</span>
                  <span className="mt-0.5 block text-flagged">{d.reason}</span>
                </li>
              ))}
            </ul>
          </details>
        )}
        {(meta.warnings ?? []).length > 0 && (
          <ul className="space-y-1 text-xs text-flagged">
            {meta.warnings!.map((w) => (
              <li key={w}>{w}</li>
            ))}
          </ul>
        )}
      </div>
    </Card>
  );
}
