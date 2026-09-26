import { EvidenceQuote } from "@/components/evidence/EvidenceQuote";
import type { EntityType, Evidence } from "@/lib/api/types";
import { ENTITY_STYLES } from "@/lib/entities";

export interface Claim {
  id?: string;
  name: string;
  evidence?: Evidence[];
}

export function ClaimList({ type, claims }: { type: EntityType; claims: Claim[] }) {
  const style = ENTITY_STYLES[type];
  const Icon = style.icon;
  return (
    <div>
      <h3 className="mb-3 flex items-center gap-2 text-sm font-medium text-ink">
        <Icon className="size-4" style={{ color: style.color }} />
        {style.plural}
        <span className="text-faint">· {claims.length}</span>
      </h3>
      {claims.length === 0 ? (
        <p className="text-sm text-faint">None stated in this paper.</p>
      ) : (
        <ul className="space-y-5">
          {claims.map((c, i) => (
            <li key={c.id ?? i}>
              <p className="text-[15px] leading-snug font-medium text-ink">{c.name}</p>
              <div className="mt-2 space-y-3">
                {(c.evidence ?? []).map((ev) => (
                  <EvidenceQuote
                    key={ev.id}
                    source={{ ...ev, page: ev.span?.page ?? null }}
                  />
                ))}
              </div>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
