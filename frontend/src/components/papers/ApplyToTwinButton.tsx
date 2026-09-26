"use client";

import { Sparkles } from "lucide-react";
import { useState } from "react";
import { useSWRConfig } from "swr";

import { Button } from "@/components/ui/Button";
import { api } from "@/lib/api/endpoints";
import type { TwinUpdate } from "@/lib/api/types";

export function ApplyToTwinButton({ paperId, onDone }: { paperId: string; onDone: () => void }) {
  const { mutate } = useSWRConfig();
  const [pending, setPending] = useState(false);
  const [result, setResult] = useState<TwinUpdate | null>(null);
  const [error, setError] = useState<string | null>(null);

  const apply = async () => {
    setPending(true);
    setError(null);
    try {
      setResult(await api.twin.applyPaper(paperId));
      await Promise.all([mutate("twin/summary"), mutate(["twin/updates", 100])]);
      onDone();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Twin update failed");
    } finally {
      setPending(false);
    }
  };

  return (
    <span className="inline-flex flex-col items-end gap-1">
      <Button icon={<Sparkles className="size-3.5" />} loading={pending} onClick={apply}>
        Merge into twin
      </Button>
      {result && <span className="max-w-72 text-right text-[11px] text-muted">{result.summary}</span>}
      {error && <span className="max-w-72 text-right text-[11px] text-flagged">{error}</span>}
    </span>
  );
}
