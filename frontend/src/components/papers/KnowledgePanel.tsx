import { EvidenceQuote } from "@/components/evidence/EvidenceQuote";
import { Card, CardHeader } from "@/components/ui/Card";
import type { PaperKnowledge } from "@/lib/api/types";

import { ClaimList } from "./ClaimList";
import { EntityChips } from "./EntityChips";
import { ResultsTable } from "./ResultsTable";

export function KnowledgePanel({ knowledge: k }: { knowledge: PaperKnowledge }) {
  const roles = new Map(
    (k.relations ?? [])
      .filter((r) => r.type === "USES" && r.properties?.role)
      .map((r) => [r.target_id, String(r.properties!.role)]),
  );

  return (
    <div className="space-y-6">
      {k.research_problem && (
        <Card className="px-6 py-5">
          <p className="mb-2 text-[11px] font-medium tracking-[0.14em] text-brass uppercase">Research problem</p>
          <p className="font-display text-xl leading-snug text-ink">{k.research_problem.text}</p>
          {k.research_problem.evidence[0] && (
            <EvidenceQuote
              className="mt-4"
              source={{ ...k.research_problem.evidence[0], page: k.research_problem.evidence[0].span?.page }}
            />
          )}
          {(k.research_questions ?? []).length > 0 && (
            <ul className="mt-4 list-disc space-y-1 pl-5 text-sm text-ink-2">
              {k.research_questions!.map((q) => (
                <li key={q.text}>{q.text}</li>
              ))}
            </ul>
          )}
        </Card>
      )}

      <Card>
        <CardHeader eyebrow="Shared concepts" title="Methods, datasets & metrics" />
        <div className="space-y-5 p-6">
          <EntityChips
            type="Method"
            items={(k.methods ?? []).map((m) => ({
              id: m.id,
              name: m.name,
              hint: m.id && roles.get(m.id) === "proposed" ? "proposed" : null,
            }))}
          />
          <EntityChips type="Dataset" items={k.datasets ?? []} />
          <EntityChips type="Metric" items={k.metrics ?? []} />
        </div>
        <div className="border-t border-line px-6 py-5">
          <h3 className="mb-3 text-[11px] font-medium tracking-wide text-muted uppercase">Reported results</h3>
          <ResultsTable knowledge={k} />
        </div>
      </Card>

      <Card>
        <CardHeader eyebrow="Evidence-backed claims" title="What the paper claims" />
        <div className="space-y-8 p-6">
          <ClaimList type="Finding" claims={k.findings ?? []} />
          <ClaimList type="Limitation" claims={k.limitations ?? []} />
          <ClaimList type="FutureWork" claims={k.future_work ?? []} />
        </div>
      </Card>
    </div>
  );
}
