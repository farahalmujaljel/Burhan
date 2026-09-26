import type { TwinUpdate } from "@/lib/api/types";
import { CHANGE_KINDS, CHANGE_STYLES, changeCount } from "@/lib/updates";

export function ChangeChips({ update, compact }: { update: TwinUpdate; compact?: boolean }) {
  return (
    <div className="flex flex-wrap gap-1.5">
      {CHANGE_KINDS.map((kind) => {
        const n = changeCount(update, kind);
        const s = CHANGE_STYLES[kind];
        return (
          <span
            key={kind}
            title={s.hint}
            className="inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-xs"
            style={{
              borderColor: n ? `${s.color}40` : "var(--color-line)",
              backgroundColor: n ? `${s.color}0f` : "transparent",
              color: n ? s.color : "var(--color-faint)",
            }}
          >
            <span className="font-mono font-medium tabular-nums">
              {kind === "removed" ? "−" : kind === "added" ? "+" : ""}
              {n}
            </span>
            {!compact && s.label.toLowerCase()}
          </span>
        );
      })}
    </div>
  );
}
