import Link from "next/link";

import { EntityBadge, StatusPill } from "@/components/ui/Badges";
import { Card } from "@/components/ui/Card";
import type { EntityType, VectorHit } from "@/lib/api/types";
import { asVerificationStatus, ENTITY_STYLES } from "@/lib/entities";

import { EvidenceQuote } from "./EvidenceQuote";

const isEntityType = (t?: string | null): t is EntityType => !!t && t in ENTITY_STYLES;

export function EvidenceResultCard({
  hit,
  rank,
  paperTitle,
}: {
  hit: VectorHit;
  rank: number;
  paperTitle?: string;
}) {
  const p = hit.payload;
  const isEvidence = p.kind === "evidence";
  return (
    <Card as="article" className="px-5 py-4 transition-shadow hover:shadow-lift animate-fade-up">
      <div className="mb-3 flex items-center gap-2 text-[11px]">
        <span className="font-mono text-faint">#{rank}</span>
        {isEvidence ? (
          isEntityType(p.entity_type) ? <EntityBadge type={p.entity_type} /> : <StatusPill tone="brass">Evidence</StatusPill>
        ) : (
          <StatusPill tone="neutral">Passage</StatusPill>
        )}
        <span className="ml-auto font-mono text-faint" title="Semantic similarity">
          similarity {hit.score.toFixed(2)}
        </span>
      </div>
      {isEvidence && p.claim && (
        <p className="mb-3 text-[15px] font-medium leading-snug text-ink">
          {p.entity_id ? (
            <Link href={`/graph?focus=${encodeURIComponent(p.entity_id)}`} className="hover:underline">
              {p.claim}
            </Link>
          ) : (
            p.claim
          )}
        </p>
      )}
      <EvidenceQuote
        source={{
          quote: p.text,
          page: p.page,
          section: p.section,
          confidence: isEvidence ? p.confidence : null,
          verification_status: isEvidence ? asVerificationStatus(p.verification_status) : null,
          paperTitle,
        }}
      />
      <div className="mt-3 text-right">
        <Link href={`/papers/${p.paper_id}`} className="text-xs text-muted hover:text-ink">
          Open paper →
        </Link>
      </div>
    </Card>
  );
}
