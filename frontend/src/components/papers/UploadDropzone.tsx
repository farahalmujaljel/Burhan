"use client";

import { FileUp, UploadCloud, X } from "lucide-react";
import { useRef, useState } from "react";

import { Button } from "@/components/ui/Button";
import { cn } from "@/components/ui/cn";
import { api } from "@/lib/api/endpoints";
import type { UploadResult } from "@/lib/api/types";
import { formatBytes } from "@/lib/format";

import { UploadResults } from "./UploadResults";

const isPdf = (f: File) => f.name.toLowerCase().endsWith(".pdf");

export function UploadDropzone({ onUploaded }: { onUploaded: () => void }) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [files, setFiles] = useState<File[]>([]);
  const [dragging, setDragging] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [results, setResults] = useState<UploadResult[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  const addFiles = (incoming: FileList | null) => {
    if (!incoming) return;
    const pdfs = Array.from(incoming).filter(isPdf);
    setError(pdfs.length < incoming.length ? "Only PDF files can be added." : null);
    setFiles((prev) => {
      const seen = new Set(prev.map((f) => `${f.name}:${f.size}`));
      return [...prev, ...pdfs.filter((f) => !seen.has(`${f.name}:${f.size}`))];
    });
    setResults(null);
  };

  const upload = async () => {
    setUploading(true);
    setError(null);
    try {
      const res = await api.papers.upload(files);
      setResults(res.results);
      setFiles([]);
      onUploaded();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Upload failed");
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="space-y-4">
      <div
        role="button"
        tabIndex={0}
        onClick={() => inputRef.current?.click()}
        onKeyDown={(e) => (e.key === "Enter" || e.key === " ") && inputRef.current?.click()}
        onDragOver={(e) => {
          e.preventDefault();
          setDragging(true);
        }}
        onDragLeave={() => setDragging(false)}
        onDrop={(e) => {
          e.preventDefault();
          setDragging(false);
          addFiles(e.dataTransfer.files);
        }}
        className={cn(
          "flex cursor-pointer flex-col items-center justify-center rounded-2xl border-2 border-dashed px-6 py-8 text-center transition-colors",
          dragging ? "border-brass bg-brass-soft/50" : "border-line-strong bg-paper-2/40 hover:border-ink/30",
        )}
      >
        <UploadCloud className={cn("mb-3 size-8", dragging ? "text-brass" : "text-muted")} />
        <p className="font-display text-lg text-ink">Drop research papers here</p>
        <p className="mt-1 text-sm text-muted">PDF only · several at once · parsed immediately</p>
        <input
          ref={inputRef}
          type="file"
          accept="application/pdf,.pdf"
          multiple
          hidden
          onChange={(e) => {
            addFiles(e.target.files);
            e.target.value = "";
          }}
        />
      </div>

      {error && <p className="text-sm text-flagged">{error}</p>}

      {files.length > 0 && (
        <div className="rounded-xl border border-line bg-white/70">
          <ul className="divide-y divide-line">
            {files.map((f) => (
              <li key={`${f.name}:${f.size}`} className="flex items-center gap-3 px-4 py-2.5 text-sm">
                <FileUp className="size-4 text-muted" />
                <span className="flex-1 truncate text-ink">{f.name}</span>
                <span className="font-mono text-xs text-faint">{formatBytes(f.size)}</span>
                <button
                  type="button"
                  aria-label={`Remove ${f.name}`}
                  onClick={() => setFiles((prev) => prev.filter((x) => x !== f))}
                  className="rounded p-1 text-faint hover:bg-paper-2 hover:text-ink"
                  disabled={uploading}
                >
                  <X className="size-3.5" />
                </button>
              </li>
            ))}
          </ul>
          <div className="flex items-center justify-between border-t border-line px-4 py-3">
            <span className="text-xs text-muted">
              {files.length} file{files.length === 1 ? "" : "s"} ready
            </span>
            <Button variant="primary" onClick={upload} loading={uploading}>
              {uploading ? "Uploading & parsing…" : "Upload & parse"}
            </Button>
          </div>
        </div>
      )}

      {results && <UploadResults results={results} />}
    </div>
  );
}
