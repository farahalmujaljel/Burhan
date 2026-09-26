import Link from "next/link";

import { StatusPill } from "@/components/ui/Badges";
import type { UploadResult } from "@/lib/api/types";

function outcome(r: UploadResult) {
  if (r.error) return <StatusPill tone="error">Rejected</StatusPill>;
  if (r.duplicate) return <StatusPill tone="neutral">Already uploaded</StatusPill>;
  if (r.paper?.status === "failed") return <StatusPill tone="error">Could not parse</StatusPill>;
  return <StatusPill tone="ok">Parsed</StatusPill>;
}

export function UploadResults({ results }: { results: UploadResult[] }) {
  return (
    <ul className="divide-y divide-line rounded-xl border border-line bg-white/70 animate-fade-up">
      {results.map((r, i) => (
        <li key={`${r.file_name}-${i}`} className="flex items-center gap-3 px-4 py-2.5 text-sm">
          {outcome(r)}
          <span className="flex-1 truncate text-ink">{r.file_name}</span>
          <span className="max-w-[50%] truncate text-xs text-muted">
            {r.error?.message ?? r.paper?.error ?? (r.paper && `${r.paper.page_count} pages · ${r.paper.chunk_count} chunks`)}
          </span>
          {r.paper && (
            <Link href={`/papers/${r.paper.paper_id}`} className="text-xs font-medium text-ink underline-offset-2 hover:underline">
              Open
            </Link>
          )}
        </li>
      ))}
    </ul>
  );
}
