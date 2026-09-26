import type { TwinUpdate } from "@/lib/api/types";
import { formatDateTime } from "@/lib/format";
import { CHANGE_STYLES, growthSeries } from "@/lib/updates";

const H = 160;
const BAR_W = 22;
const GAP = 14;

/** How the twin grew: per-update entity changes (bars) and total entities over time (line). */
export function GrowthChart({ updates }: { updates: TwinUpdate[] }) {
  const points = growthSeries(updates);
  const maxBar = Math.max(1, ...points.map((p) => Math.max(p.added + p.strengthened, p.removed)));
  const maxTotal = Math.max(1, ...points.map((p) => p.total));
  const width = Math.max(points.length * (BAR_W + GAP) + GAP, 640);
  const mid = H * 0.72;
  const scale = (n: number) => (n / maxBar) * (mid - 16);
  const lineY = (n: number) => mid - 8 - (n / maxTotal) * (mid - 24);

  return (
    <div className="overflow-x-auto">
      <svg
        viewBox={`0 0 ${width} ${H}`}
        preserveAspectRatio="xMinYMid meet"
        className="h-44 w-full"
        style={{ minWidth: points.length > 20 ? width : undefined }}
        role="img"
        aria-label="Twin growth over time"
      >
        <line x1={0} x2={width} y1={mid} y2={mid} stroke="#e3ded4" />
        {points.map((p, i) => {
          const x = GAP + i * (BAR_W + GAP);
          const addH = scale(p.added);
          const strH = scale(p.strengthened);
          return (
            <g key={p.update.id}>
              <title>{`${formatDateTime(p.update.created_at)}\n+${p.added} added · ${p.strengthened} strengthened · −${p.removed} removed\n${p.total} entities`}</title>
              <rect x={x} y={mid - addH} width={BAR_W} height={addH} rx={3} fill={CHANGE_STYLES.added.color} opacity={0.85} />
              <rect x={x} y={mid - addH - strH} width={BAR_W} height={strH} rx={3} fill={CHANGE_STYLES.strengthened.color} opacity={0.85} />
              <rect x={x} y={mid + 2} width={BAR_W} height={scale(p.removed)} rx={3} fill={CHANGE_STYLES.removed.color} opacity={0.8} />
            </g>
          );
        })}
        {points.length > 1 && (
          <polyline
            fill="none"
            stroke="#0e0e10"
            strokeWidth={1.5}
            strokeDasharray="3 3"
            points={points.map((p, i) => `${GAP + i * (BAR_W + GAP) + BAR_W / 2},${lineY(p.total)}`).join(" ")}
          />
        )}
        {points.map((p, i) => (
          <circle key={p.update.id} cx={GAP + i * (BAR_W + GAP) + BAR_W / 2} cy={lineY(p.total)} r={3} fill="#0e0e10" />
        ))}
      </svg>
    </div>
  );
}
