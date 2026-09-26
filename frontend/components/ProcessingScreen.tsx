"use client";

import { CheckCircle2, CircleDashed, Database, GitBranch, Layers3 } from "lucide-react";

const steps = [
  { label: "Scientific extraction", description: "Parsing sections and extracting methods, datasets, metrics, findings, and limitations.", icon: Database },
  { label: "Knowledge graph construction", description: "Creating paper, method, dataset, finding, limitation, and gap relationships.", icon: GitBranch },
  { label: "Digital Twin generation", description: "Combining graph relationships and evidence into the Research Digital Twin.", icon: Layers3 }
];

export function ProcessingScreen({ progress, message }: { progress: number; message: string }) {
  const activeIndex = progress < 45 ? 0 : progress < 82 ? 1 : 2;

  return (
    <section className="grid min-h-screen place-items-center bg-slate-50 px-5 py-10">
      <div className="w-full max-w-4xl rounded-lg border border-slate-200 bg-white p-6 shadow-xl shadow-blue-950/10 md:p-8">
        <div className="flex flex-col gap-5 md:flex-row md:items-end md:justify-between">
          <div>
            <p className="text-sm font-semibold uppercase tracking-[0.2em] text-blue-700">Processing</p>
            <h1 className="mt-2 text-3xl font-semibold tracking-tight text-slate-950 md:text-4xl">Building the Research Digital Twin</h1>
            <p className="mt-3 max-w-2xl text-base leading-7 text-slate-600">{message}</p>
          </div>
          <div className="text-4xl font-semibold text-blue-700">{progress}%</div>
        </div>
        <div className="mt-8 h-3 overflow-hidden rounded-lg bg-slate-100">
          <div className="h-full rounded-lg bg-blue-700 transition-all duration-500" style={{ width: `${Math.max(progress, 8)}%` }} />
        </div>
        <div className="mt-8 grid gap-4 md:grid-cols-3">
          {steps.map((step, index) => {
            const Icon = step.icon;
            const complete = index < activeIndex || progress === 100;
            const active = index === activeIndex && progress < 100;
            return (
              <article key={step.label} className={`rounded-lg border p-5 ${active ? "border-blue-300 bg-blue-50" : "border-slate-200 bg-white"}`}>
                <div className="flex items-center justify-between">
                  <div className="grid h-10 w-10 place-items-center rounded-lg bg-white text-blue-700 shadow-sm">
                    <Icon className="h-5 w-5" />
                  </div>
                  {complete ? <CheckCircle2 className="h-5 w-5 text-blue-700" /> : <CircleDashed className={`h-5 w-5 ${active ? "animate-spin text-blue-700" : "text-slate-300"}`} />}
                </div>
                <h2 className="mt-4 font-semibold text-slate-950">{step.label}</h2>
                <p className="mt-2 text-sm leading-6 text-slate-600">{step.description}</p>
              </article>
            );
          })}
        </div>
      </div>
    </section>
  );
}
