"use client";

import { ArrowRight, BarChart3, BrainCircuit, FileSearch, GitBranch, Layers3, MessageSquareQuote, Network, ShieldCheck, Sparkles } from "lucide-react";
import { BrandLogo } from "./Brand";

export function LandingPage({ onStart }: { onStart: () => void }) {
  return (
    <section className="relative isolate min-h-screen overflow-hidden bg-[#f7fbff]">
      <KnowledgeBackdrop />
      <div className="sticky top-0 z-30 border-b border-white/60 bg-white/80 backdrop-blur-xl">
        <header className="mx-auto flex h-20 max-w-7xl items-center justify-between px-5">
          <BrandLogo />
          <nav className="hidden items-center gap-8 rounded-full bg-white/70 px-6 py-3 text-sm font-semibold text-gray-600 shadow-sm shadow-blue-900/5 lg:flex">
            <a href="#" className="text-blue-700">Home</a>
            <a href="#how-it-works" className="transition hover:text-blue-700">How it Works</a>
            <a href="#features" className="transition hover:text-blue-700">Features</a>
            <a href="#about" className="transition hover:text-blue-700">About</a>
          </nav>
          <button
            onClick={onStart}
            className="inline-flex h-12 items-center gap-2 rounded-[18px] bg-blue-600 px-5 text-sm font-bold text-white shadow-lg shadow-blue-700/20 transition hover:-translate-y-0.5 hover:bg-blue-700"
          >
            Upload Research Papers
            <ArrowRight className="h-4 w-4" />
          </button>
        </header>
      </div>

      <div className="mx-auto flex min-h-[calc(100vh-80px)] max-w-7xl flex-col px-5">
        <div className="grid flex-1 items-center gap-14 py-16 lg:grid-cols-[1fr_520px]">
          <div>
            <div className="mb-6 inline-flex items-center gap-2 rounded-full border border-blue-100 bg-white/75 px-4 py-2 text-sm font-semibold text-blue-800 shadow-sm shadow-blue-900/5">
              <span className="h-2 w-2 rounded-full bg-blue-600" />
              FARQ Hackathon MVP • Research Intelligence
            </div>
            <h1 className="max-w-5xl text-5xl font-bold leading-[0.98] tracking-tight text-gray-900 md:text-7xl">
              Build a Living
              <span className="block bg-gradient-to-r from-blue-700 via-blue-500 to-sky-400 bg-clip-text text-transparent">Research Digital Twin</span>
            </h1>
            <p className="mt-7 max-w-3xl text-lg leading-8 text-gray-600 md:text-xl">
              Upload research papers and let Burhan automatically extract methods, datasets, findings, limitations, relationships, and research gaps to build a continuously evolving Digital Twin.
            </p>
            <div className="mt-10 flex flex-col gap-3 sm:flex-row">
              <button
                onClick={onStart}
                className="inline-flex h-14 items-center justify-center gap-2 rounded-[20px] bg-blue-600 px-7 text-base font-bold text-white shadow-xl shadow-blue-700/25 transition hover:-translate-y-0.5 hover:bg-blue-700"
              >
                Upload Research Papers
                <ArrowRight className="h-5 w-5" />
              </button>
              <a
                href="#how-it-works"
                className="inline-flex h-14 items-center justify-center rounded-[20px] bg-white/80 px-7 text-base font-bold text-blue-900 shadow-lg shadow-blue-900/5 ring-1 ring-blue-100 transition hover:-translate-y-0.5 hover:bg-white"
              >
                See workflow
              </a>
            </div>
          </div>

          <HeroIllustration />
        </div>

        <div id="features" className="grid gap-4 pb-10 sm:grid-cols-2 lg:grid-cols-5">
          <FeaturePill icon={<FileSearch />} title="Extract Knowledge" />
          <FeaturePill icon={<GitBranch />} title="Build Knowledge Graph" />
          <FeaturePill icon={<BrainCircuit />} title="Identify Research Gaps" />
          <FeaturePill icon={<BarChart3 />} title="Compare Papers" />
          <FeaturePill icon={<MessageSquareQuote />} title="Ask with Evidence" />
        </div>

        <div id="how-it-works" className="grid gap-5 pb-14 md:grid-cols-3">
          <ValueCard icon={<Layers3 />} title="Upload Papers" text="Start with five PDFs from one focused domain. Burhan keeps the workflow narrow, inspectable, and demo-ready." />
          <ValueCard icon={<GitBranch />} title="Generate the Twin" text="Knowledge extraction feeds a graph of papers, methods, datasets, findings, limitations, and gaps." />
          <ValueCard icon={<ShieldCheck />} title="Answer with Evidence" text="The assistant is grounded in extracted evidence and stays secondary to the Digital Twin." />
        </div>
      </div>
    </section>
  );
}

function ValueCard({ icon, title, text }: { icon: React.ReactNode; title: string; text: string }) {
  return (
    <article className="rounded-[24px] bg-white/85 p-6 shadow-xl shadow-blue-950/5 ring-1 ring-blue-100/70 backdrop-blur transition hover:-translate-y-1 hover:shadow-2xl hover:shadow-blue-950/10">
      <div className="mb-5 grid h-12 w-12 place-items-center rounded-[18px] bg-blue-50 text-blue-700">{icon}</div>
      <h2 className="text-lg font-bold text-gray-900">{title}</h2>
      <p className="mt-3 text-sm leading-6 text-gray-600">{text}</p>
    </article>
  );
}

function FeaturePill({ icon, title }: { icon: React.ReactNode; title: string }) {
  return (
    <div className="flex items-center gap-3 rounded-[22px] bg-white/80 p-4 shadow-lg shadow-blue-950/5 ring-1 ring-blue-100/80 backdrop-blur">
      <div className="grid h-10 w-10 shrink-0 place-items-center rounded-[16px] bg-[#EAF3FF] text-blue-700">{icon}</div>
      <span className="text-sm font-bold text-gray-800">{title}</span>
    </div>
  );
}

function HeroIllustration() {
  const cards = [
    { title: "Research Paper", detail: "PDF evidence", icon: FileSearch },
    { title: "Knowledge Extraction", detail: "methods, datasets, findings", icon: Sparkles },
    { title: "Knowledge Graph", detail: "relationships and evidence", icon: GitBranch },
    { title: "Research Digital Twin", detail: "living domain intelligence", icon: Network }
  ];
  return (
    <div className="relative mx-auto w-full max-w-[520px]">
      <div className="absolute inset-8 rounded-full bg-blue-300/20 blur-3xl" />
      <div className="relative rounded-[30px] bg-white/55 p-5 shadow-2xl shadow-blue-950/10 ring-1 ring-white/70 backdrop-blur-xl">
        <div className="grid gap-4">
          {cards.map((card, index) => {
            const Icon = card.icon;
            return (
              <div key={card.title} className="relative rounded-[24px] bg-white/85 p-5 shadow-lg shadow-blue-950/5 ring-1 ring-blue-100/80 transition hover:-translate-y-1">
                {index < cards.length - 1 && <div className="absolute -bottom-5 left-1/2 h-6 w-px bg-blue-300" />}
                <div className="flex items-center gap-4">
                  <div className="grid h-12 w-12 place-items-center rounded-[18px] bg-gradient-to-br from-blue-600 to-sky-400 text-white">
                    <Icon className="h-5 w-5" />
                  </div>
                  <div>
                    <h3 className="font-bold text-gray-900">{card.title}</h3>
                    <p className="mt-1 text-sm text-gray-500">{card.detail}</p>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}

function KnowledgeBackdrop() {
  return (
    <div className="pointer-events-none absolute inset-0 -z-10">
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_22%_22%,rgba(37,99,235,0.16),transparent_34%),radial-gradient(circle_at_72%_26%,rgba(14,165,233,0.13),transparent_32%),linear-gradient(180deg,#F8FBFF_0%,#EAF3FF_100%)]" />
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
