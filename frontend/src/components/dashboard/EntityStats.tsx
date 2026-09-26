import { Card } from "@/components/ui/Card";
import { Skeleton } from "@/components/ui/Skeleton";
import type { EntityType, TwinSummary } from "@/lib/api/types";
import { ENTITY_STYLES } from "@/lib/entities";

const SHOWN: EntityType[] = ["Paper", "Method", "Dataset", "Metric", "Finding", "Limitation", "FutureWork"];

export function EntityStats({ summary }: { summary?: TwinSummary }) {
  return (
    <div className="grid grid-cols-2 gap-3 sm:grid-cols-4 xl:grid-cols-7">
      {SHOWN.map((type, i) => {
        const s = ENTITY_STYLES[type];
        const Icon = s.icon;
        const count = summary?.stats.entity_counts[type] ?? 0;
        return (
          <Card key={type} as="div" className="group px-4 py-3.5 transition-shadow hover:shadow-lift">
            <div className="animate-fade-up" style={{ animationDelay: `${i * 40}ms` }}>
              <div className="flex items-center justify-between">
                <span className="text-[11px] tracking-wide text-muted uppercase">{s.plural}</span>
                <Icon className="size-3.5" style={{ color: s.color }} />
              </div>
              <div className="mt-2 font-display text-3xl text-ink tabular-nums">
                {summary ? count : <Skeleton className="h-8 w-10" />}
              </div>
              <div className="mt-2 h-0.5 w-6 rounded-full" style={{ backgroundColor: s.color }} />
            </div>
          </Card>
        );
      })}
    </div>
  );
}
