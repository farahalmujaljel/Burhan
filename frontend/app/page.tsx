"use client";

import { useMemo, useState } from "react";
import { Background, Controls, ReactFlow, type Edge, type Node } from "@xyflow/react";
import { Activity, Bot, Database, FileText, GitBranch, Search, UploadCloud } from "lucide-react";
import { askBurhan, createRun } from "@/lib/api";
import type { GroundedAnswer, TwinState } from "@/lib/types";

const screens = ["Upload", "AI Analysis", "Structured Extraction", "Knowledge Graph", "Research Gap", "Ask Burhan"];

export default function Home() {
  const [active, setActive] = useState(0);
  const [files, setFiles] = useState<File[]>([]);
  const [progress, setProgress] = useState(0);
  const [message, setMessage] = useState("Upload exactly five breast cancer AI papers to begin.");
  const [loading, setLoading] = useState(false);
  const [twin, setTwin] = useState<TwinState | null>(null);
  const [selectedNode, setSelectedNode] = useState<Node | null>(null);
  const [question, setQuestion] = useState("What is the most effective method?");
  const [answer, setAnswer] = useState<GroundedAnswer | null>(null);

  const flow = useMemo(() => {
    if (!twin) return { nodes: [], edges: [] };
    const nodes: Node[] = twin.nodes.map((node, index) => ({
      id: node.id,
      position: { x: (index % 5) * 230, y: Math.floor(index / 5) * 130 },
      data: { label: `${node.type}: ${node.label}` },
      type: "default",
      style: { borderColor: colorFor(node.type), background: backgroundFor(node.type) }
    }));
    const edges: Edge[] = twin.edges.map((edge) => ({
      id: edge.id,
      source: edge.source,
      target: edge.target,
      label: edge.type,
      animated: edge.type === "SUGGESTS" || edge.type === "COMPARES"
    }));
    return { nodes, edges };
  }, [twin]);

  async function startRun() {
    setLoading(true);
    setProgress(10);
    setMessage("Uploading papers and starting the Burhan workflow.");
    setAnswer(null);
    try {
      const result = await createRun(files);
      setProgress(result.progress);
      setMessage(result.message);
      setTwin(result.twin);
      if (result.twin) setActive(1);
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Upload failed.");
    } finally {
      setLoading(false);
    }
  }

  async function submitQuestion() {
    if (!twin) return;
    setLoading(true);
    setMessage("Retrieving evidence and asking Burhan.");
    try {
      const result = await askBurhan(twin.run_id, question);
      setAnswer(result);
      setActive(5);
      setMessage("Grounded answer generated with paper citations.");
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Question failed.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="min-h-screen">
      <header className="border-b border-line bg-paper">
        <div className="mx-auto flex max-w-7xl flex-col gap-6 px-5 py-6 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <p className="text-sm font-semibold uppercase tracking-wide text-clay">Burhan MVP</p>
            <h1 className="mt-2 text-3xl font-semibold text-ink md:text-5xl">Agentic AI Research Scientist</h1>
            <p className="mt-3 max-w-3xl text-base leading-7 text-ink/75">
              Upload five research papers. Burhan extracts scientific knowledge, grows a graph, updates a Research Digital Twin, compares papers, finds one evidence-backed gap, and answers one grounded question.
            </p>
          </div>
          <div className="w-full max-w-md">
            <div className="h-2 overflow-hidden rounded-full bg-line">
              <div className="h-full bg-moss transition-all" style={{ width: `${progress}%` }} />
            </div>
            <p className="mt-2 text-sm text-ink/70">{message}</p>
          </div>
        </div>
      </header>

      <nav className="border-b border-line bg-white/70">
        <div className="mx-auto grid max-w-7xl grid-cols-2 gap-2 px-5 py-3 md:grid-cols-6">
          {screens.map((screen, index) => (
            <button
              key={screen}
              onClick={() => setActive(index)}
              className={`h-10 rounded-md border text-sm font-medium ${active === index ? "border-moss bg-moss text-white" : "border-line bg-white text-ink"}`}
            >
              {screen}
            </button>
          ))}
        </div>
      </nav>

      <section className="mx-auto max-w-7xl px-5 py-6">
        {active === 0 && (
          <Panel icon={<UploadCloud />} title="Upload Five PDFs">
            <input
              type="file"
              accept="application/pdf"
              multiple
              onChange={(event) => setFiles(Array.from(event.target.files ?? []))}
              className="w-full rounded-md border border-line bg-white p-3"
            />
            <div className="mt-4 grid gap-3 md:grid-cols-5">
              {files.map((file) => (
                <div key={file.name} className="rounded-md border border-line bg-white p-3 text-sm">
                  <FileText className="mb-2 h-4 w-4 text-moss" />
                  <p className="break-words font-medium">{file.name}</p>
                  <p className="text-ink/60">{Math.round(file.size / 1024)} KB</p>
                </div>
              ))}
            </div>
            <button
              disabled={files.length !== 5 || loading}
              onClick={startRun}
              className="mt-5 h-11 rounded-md bg-moss px-5 font-semibold text-white disabled:cursor-not-allowed disabled:bg-ink/25"
            >
              {loading ? "Building twin..." : "Build Research Digital Twin"}
            </button>
          </Panel>
        )}

        {active === 1 && (
          <Panel icon={<Activity />} title="AI Analysis">
            <MetricGrid twin={twin} />
          </Panel>
        )}

        {active === 2 && (
          <Panel icon={<Database />} title="Structured Extraction">
            <div className="grid gap-4">
              {twin?.papers.map((paper) => (
                <article key={paper.id} className="rounded-md border border-line bg-white p-4">
                  <h3 className="font-semibold">{paper.metadata.title}</h3>
                  <p className="mt-1 text-sm text-ink/60">{paper.filename}</p>
                  <div className="mt-4 grid gap-3 md:grid-cols-3">
                    <Fact label="Method" value={paper.extraction.method} />
                    <Fact label="Dataset" value={paper.extraction.dataset} />
                    <Fact label="Metrics" value={paper.extraction.metrics.join(", ")} />
                  </div>
                  <List title="Findings" items={paper.extraction.findings} />
                  <List title="Limitations" items={paper.extraction.limitations} />
                </article>
              )) ?? <Empty />}
            </div>
          </Panel>
        )}

        {active === 3 && (
          <Panel icon={<GitBranch />} title="Knowledge Graph">
            <div className="grid gap-4 lg:grid-cols-[1fr_320px]">
              <div className="h-[620px] overflow-hidden rounded-md border border-line bg-white">
                <ReactFlow nodes={flow.nodes} edges={flow.edges} fitView onNodeClick={(_, node) => setSelectedNode(node)}>
                  <Background />
                  <Controls />
                </ReactFlow>
              </div>
              <aside className="rounded-md border border-line bg-white p-4">
                <h3 className="font-semibold">Node metadata</h3>
                {selectedNode ? <pre className="mt-3 whitespace-pre-wrap text-xs">{JSON.stringify(selectedNode, null, 2)}</pre> : <p className="mt-3 text-sm text-ink/65">Click a graph node to inspect it.</p>}
              </aside>
            </div>
          </Panel>
        )}

        {active === 4 && (
          <Panel icon={<Search />} title="Research Gap">
            {twin ? (
              <div className="rounded-md border border-line bg-white p-5">
                <h3 className="text-xl font-semibold">{twin.research_gap.title}</h3>
                <p className="mt-3 leading-7 text-ink/75">{twin.research_gap.description}</p>
                <List title="Supporting Papers" items={twin.research_gap.supporting_papers} />
                <List title="Evidence" items={twin.research_gap.evidence} />
              </div>
            ) : (
              <Empty />
            )}
          </Panel>
        )}

        {active === 5 && (
          <Panel icon={<Bot />} title="Ask Burhan">
            <div className="grid gap-4 lg:grid-cols-[420px_1fr]">
              <div className="rounded-md border border-line bg-white p-4">
                <label className="text-sm font-semibold">Grounded question</label>
                <textarea value={question} onChange={(event) => setQuestion(event.target.value)} className="mt-2 h-32 w-full rounded-md border border-line p-3" />
                <button disabled={!twin || loading} onClick={submitQuestion} className="mt-3 h-10 rounded-md bg-moss px-4 font-semibold text-white disabled:bg-ink/25">
                  Ask Burhan
                </button>
              </div>
              <div className="rounded-md border border-line bg-white p-4">
                {answer ? (
                  <>
                    <h3 className="font-semibold">Grounded Answer</h3>
                    <p className="mt-3 leading-7 text-ink/75">{answer.answer}</p>
                    <List title="Citations" items={answer.citations} />
                    <List title="Evidence Retrieved" items={answer.evidence} />
                  </>
                ) : (
                  <p className="text-ink/65">Ask the required FARQ demo question after the twin is built.</p>
                )}
              </div>
            </div>
          </Panel>
        )}
      </section>
    </main>
  );
}

function Panel({ icon, title, children }: { icon: React.ReactNode; title: string; children: React.ReactNode }) {
  return (
    <div>
      <div className="mb-5 flex items-center gap-3">
        <div className="grid h-10 w-10 place-items-center rounded-md bg-clay text-white">{icon}</div>
        <h2 className="text-2xl font-semibold">{title}</h2>
      </div>
      {children}
    </div>
  );
}

function MetricGrid({ twin }: { twin: TwinState | null }) {
  if (!twin) return <Empty />;
  const items = [
    ["Papers", String(twin.papers.length)],
    ["Graph Nodes", String(twin.nodes.length)],
    ["Graph Edges", String(twin.edges.length)],
    ["Methods", twin.analysis.most_common_methods.join(", ")],
    ["Datasets", twin.analysis.most_common_datasets.join(", ")],
    ["Metrics", twin.analysis.common_metrics.join(", ")]
  ];
  return (
    <div className="grid gap-4 md:grid-cols-3">
      {items.map(([label, value]) => (
        <Fact key={label} label={label} value={value} />
      ))}
    </div>
  );
}

function Fact({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-md border border-line bg-white p-4">
      <p className="text-xs font-semibold uppercase tracking-wide text-clay">{label}</p>
      <p className="mt-2 text-sm leading-6 text-ink">{value || "Not found"}</p>
    </div>
  );
}

function List({ title, items }: { title: string; items: string[] }) {
  return (
    <div className="mt-4">
      <h4 className="text-sm font-semibold">{title}</h4>
      <ul className="mt-2 grid gap-2">
        {items.map((item, index) => (
          <li key={`${title}-${index}`} className="rounded-md bg-paper p-3 text-sm leading-6">
            {item}
          </li>
        ))}
      </ul>
    </div>
  );
}

function Empty() {
  return <div className="rounded-md border border-line bg-white p-5 text-ink/65">Build a Research Digital Twin from five PDFs to populate this screen.</div>;
}

function colorFor(type: string) {
  if (type === "Paper") return "#355c4a";
  if (type === "ResearchGap") return "#b46848";
  if (type === "Limitation") return "#8a5a44";
  return "#d7d4cb";
}

function backgroundFor(type: string) {
  if (type === "Paper") return "#eef5ef";
  if (type === "ResearchGap") return "#fff0e8";
  if (type === "Limitation") return "#fbf4ed";
  return "#fffdfa";
}
