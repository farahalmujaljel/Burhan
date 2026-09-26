import { ConfidenceMeter, VerificationBadge } from "@/components/ui/Badges";
import { cn } from "@/components/ui/cn";
import type { VerificationStatus } from "@/lib/api/types";

const BORDER: Record<VerificationStatus, string> = {
  verified: "border-verified/60",
  flagged: "border-flagged/70",
  unverified: "border-unverified/50",
};

export interface QuoteSource {
  quote: string;
  page?: number | null;
  section?: string | null;
  confidence?: number | null;
  verification_status?: VerificationStatus | null;
  verification_note?: string | null;
  paperTitle?: string;
}

/** A verbatim evidence quote with its provenance, the basic unit of trust in Burhan. */
export function EvidenceQuote({ source, className }: { source: QuoteSource; className?: string }) {
  const status = source.verification_status ?? "unverified";
  return (
    <figure className={cn("border-l-2 pl-4", BORDER[status], className)}>
      <blockquote className="font-display text-[15px] leading-relaxed text-ink-2 italic">
        “{source.quote.replace(/\s+/g, " ").trim()}”
      </blockquote>
      <figcaption className="mt-2 flex flex-wrap items-center gap-x-3 gap-y-1.5 text-[11px] text-muted">
        <VerificationBadge status={status} />
        {source.paperTitle && <span className="max-w-72 truncate font-medium text-ink-2">{source.paperTitle}</span>}
        {source.page != null && <span>p. {source.page}</span>}
        {source.section && <span className="max-w-60 truncate">§ {source.section}</span>}
        {source.confidence != null && <ConfidenceMeter value={source.confidence} />}
        {source.verification_note && status !== "verified" && (
          <span className="basis-full text-[11px] text-faint" title={source.verification_note}>
            {verifierReason(source.verification_note)}
          </span>
        )}
      </figcaption>
    </figure>
  );
}

/** Pull the verifier's human-readable reason out of the stored provenance note. */
function verifierReason(note: string): string {
  const match = note.match(/(?:not_supported|partially_supported|semantic check unavailable)[^[]*/);
  return (match?.[0] ?? note).replace(/_/g, " ").trim();
}
