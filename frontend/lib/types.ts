export type PaperRecord = {
  id: string;
  filename: string;
  metadata: {
    title: string;
    authors: string[];
    year: number | null;
    abstract: string;
    sections: Record<string, string>;
  };
  extraction: {
    problem: string;
    objective: string;
    method: string;
    dataset: string;
    metrics: string[];
    findings: string[];
    limitations: string[];
    future_work: string[];
    evidence_quotes: string[];
  };
};

export type TwinState = {
  run_id: string;
  papers: PaperRecord[];
  nodes: Array<{ id: string; type: string; label: string; metadata: Record<string, unknown> }>;
  edges: Array<{ id: string; source: string; target: string; type: string }>;
  analysis: {
    most_common_methods: string[];
    most_common_datasets: string[];
    repeated_limitations: string[];
    contradictions: string[];
    common_metrics: string[];
  };
  research_gap: {
    title: string;
    description: string;
    supporting_papers: string[];
    evidence: string[];
  };
  grounded_answer: GroundedAnswer | null;
};

export type GroundedAnswer = {
  question: string;
  answer: string;
  citations: string[];
  evidence: string[];
};

export type RunSummary = {
  run_id: string;
  status: string;
  progress: number;
  message: string;
  twin: TwinState | null;
};
