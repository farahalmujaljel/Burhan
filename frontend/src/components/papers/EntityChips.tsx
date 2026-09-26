import type { EntityType } from "@/lib/api/types";
import { ENTITY_STYLES } from "@/lib/entities";

export function EntityChips({
  type,
  items,
}: {
  type: EntityType;
  items: { id?: string; name: string; hint?: string | null }[];
}) {
  const style = ENTITY_STYLES[type];
  const Icon = style.icon;
  return (
    <div>
      <h3 className="mb-2.5 flex items-center gap-2 text-[11px] font-medium tracking-wide text-muted uppercase">
        <Icon className="size-3.5" style={{ color: style.color }} />
        {style.plural} <span className="text-faint">· {items.length}</span>
      </h3>
      {items.length === 0 ? (
        <p className="text-sm text-faint">None extracted.</p>
      ) : (
        <ul className="flex flex-wrap gap-1.5">
          {items.map((it) => (
            <li
              key={it.id ?? it.name}
              className="rounded-lg border px-2.5 py-1 text-sm text-ink"
              style={{ borderColor: `${style.color}33`, backgroundColor: `${style.color}0b` }}
            >
              {it.name}
              {it.hint && <span className="ml-1.5 text-[11px] text-muted">{it.hint}</span>}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
