import Link from "next/link";

import { Card, CardHeader } from "@/components/ui/Card";
import { SkeletonLines } from "@/components/ui/Skeleton";
import type { EntityType, RankedEntity } from "@/lib/api/types";
import { ENTITY_STYLES } from "@/lib/entities";

export function TopEntities({
  type,
  items,
  paperCount,
}: {
  type: EntityType;
  items?: RankedEntity[];
  paperCount: number;
}) {
  const style = ENTITY_STYLES[type];
  const Icon = style.icon;
  return (
    <Card className="flex flex-col">
      <CardHeader
        eyebrow="Most used across papers"
        title={`Top ${style.plural.toLowerCase()}`}
        action={<Icon className="size-5" style={{ color: style.color }} />}
      />
      <div className="flex-1 px-6 pt-4 pb-6">
        {!items ? (
          <SkeletonLines lines={5} />
        ) : items.length === 0 ? (
          <p className="text-sm text-muted">None extracted yet.</p>
        ) : (
          <ol className="space-y-3">
            {items.slice(0, 6).map((item) => (
              <li key={item.id}>
                <Link href={`/graph?focus=${encodeURIComponent(item.id)}`} className="group block">
                  <div className="flex items-baseline justify-between gap-3 text-sm">
                    <span className="truncate text-ink group-hover:underline">{item.name}</span>
                    <span className="shrink-0 font-mono text-[11px] text-muted">
                      {item.paper_count}/{paperCount} papers
                    </span>
                  </div>
                  <div className="mt-1.5 h-1 overflow-hidden rounded-full bg-paper-3">
                    <div
                      className="h-full rounded-full"
                      style={{
                        width: `${Math.max(8, (item.paper_count / Math.max(paperCount, 1)) * 100)}%`,
                        backgroundColor: style.color,
                      }}
                    />
                  </div>
                </Link>
              </li>
            ))}
          </ol>
        )}
      </div>
    </Card>
  );
}
