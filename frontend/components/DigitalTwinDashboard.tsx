"use client";

import { useMemo, useState } from "react";
import { Background, Controls, ReactFlow, type Edge, type Node } from "@xyflow/react";
import { Bot, Database, FileSearch, GitBranch, Lightbulb, Network, Quote, Sparkles } from "lucide-react";
import type { GroundedAnswer, TwinState } from "@/lib/types";

const suggestedQuestions = [
  "What is the most effective method?",
  "Which datasets appear most often?",
  "What limitations repeat across papers?",
  "What evidence supports the research gap?"
];

export function DigitalTwinDashboard({
  twin,
  question,
  answer,
  loading,
  onQuestionChange,
  onAsk
}: {
  twin: TwinState;
  question: string;
  answer: GroundedAnswer | null;
  loading: boolean;
  onQuestionChange: (question: string) => void;
  onAsk: () => void;
}) {
  const [selectedNode, setSelectedNode] = useState<Node | null>(null);
  const flow = useMemo(() => buildFlow(twin), [twin]);

  return (
    <main className="min-h-screen bg-slate-50">
      <TopBar />
      <section className="mx-auto max-w-[1440px] px-5 py-6">
        <div className="mb-6 flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <p className="text-sm font-semibold uppercase tracking-[0.2em] text-blue-700">Research Digital Twin</p>
            <h1 className="mt-2 text-3xl font-semibold tracking-tight text-slate-950 md:text-4xl">Focused Research Domain</h1>
            <p className="mt-3 max-w-3xl text-base leading-7 text-slate-600">
              Burhan extracted structured knowledge from {twin.papers.length} papers and connected it into a graph-first research intelligence layer.
            </p>
          </div>
          <div className="rounded-lg border border-blue-100 bg-white px-4 py-3 text-sm text-slate-600 shadow-sm">
            Run ID <span className="font-semibold text-slate-950">{twin.run_id.slice(0, 10)}</span>
          </div>
        </div>

        <SummaryCards twin={twin} />

        <div className="mt-6 grid gap-6 xl:grid-cols-[1fr_390px]">
          <section className="rounded-lg border border-slate-200 bg-white shadow-sm shadow-blue-950/5">
            <div className="flex flex-col gap-3 border-b border-slate-200 p-5 md:flex-row md:items-center md:justify-between">
              <div>
                <div className="flex items-center gap-2">
                  <GitBranch className="h-5 w-5 text-blue-700" />
                  <h2 className="text-lg font-semibold text-slate-950">Knowledge Graph</h2>
                </div>
                <p className="mt-1 text-sm text-slate-500">Click any node to inspect its Digital Twin metadata.</p>
              </div>
              <GraphLegend />
            </div>
            <div className="grid min-h-[660px] xl:grid-cols-[1fr_320px]">
              <div className="h-[660px]">
                <ReactFlow nodes={flow.nodes} edges={flow.edges} fitView onNodeClick={(_, node) => setSelectedNode(node)}>
                  <Background color="#dbeafe" gap={22} />
                  <Controls />
                </ReactFlow>
              </div>
              <aside className="border-t border-slate-200 p-5 xl:border-l xl:border-t-0">
                <h3 className="font-semibold text-slate-950">Node details</h3>
                {selectedNode ? (
                  <div className="mt-4 space-y-4">
                    <div className="rounded-lg bg-blue-50 p-3">
                      <p className="text-xs font-semibold uppercase tracking-wide text-blue-700">Selected node</p>
                      <p className="mt-1 text-sm font-semibold text-slate-950">{String(selectedNode.data.label)}</p>
                    </div>
                    <pre className="max-h-[480px] overflow-auto rounded-lg bg-slate-950 p-4 text-xs leading-5 text-blue-50">{JSON.stringify(selectedNode, null, 2)}</pre>
                  </div>
                ) : (
                  <p className="mt-4 rounded-lg bg-slate-50 p-4 text-sm leading-6 text-slate-500">Select a paper, method, dataset, finding, limitation, or research gap node to inspect its metadata.</p>
                )}
              </aside>
            </div>
          </section>

          <ResearchAssistant question={question} answer={answer} loading={loading} onQuestionChange={onQuestionChange} onAsk={onAsk} />
        </div>

        <div className="mt-6 grid gap-6 xl:grid-cols-[1fr_420px]">
          <ExtractionOverview twin={twin} />
          <ResearchGapCard twin={twin} />
        </div>
      </section>
    </main>
  );
}

function TopBar() {
  return (
    <header className="sticky top-0 z-20 border-b border-slate-200 bg-white/90 backdrop-blur">
      <div className="mx-auto flex h-16 max-w-[1440px] items-center justify-between px-5">
        <div>
          <p className="text-lg font-semibold tracking-tight text-slate-950">Burhan</p>
          <p className="text-xs font-medium uppercase tracking-[0.18em] text-blue-700">Agentic Research Scientist</p>
        </div>
        <div className="hidden items-center gap-2 rounded-lg bg-blue-50 px-3 py-2 text-sm font-medium text-blue-800 md:flex">
          <Sparkles className="h-4 w-4" />
          Twin generated
        </div>
      </div>
    </header>
  );
}

function SummaryCards({ twin }: { twin: TwinState }) {
  const cards = [
    { label: "Papers", value: twin.papers.length, detail: "uploaded and parsed", icon: FileSearch },
    { label: "Methods", value: twin.analysis.most_common_methods.length, detail: firstOrCount(twin.analysis.most_common_methods), icon: Network },
    { label: "Datasets", value: twin.analysis.most_common_datasets.length, detail: firstOrCount(twin.analysis.most_common_datasets), icon: Database },
    { label: "Findings", value: twin.papers.reduce((sum, paper) => sum + paper.extraction.findings.length, 0), detail: "evidence-linked claims", icon: Quote },
    { label: "Research Gaps", value: 1, detail: "multi-paper support", icon: Lightbulb },
    { label: "Citations", value: twin.research_gap.supporting_papers.length, detail: "supporting papers", icon: GitBranch }
  ];

  return (
    <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-6">
      {cards.map((card) => {
        const Icon = card.icon;
        return (
          <article key={card.label} className="rounded-lg border border-slate-200 bg-white p-4 shadow-sm shadow-blue-950/5">
            <div className="flex items-center justify-between">
              <div className="grid h-10 w-10 place-items-center rounded-lg bg-blue-50 text-blue-700">
                <Icon className="h-5 w-5" />
              </div>
              <span className="text-2xl font-semibold text-slate-950">{card.value}</span>
            </div>
            <h2 className="mt-4 text-sm font-semibold text-slate-950">{card.label}</h2>
            <p className="mt-1 truncate text-xs text-slate-500">{card.detail}</p>
          </article>
        );
      })}
    </div>
  );
}

function ResearchAssistant({
  question,
  answer,
  loading,
  onQuestionChange,
  onAsk
}: {
  question: string;
  answer: GroundedAnswer | null;
  loading: boolean;
  onQuestionChange: (question: string) => void;
  onAsk: () => void;
}) {
  return (
    <aside className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm shadow-blue-950/5">
      <div className="flex items-center gap-2">
        <Bot className="h-5 w-5 text-blue-700" />
        <h2 className="text-lg font-semibold text-slate-950">Research Assistant</h2>
      </div>
      <p className="mt-2 text-sm leading-6 text-slate-500">Ask evidence-based questions after inspecting the Digital Twin.</p>

      <div className="mt-5 grid gap-2">
        {suggestedQuestions.map((suggestion) => (
          <button
            key={suggestion}
            type="button"
            onClick={() => onQuestionChange(suggestion)}
            className="rounded-lg border border-blue-100 bg-blue-50/70 px-3 py-2 text-left text-sm font-medium text-blue-900 transition hover:border-blue-300 hover:bg-blue-100"
          >
            {suggestion}
          </button>
        ))}
      </div>

      <label className="mt-5 block text-sm font-semibold text-slate-950">Grounded question</label>
      <textarea
        value={question}
        onChange={(event) => onQuestionChange(event.target.value)}
        className="mt-2 h-28 w-full resize-none rounded-lg border border-slate-200 bg-white p-3 text-sm leading-6 text-slate-900 outline-none transition focus:border-blue-400 focus:ring-4 focus:ring-blue-100"
      />
      <button disabled={loading || question.trim().length === 0} onClick={onAsk} className="mt-3 h-11 w-full rounded-lg bg-blue-700 text-sm font-semibold text-white shadow-sm shadow-blue-900/15 transition hover:bg-blue-800 disabled:cursor-not-allowed disabled:bg-slate-300">
        {loading ? "Retrieving evidence..." : "Ask Burhan"}
      </button>

      <div className="mt-5 rounded-lg bg-slate-50 p-4">
        {answer ? (
          <>
            <h3 className="text-sm font-semibold text-slate-950">Grounded answer</h3>
            <p className="mt-2 text-sm leading-6 text-slate-700">{answer.answer}</p>
            <EvidenceList title="Citations" items={answer.citations} />
            <EvidenceList title="Evidence retrieved" items={answer.evidence.slice(0, 4)} />
          </>
        ) : (
          <p className="text-sm leading-6 text-slate-500">Suggested questions are grounded in the uploaded papers and Research Digital Twin outputs.</p>
        )}
      </div>
    </aside>
  );
}

function ExtractionOverview({ twin }: { twin: TwinState }) {
  return (
    <section className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm shadow-blue-950/5">
      <div className="flex items-center gap-2">
        <Database className="h-5 w-5 text-blue-700" />
        <h2 className="text-lg font-semibold text-slate-950">Structured Extraction</h2>
      </div>
      <div className="mt-5 overflow-x-auto">
        <table className="w-full min-w-[760px] text-left text-sm">
          <thead className="text-xs uppercase tracking-wide text-slate-500">
            <tr className="border-b border-slate-200">
              <th className="pb-3 pr-4 font-semibold">Paper</th>
              <th className="pb-3 pr-4 font-semibold">Method</th>
              <th className="pb-3 pr-4 font-semibold">Dataset</th>
              <th className="pb-3 pr-4 font-semibold">Metrics</th>
              <th className="pb-3 font-semibold">Findings</th>
            </tr>
          </thead>
          <tbody>
            {twin.papers.map((paper) => (
              <tr key={paper.id} className="border-b border-slate-100 align-top last:border-0">
                <td className="py-4 pr-4 font-medium text-slate-950">{paper.metadata.title}</td>
                <td className="py-4 pr-4 text-slate-600">{paper.extraction.method}</td>
                <td className="py-4 pr-4 text-slate-600">{paper.extraction.dataset}</td>
                <td className="py-4 pr-4 text-slate-600">{paper.extraction.metrics.join(", ") || "Not found"}</td>
                <td className="py-4 text-slate-600">{paper.extraction.findings[0] || "Not found"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}

function ResearchGapCard({ twin }: { twin: TwinState }) {
  return (
    <section className="rounded-lg border border-blue-200 bg-blue-700 p-5 text-white shadow-lg shadow-blue-900/20">
      <div className="flex items-center gap-2">
        <Lightbulb className="h-5 w-5" />
        <h2 className="text-lg font-semibold">Evidence-backed research gap</h2>
      </div>
      <h3 className="mt-5 text-xl font-semibold leading-7">{twin.research_gap.title}</h3>
      <p className="mt-3 text-sm leading-6 text-blue-50">{twin.research_gap.description}</p>
      <EvidenceList title="Supporting papers" items={twin.research_gap.supporting_papers} inverted />
      <EvidenceList title="Evidence" items={twin.research_gap.evidence.slice(0, 4)} inverted />
    </section>
  );
}

function EvidenceList({ title, items, inverted = false }: { title: string; items: string[]; inverted?: boolean }) {
  return (
    <div className="mt-4">
      <h4 className={`text-xs font-semibold uppercase tracking-wide ${inverted ? "text-blue-100" : "text-slate-500"}`}>{title}</h4>
      <ul className="mt-2 grid gap-2">
        {items.map((item, index) => (
          <li key={`${title}-${index}`} className={`rounded-lg p-3 text-sm leading-6 ${inverted ? "bg-white/10 text-white" : "bg-white text-slate-600"}`}>
            {item}
          </li>
        ))}
      </ul>
    </div>
  );
}

function GraphLegend() {
  return (
    <div className="flex flex-wrap gap-2 text-xs font-medium">
      {["Paper", "Method", "Dataset", "Finding", "Gap"].map((item) => (
        <span key={item} className="rounded-lg bg-slate-50 px-2.5 py-1 text-slate-600">
          {item}
        </span>
      ))}
    </div>
  );
}

function buildFlow(twin: TwinState): { nodes: Node[]; edges: Edge[] } {
  const typeCounts = new Map<string, number>();
  const nodes: Node[] = twin.nodes.map((node, index) => {
    const typeIndex = typeCounts.get(node.type) ?? 0;
    typeCounts.set(node.type, typeIndex + 1);
    const position = positionFor(node.type, typeIndex, index);
    return {
      id: node.id,
      position,
      data: { label: node.label },
      type: "default",
      style: {
        borderColor: colorFor(node.type),
        background: backgroundFor(node.type),
        color: "#0f172a",
        boxShadow: "0 12px 30px rgba(15, 23, 42, 0.08)"
      }
    };
  });
  const edges: Edge[] = twin.edges.map((edge) => ({
    id: edge.id,
    source: edge.source,
    target: edge.target,
    label: edge.type,
    animated: edge.type === "SUGGESTS" || edge.type === "COMPARES",
    style: { stroke: edge.type === "SUGGESTS" ? "#2563eb" : "#93c5fd", strokeWidth: edge.type === "SUGGESTS" ? 2.4 : 1.5 },
    labelStyle: { fill: "#1e40af", fontSize: 10, fontWeight: 600 }
  }));
  return { nodes, edges };
}

function positionFor(type: string, typeIndex: number, fallbackIndex: number) {
  const lanes: Record<string, { x: number; y: number }> = {
    Paper: { x: 20, y: 80 },
    Method: { x: 320, y: 30 },
    Dataset: { x: 320, y: 230 },
    Metric: { x: 620, y: 30 },
    Finding: { x: 620, y: 210 },
    Limitation: { x: 920, y: 120 },
    ResearchGap: { x: 1180, y: 210 }
  };
  const lane = lanes[type] ?? { x: 200 + (fallbackIndex % 4) * 240, y: 120 };
  return { x: lane.x, y: lane.y + typeIndex * 96 };
}

function colorFor(type: string) {
  if (type === "Paper") return "#2563eb";
  if (type === "ResearchGap") return "#1d4ed8";
  if (type === "Limitation") return "#0ea5e9";
  if (type === "Finding") return "#60a5fa";
  return "#bfdbfe";
}

function backgroundFor(type: string) {
  if (type === "Paper") return "#eff6ff";
  if (type === "ResearchGap") return "#dbeafe";
  if (type === "Limitation") return "#f0f9ff";
  if (type === "Finding") return "#ffffff";
  return "#ffffff";
}

function firstOrCount(items: string[]) {
  if (items.length === 0) return "none detected";
  if (items.length === 1) return items[0];
  return `${items[0]} +${items.length - 1} more`;
}
