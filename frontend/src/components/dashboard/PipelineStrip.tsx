import { Diamond } from "@/components/ui/Motifs";

const STEPS = [
  ["Read", "Parse papers into page-aware sections"],
  ["Extract", "Methods, datasets, results, and claims"],
  ["Verify", "Every claim checked against its source quote"],
  ["Connect", "Merge into a shared knowledge graph"],
  ["Evolve", "The twin updates with every new paper"],
];

/** How Burhan works, stated once so the dashboard is never mistaken for a chat app. */
export function PipelineStrip() {
  return (
    <ol className="flex flex-wrap items-stretch gap-y-3 rounded-2xl border border-line bg-paper-2/60 px-2 py-3">
      {STEPS.map(([title, text], i) => (
        <li key={title} className="flex min-w-[180px] flex-1 items-center gap-3 px-4">
          <span className="font-mono text-[11px] text-faint">0{i + 1}</span>
          <span>
            <span className="block text-sm font-medium text-ink">{title}</span>
            <span className="block text-xs text-muted">{text}</span>
          </span>
          {i < STEPS.length - 1 && <Diamond size={6} className="ml-auto hidden text-line-strong xl:block" />}
        </li>
      ))}
    </ol>
  );
}
