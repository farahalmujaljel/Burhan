"use client";

import Link from "next/link";

import { StatusPill } from "@/components/ui/Badges";
import type { PaperRecord } from "@/lib/api/types";
import { timeAgo } from "@/lib/format";
import { displayTitle } from "@/lib/paper-status";

import { ExtractButton } from "./ExtractButton";
import { PipelineDots } from "./PipelineSteps";

function StatusCell({ p }: { p: PaperRecord }) {
  if (p.status === "failed") return <StatusPill tone="error">Parse failed</StatusPill>;
  if (p.extraction_status === "running") return <StatusPill tone="busy" pulse>Extracting</StatusPill>;
  if (p.extraction_status === "failed") return <StatusPill tone="error">Extraction failed</StatusPill>;
  if (p.twin_error) return <StatusPill tone="error">Twin update failed</StatusPill>;
  if (p.twin_updated_at) return <StatusPill tone="ok">In the twin</StatusPill>;
  if (p.extraction_status === "completed") return <StatusPill tone="brass">Extracted</StatusPill>;
  return <StatusPill tone="neutral">Parsed · awaiting extraction</StatusPill>;
}

export function PapersTable({
  papers,
  onChange,
}: {
  papers: PaperRecord[];
  onChange: () => void;
}) {
  return (
    <div className="overflow-x-auto rounded-2xl border border-line bg-white/70 shadow-card">
      <table className="w-full min-w-[820px] text-sm">
        <thead>
          <tr className="border-b border-line bg-paper-2/60 text-left text-[11px] tracking-wide text-faint uppercase">
            <th className="px-5 py-3 font-medium">Paper</th>
            <th className="px-3 py-3 font-medium">Structure</th>
            <th className="px-3 py-3 font-medium">Pipeline</th>
            <th className="px-3 py-3 font-medium">Status</th>
            <th className="px-5 py-3 text-right font-medium">Action</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-line">
          {papers.map((p) => (
            <tr key={p.paper_id} className="group transition-colors hover:bg-paper-2/40">
              <td className="max-w-md px-5 py-3.5">
                <Link href={`/papers/${p.paper_id}`} className="block">
                  <span className="line-clamp-1 font-medium text-ink group-hover:underline">
                    {displayTitle(p)}
                  </span>
                  <span className="mt-0.5 block truncate text-xs text-faint">
                    {p.file_name} · added {timeAgo(p.created_at)}
                  </span>
                </Link>
              </td>
              <td className="px-3 py-3.5 font-mono text-xs whitespace-nowrap text-muted">
                {p.status === "parsed"
                  ? `${p.page_count}p · ${p.section_count}s · ${p.chunk_count}c`
                  : "—"}
              </td>
              <td className="px-3 py-3.5">
                <PipelineDots paper={p} />
              </td>
              <td className="px-3 py-3.5">
                <StatusCell p={p} />
              </td>
              <td className="px-5 py-3.5 text-right">
                <ExtractButton paper={p} onStarted={onChange} />
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export function PapersTableSkeleton() {
  return (
    <div className="space-y-px overflow-hidden rounded-2xl border border-line">
      {Array.from({ length: 4 }, (_, i) => (
        <div key={i} className="skeleton h-14" />
      ))}
    </div>
  );
}
