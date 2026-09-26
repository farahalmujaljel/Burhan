"use client";

import { FileText, Search, UploadCloud, X } from "lucide-react";
import { BrandLogo } from "./Brand";

export function UploadDropzone({
  files,
  loading,
  message,
  onFilesChange,
  onStart
}: {
  files: File[];
  loading: boolean;
  message: string;
  onFilesChange: (files: File[]) => void;
  onStart: () => void;
}) {
  function addFiles(nextFiles: FileList | File[]) {
    const pdfs = Array.from(nextFiles).filter((file) => file.type === "application/pdf" || file.name.toLowerCase().endsWith(".pdf"));
    onFilesChange(pdfs.slice(0, 5));
  }

  return (
    <section className="min-h-screen bg-[#F8FBFF] px-5 py-8">
      <div className="mx-auto max-w-6xl">
        <Header />
        <div className="mt-12 text-center">
          <p className="text-sm font-bold uppercase tracking-[0.22em] text-blue-600">Upload Research Papers</p>
          <h1 className="mt-3 text-4xl font-bold tracking-tight text-gray-900 md:text-6xl">Create your Research Digital Twin</h1>
          <p className="mx-auto mt-4 max-w-2xl text-lg leading-8 text-gray-600">Start with five PDFs from a single domain. Burhan will extract knowledge and build the graph-first twin.</p>
        </div>

        <div className="mt-10 grid gap-7 lg:grid-cols-[1fr_380px]">
          <label
            onDragOver={(event) => event.preventDefault()}
            onDrop={(event) => {
              event.preventDefault();
              addFiles(event.dataTransfer.files);
            }}
            className="group flex min-h-[520px] cursor-pointer flex-col items-center justify-center rounded-[28px] border-2 border-dashed border-blue-200 bg-white/90 p-8 text-center shadow-2xl shadow-blue-950/10 ring-1 ring-white/80 transition hover:-translate-y-1 hover:border-blue-500 hover:bg-white"
          >
            <input type="file" accept="application/pdf" multiple className="sr-only" onChange={(event) => addFiles(event.target.files ?? [])} />
            <div className="relative mb-7 grid h-32 w-32 place-items-center rounded-[32px] bg-gradient-to-br from-blue-600 to-sky-400 text-white shadow-2xl shadow-blue-700/25 transition group-hover:scale-105">
              <UploadCloud className="h-14 w-14" />
              <div className="absolute -right-4 -top-4 rounded-[18px] bg-white p-3 text-blue-700 shadow-xl">
                <FileText className="h-6 w-6" />
              </div>
            </div>
            <h2 className="text-3xl font-bold tracking-tight text-gray-900">Drag and drop your research papers here</h2>
            <p className="mt-4 max-w-xl text-base leading-7 text-gray-600">
              Supported sources include PDF exports from IEEE, ACM, Springer, arXiv, and other academic publishers.
            </p>
            <div className="mt-5 flex flex-wrap justify-center gap-2 text-xs font-bold text-blue-700">
              {["PDF", "IEEE", "ACM", "Springer", "arXiv"].map((item) => (
                <span key={item} className="rounded-full bg-[#EAF3FF] px-3 py-1.5">{item}</span>
              ))}
            </div>
            <span className="mt-7 inline-flex h-12 items-center rounded-[18px] bg-blue-600 px-6 text-sm font-bold text-white shadow-lg shadow-blue-700/20">
              Browse Files
            </span>
          </label>

          <aside className="rounded-[26px] bg-white p-6 shadow-xl shadow-blue-950/10 ring-1 ring-blue-100/80">
            <div className="flex items-center justify-between">
              <h2 className="font-bold text-gray-900">Selected papers</h2>
              <span className="rounded-full bg-blue-50 px-3 py-1.5 text-xs font-bold text-blue-700">{files.length}/5 PDFs</span>
            </div>
            <div className="mt-4 grid gap-3">
              {files.length === 0 ? (
                <div className="rounded-[20px] bg-slate-50 p-4 text-sm leading-6 text-gray-500">
                  <p>No files selected yet. The MVP requires exactly five PDFs.</p>
                  <div className="mt-4 space-y-2">
                    <p className="text-xs font-bold uppercase tracking-wide text-gray-400">Example papers</p>
                    {["Transformer survey.pdf", "Dataset benchmark.pdf", "Model comparison.pdf"].map((paper) => (
                      <div key={paper} className="flex items-center gap-2 text-gray-500">
                        <Search className="h-3.5 w-3.5 text-blue-500" />
                        {paper}
                      </div>
                    ))}
                  </div>
                </div>
              ) : (
                files.map((file) => (
                  <div key={`${file.name}-${file.size}`} className="flex items-start gap-3 rounded-[18px] bg-[#F8FBFF] p-3 ring-1 ring-blue-100/80">
                    <FileText className="mt-0.5 h-5 w-5 shrink-0 text-blue-700" />
                    <div className="min-w-0 flex-1">
                      <p className="truncate text-sm font-semibold text-slate-900">{file.name}</p>
                      <p className="text-xs text-slate-500">{Math.max(1, Math.round(file.size / 1024))} KB</p>
                    </div>
                    <button
                      type="button"
                      aria-label={`Remove ${file.name}`}
                      onClick={() => onFilesChange(files.filter((item) => item !== file))}
                      className="grid h-7 w-7 place-items-center rounded-[12px] text-slate-400 transition hover:bg-slate-100 hover:text-slate-700"
                    >
                      <X className="h-4 w-4" />
                    </button>
                  </div>
                ))
              )}
            </div>
            <button
              disabled={files.length !== 5 || loading}
              onClick={onStart}
              className="mt-5 w-full rounded-[18px] bg-blue-600 py-4 text-sm font-bold text-white shadow-lg shadow-blue-700/20 transition hover:-translate-y-0.5 hover:bg-blue-700 disabled:cursor-not-allowed disabled:bg-slate-300 disabled:shadow-none"
            >
              {loading ? "Starting analysis..." : "Generate Research Digital Twin"}
            </button>
            <p className="mt-4 text-sm leading-6 text-gray-500">{message}</p>
          </aside>
        </div>
      </div>
    </section>
  );
}

function Header() {
  return (
    <header className="flex items-center justify-between">
      <BrandLogo />
      <div className="rounded-full bg-white px-4 py-2 text-sm font-bold text-blue-800 shadow-sm shadow-blue-950/5 ring-1 ring-blue-100">Focused Research Domain</div>
    </header>
  );
}
