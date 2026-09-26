"use client";

import { ArrowRight, GitBranch, Layers3, ShieldCheck } from "lucide-react";

export function LandingPage({ onStart }: { onStart: () => void }) {
  return (
    <section className="relative isolate min-h-screen overflow-hidden bg-[#f7fbff]">
      <KnowledgeBackdrop />
      <div className="mx-auto flex min-h-screen max-w-7xl flex-col px-5 py-6">
        <header className="flex items-center justify-between">
          <div>
            <p className="text-lg font-semibold tracking-tight text-slate-950">Burhan</p>
            <p className="text-xs font-medium uppercase tracking-[0.22em] text-blue-700">Agentic AI Research Scientist</p>
          </div>
          <button
            onClick={onStart}
            className="hidden h-10 items-center gap-2 rounded-lg bg-blue-700 px-4 text-sm font-semibold text-white shadow-sm shadow-blue-900/15 transition hover:bg-blue-800 md:inline-flex"
          >
            Upload Research Papers
            <ArrowRight className="h-4 w-4" />
          </button>
        </header>

        <div className="flex flex-1 items-center py-16">
          <div className="max-w-4xl">
            <div className="mb-6 inline-flex items-center gap-2 rounded-lg border border-blue-200 bg-white/80 px-3 py-2 text-sm font-medium text-blue-800 shadow-sm">
              <span className="h-2 w-2 rounded-full bg-blue-600" />
              FARQ Hackathon MVP
            </div>
            <h1 className="max-w-5xl text-5xl font-semibold leading-[1.02] tracking-tight text-slate-950 md:text-7xl">
              Turn research papers into a living Research Digital Twin.
            </h1>
            <p className="mt-6 max-w-3xl text-lg leading-8 text-slate-600 md:text-xl">
              Upload five papers and Burhan extracts scientific knowledge, builds the knowledge graph, identifies an evidence-backed research gap, and prepares a grounded assistant answer.
            </p>
            <div className="mt-9 flex flex-col gap-3 sm:flex-row">
              <button
                onClick={onStart}
                className="inline-flex h-12 items-center justify-center gap-2 rounded-lg bg-blue-700 px-6 text-base font-semibold text-white shadow-lg shadow-blue-900/20 transition hover:bg-blue-800"
              >
                Upload Research Papers
                <ArrowRight className="h-5 w-5" />
              </button>
              <a
                href="#how-it-works"
                className="inline-flex h-12 items-center justify-center rounded-lg border border-blue-200 bg-white/80 px-6 text-base font-semibold text-blue-900 shadow-sm transition hover:bg-white"
              >
                See workflow
              </a>
            </div>
          </div>
        </div>

        <div id="how-it-works" className="grid gap-4 pb-8 md:grid-cols-3">
          <ValueCard icon={<Layers3 />} title="Structured extraction" text="Methods, datasets, metrics, findings, limitations, and evidence are extracted into validated research objects." />
          <ValueCard icon={<GitBranch />} title="Knowledge graph first" text="Burhan makes the graph the primary interface for understanding relationships across papers." />
          <ValueCard icon={<ShieldCheck />} title="Grounded intelligence" text="Research gaps and answers are tied back to supporting papers and evidence snippets." />
        </div>
      </div>
    </section>
  );
}

function ValueCard({ icon, title, text }: { icon: React.ReactNode; title: string; text: string }) {
  return (
    <article className="rounded-lg border border-blue-100 bg-white/85 p-5 shadow-sm shadow-blue-900/5 backdrop-blur">
      <div className="mb-4 grid h-10 w-10 place-items-center rounded-lg bg-blue-50 text-blue-700">{icon}</div>
      <h2 className="text-base font-semibold text-slate-950">{title}</h2>
      <p className="mt-2 text-sm leading-6 text-slate-600">{text}</p>
    </article>
  );
}

function KnowledgeBackdrop() {
  return (
    <div className="pointer-events-none absolute inset-0 -z-10">
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_25%_25%,rgba(59,130,246,0.16),transparent_32%),radial-gradient(circle_at_72%_30%,rgba(14,165,233,0.12),transparent_30%),linear-gradient(180deg,#f7fbff_0%,#eef6ff_100%)]" />
      <div className="absolute left-1/2 top-1/2 h-[620px] w-[920px] -translate-x-1/2 -translate-y-1/2 opacity-70">
        <div className="absolute left-[12%] top-[16%] h-3 w-3 rounded-full bg-blue-700 shadow-[160px_90px_0_#38bdf8,310px_20px_0_#1d4ed8,470px_170px_0_#60a5fa,680px_80px_0_#2563eb,220px_290px_0_#0ea5e9,560px_340px_0_#1d4ed8]" />
        <div className="absolute left-[18%] top-[25%] h-px w-[560px] rotate-12 bg-blue-300/70" />
        <div className="absolute left-[32%] top-[17%] h-px w-[420px] rotate-[28deg] bg-sky-300/70" />
        <div className="absolute left-[23%] top-[48%] h-px w-[500px] -rotate-6 bg-blue-300/70" />
        <div className="absolute left-[55%] top-[36%] h-px w-[260px] rotate-[55deg] bg-blue-300/70" />
      </div>
    </div>
  );
}
