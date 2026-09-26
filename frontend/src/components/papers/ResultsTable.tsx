import { VerificationBadge } from "@/components/ui/Badges";
import type { PaperKnowledge } from "@/lib/api/types";

/** Quantitative results (REPORTS relations): method × metric × dataset = value. */
export function ResultsTable({ knowledge }: { knowledge: PaperKnowledge }) {
  const metrics = new Map((knowledge.metrics ?? []).map((m) => [m.id, m.name]));
  const rows = (knowledge.relations ?? []).filter((r) => r.type === "REPORTS");
  if (rows.length === 0) return <p className="text-sm text-faint">No quantitative results extracted.</p>;
  return (
    <table className="w-full text-sm">
      <thead>
        <tr className="border-b border-line text-left text-[11px] tracking-wide text-faint uppercase">
          <th className="py-2 pr-3 font-medium">Method</th>
          <th className="py-2 pr-3 font-medium">Metric</th>
          <th className="py-2 pr-3 text-right font-medium">Value</th>
          <th className="py-2 pr-3 font-medium">Dataset</th>
          <th className="py-2 font-medium">Evidence</th>
        </tr>
      </thead>
      <tbody className="divide-y divide-line">
        {rows.map((r) => {
          const ev = r.evidence?.[0];
          return (
            <tr key={r.id} title={ev?.quote}>
              <td className="py-2.5 pr-3 text-ink">{String(r.properties?.method ?? "—")}</td>
              <td className="py-2.5 pr-3 text-muted">{metrics.get(r.target_id) ?? "—"}</td>
              <td className="py-2.5 pr-3 text-right font-mono font-medium text-ink tabular-nums">
                {String(r.properties?.value ?? "—")}
              </td>
              <td className="py-2.5 pr-3 text-muted">{String(r.properties?.dataset ?? "—")}</td>
              <td className="py-2.5">
                {ev && <VerificationBadge status={ev.verification_status ?? "unverified"} />}
              </td>
            </tr>
          );
        })}
      </tbody>
    </table>
  );
}
