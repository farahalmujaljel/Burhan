"use client";

import { CheckCircle2, CircleDashed, Database, FileUp, GitBranch, Layers3 } from "lucide-react";
import { BrandLogo } from "./Brand";

const steps = [
  { label: "Uploading papers", description: "Saving PDFs locally and preparing the paper set.", icon: FileUp, target: 25 },
  { label: "Extracting entities", description: "Parsing methods, datasets, metrics, findings, and limitations.", icon: Database, target: 70 },
  { label: "Building Knowledge Graph", description: "Creating paper, method, dataset, finding, limitation, and gap relationships.", icon: GitBranch, target: 88 },
  { label: "Generating Research Digital Twin", description: "Combining graph relationships and evidence into domain intelligence.", icon: Layers3, target: 100 }
];

export function ProcessingScreen({ progress, message }: { progress: number; message: string }) {
  const activeIndex = progress < 25 ? 0 : progress < 70 ? 1 : progress < 88 ? 2 : 3;

  return (
    <section className="grid min-h-screen place-items-center bg-[radial-gradient(circle_at_top_left,rgba(37,99,235,0.13),transparent_34%),linear-gradient(180deg,#F8FBFF,#EAF3FF)] px-5 py-10">
      <div className="w-full max-w-5xl rounded-[30px] bg-white/85 p-6 shadow-2xl shadow-blue-950/10 ring-1 ring-white/80 backdrop-blur md:p-8">
        <div className="flex flex-col gap-5 md:flex-row md:items-end md:justify-between">
          <div>
            <BrandLogo />
            <p className="mt-8 text-sm font-bold uppercase tracking-[0.2em] text-blue-700">Processing Pipeline</p>
            <h1 className="mt-2 text-3xl font-bold tracking-tight text-gray-900 md:text-5xl">Building the Research Digital Twin</h1>
            <p className="mt-3 max-w-2xl text-base leading-7 text-gray-600">{message}</p>
          </div>
          <div className="rounded-[24px] bg-[#EAF3FF] px-6 py-4 text-right">
            <div className="text-4xl font-bold text-blue-700">{progress}%</div>
            <p className="mt-1 text-sm font-semibold text-blue-900">~2 min remaining</p>
          </div>
        </div>
        <div className="mt-8 h-3 overflow-hidden rounded-full bg-slate-100">
          <div className="h-full rounded-full bg-gradient-to-r from-blue-600 to-sky-400 transition-all duration-500" style={{ width: `${Math.max(progress, 8)}%` }} />
        </div>
        <div className="mt-8 grid gap-4 lg:grid-cols-4">
          {steps.map((step, index) => {
            const Icon = step.icon;
            const complete = index < activeIndex || progress === 100;
            const active = index === activeIndex && progress < 100;
            const stepProgress = complete ? 100 : active ? Math.min(99, Math.max(18, Math.round((progress / step.target) * 100))) : 0;
            return (
              <article key={step.label} className={`rounded-[24px] p-5 shadow-lg shadow-blue-950/5 ring-1 transition ${active ? "bg-blue-50 ring-blue-200" : "bg-white ring-blue-100/70"}`}>
                <div className="flex items-center justify-between">
                  <div className="grid h-12 w-12 place-items-center rounded-[18px] bg-white text-blue-700 shadow-sm">
                    <Icon className="h-5 w-5" />
                  </div>
                  {complete ? <CheckCircle2 className="h-5 w-5 text-blue-700" /> : <CircleDashed className={`h-5 w-5 ${active ? "animate-spin text-blue-700" : "text-slate-300"}`} />}
                </div>
                <h2 className="mt-4 font-bold text-gray-900">{step.label}</h2>
                <p className="mt-2 min-h-[72px] text-sm leading-6 text-gray-600">{step.description}</p>
                <div className="mt-4 h-2 overflow-hidden rounded-full bg-slate-100">
                  <div className="h-full rounded-full bg-blue-600 transition-all duration-500" style={{ width: `${stepProgress}%` }} />
                </div>
                <p className="mt-2 text-xs font-bold text-blue-700">{stepProgress}%</p>
              </article>
            );
          })}
        </div>
      </div>
    </section>
  );
}
