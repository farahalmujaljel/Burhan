"use client";

import { FileText, UploadCloud, X } from "lucide-react";

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
    <section className="min-h-screen bg-slate-50 px-5 py-8">
      <div className="mx-auto max-w-6xl">
        <Header />
        <div className="mt-10 grid gap-6 lg:grid-cols-[1fr_360px]">
          <label
            onDragOver={(event) => event.preventDefault()}
            onDrop={(event) => {
              event.preventDefault();
              addFiles(event.dataTransfer.files);
            }}
            className="group flex min-h-[420px] cursor-pointer flex-col items-center justify-center rounded-lg border border-dashed border-blue-300 bg-white p-8 text-center shadow-sm shadow-blue-950/5 transition hover:border-blue-500 hover:bg-blue-50/40"
          >
            <input type="file" accept="application/pdf" multiple className="sr-only" onChange={(event) => addFiles(event.target.files ?? [])} />
            <div className="grid h-16 w-16 place-items-center rounded-lg bg-blue-50 text-blue-700 transition group-hover:bg-blue-100">
              <UploadCloud className="h-8 w-8" />
            </div>
            <h1 className="mt-6 text-3xl font-semibold tracking-tight text-slate-950">Upload five research papers</h1>
            <p className="mt-3 max-w-xl text-base leading-7 text-slate-600">
              Drag and drop PDFs about one research domain. Burhan will parse, extract, build the graph, and generate the Research Digital Twin.
            </p>
            <span className="mt-6 inline-flex h-11 items-center rounded-lg bg-blue-700 px-5 text-sm font-semibold text-white shadow-sm shadow-blue-900/15">
              Choose PDF files
            </span>
          </label>

          <aside className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm shadow-blue-950/5">
            <div className="flex items-center justify-between">
              <h2 className="font-semibold text-slate-950">Selected papers</h2>
              <span className="rounded-lg bg-blue-50 px-2.5 py-1 text-xs font-semibold text-blue-700">{files.length}/5 PDFs</span>
            </div>
            <div className="mt-4 grid gap-3">
              {files.length === 0 ? (
                <p className="rounded-lg bg-slate-50 p-4 text-sm leading-6 text-slate-500">No files selected yet. The MVP requires exactly five PDFs.</p>
              ) : (
                files.map((file) => (
                  <div key={`${file.name}-${file.size}`} className="flex items-start gap-3 rounded-lg border border-slate-200 bg-white p-3">
                    <FileText className="mt-0.5 h-5 w-5 shrink-0 text-blue-700" />
                    <div className="min-w-0 flex-1">
                      <p className="truncate text-sm font-semibold text-slate-900">{file.name}</p>
                      <p className="text-xs text-slate-500">{Math.max(1, Math.round(file.size / 1024))} KB</p>
                    </div>
                    <button
                      type="button"
                      aria-label={`Remove ${file.name}`}
                      onClick={() => onFilesChange(files.filter((item) => item !== file))}
                      className="grid h-7 w-7 place-items-center rounded-lg text-slate-400 transition hover:bg-slate-100 hover:text-slate-700"
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
              className="mt-5 h-12 w-full rounded-lg bg-blue-700 text-sm font-semibold text-white shadow-lg shadow-blue-900/15 transition hover:bg-blue-800 disabled:cursor-not-allowed disabled:bg-slate-300 disabled:shadow-none"
            >
              {loading ? "Starting analysis..." : "Generate Research Digital Twin"}
            </button>
            <p className="mt-3 text-sm leading-6 text-slate-500">{message}</p>
          </aside>
        </div>
      </div>
    </section>
  );
}

function Header() {
  return (
    <header className="flex items-center justify-between">
      <div>
        <p className="text-lg font-semibold text-slate-950">Burhan</p>
        <p className="text-sm text-slate-500">Paper-to-twin workflow</p>
      </div>
      <div className="rounded-lg border border-blue-100 bg-white px-3 py-2 text-sm font-medium text-blue-800 shadow-sm">Breast Cancer Detection using AI</div>
    </header>
  );
}
