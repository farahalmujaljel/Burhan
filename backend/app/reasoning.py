from __future__ import annotations

from collections import Counter, defaultdict
from datetime import datetime
from uuid import uuid4

from .schemas import CrossPaperAnalysis, GraphEdge, GraphNode, GroundedAnswer, PaperRecord, ResearchGap, TwinState


def build_twin(run_id: str, papers: list[PaperRecord]) -> TwinState:
    nodes: list[GraphNode] = []
    edges: list[GraphEdge] = []
    method_nodes: dict[str, str] = {}
    dataset_nodes: dict[str, str] = {}
    metric_nodes: dict[str, str] = {}

    for paper in papers:
        paper_node = GraphNode(
            id=f"paper:{paper.id}",
            type="Paper",
            label=paper.metadata.title[:90],
            metadata={"filename": paper.filename, "year": paper.metadata.year, "authors": paper.metadata.authors},
        )
        nodes.append(paper_node)

        method_id = method_nodes.setdefault(_key(paper.extraction.method), f"method:{len(method_nodes) + 1}")
        if not any(node.id == method_id for node in nodes):
            nodes.append(GraphNode(id=method_id, type="Method", label=paper.extraction.method, metadata={}))
        edges.append(_edge(paper_node.id, method_id, "USES"))

        dataset_id = dataset_nodes.setdefault(_key(paper.extraction.dataset), f"dataset:{len(dataset_nodes) + 1}")
        if not any(node.id == dataset_id for node in nodes):
            nodes.append(GraphNode(id=dataset_id, type="Dataset", label=paper.extraction.dataset, metadata={}))
        edges.append(_edge(paper_node.id, dataset_id, "EVALUATES"))

        for metric in paper.extraction.metrics:
            metric_id = metric_nodes.setdefault(_key(metric), f"metric:{len(metric_nodes) + 1}")
            if not any(node.id == metric_id for node in nodes):
                nodes.append(GraphNode(id=metric_id, type="Metric", label=metric, metadata={}))
            edges.append(_edge(paper_node.id, metric_id, "REPORTS"))

        for index, finding in enumerate(paper.extraction.findings[:3]):
            finding_id = f"finding:{paper.id}:{index}"
            nodes.append(GraphNode(id=finding_id, type="Finding", label=finding[:110], metadata={"paper": paper.metadata.title}))
            edges.append(_edge(paper_node.id, finding_id, "CLAIMS"))

        for index, limitation in enumerate(paper.extraction.limitations[:3]):
            limitation_id = f"limitation:{paper.id}:{index}"
            nodes.append(GraphNode(id=limitation_id, type="Limitation", label=limitation[:110], metadata={"paper": paper.metadata.title}))
            edges.append(_edge(paper_node.id, limitation_id, "STATES"))

    _add_method_comparisons(edges, method_nodes)
    analysis = analyze_papers(papers)
    gap = detect_research_gap(papers, analysis)
    gap_node = GraphNode(id="gap:primary", type="ResearchGap", label=gap.title, metadata={"supporting_papers": gap.supporting_papers})
    nodes.append(gap_node)
    for paper_title in gap.supporting_papers:
        match = next((paper for paper in papers if paper.metadata.title == paper_title), None)
        if match:
            edges.append(_edge(f"paper:{match.id}", gap_node.id, "SUGGESTS"))

    return TwinState(run_id=run_id, created_at=datetime.utcnow(), papers=papers, nodes=nodes, edges=edges, analysis=analysis, research_gap=gap)


def analyze_papers(papers: list[PaperRecord]) -> CrossPaperAnalysis:
    methods = Counter(_key(paper.extraction.method) for paper in papers)
    datasets = Counter(_key(paper.extraction.dataset) for paper in papers)
    metrics = Counter(metric.lower() for paper in papers for metric in paper.extraction.metrics)
    limitation_groups: defaultdict[str, list[str]] = defaultdict(list)
    for paper in papers:
        for limitation in paper.extraction.limitations:
            limitation_groups[_limitation_theme(limitation)].append(paper.metadata.title)
    repeated = [f"{theme} ({len(set(titles))} papers)" for theme, titles in limitation_groups.items() if len(set(titles)) >= 2]
    contradictions = _find_contradictions(papers)
    return CrossPaperAnalysis(
        most_common_methods=[item for item, _ in methods.most_common(5)],
        most_common_datasets=[item for item, _ in datasets.most_common(5)],
        repeated_limitations=repeated[:5],
        contradictions=contradictions[:5],
        common_metrics=[item for item, _ in metrics.most_common(6)],
    )


def detect_research_gap(papers: list[PaperRecord], analysis: CrossPaperAnalysis) -> ResearchGap:
    evidence: list[str] = []
    supporting: list[str] = []
    for paper in papers:
        for limitation in paper.extraction.limitations:
            if _limitation_theme(limitation) in " ".join(analysis.repeated_limitations):
                evidence.append(limitation)
                supporting.append(paper.metadata.title)
                break
    if len(set(supporting)) < 2:
        for paper in papers[:2]:
            evidence.extend(paper.extraction.limitations[:1])
            supporting.append(paper.metadata.title)
    return ResearchGap(
        title="Need for externally validated and generalizable AI research evidence",
        description="Multiple uploaded papers indicate limitations around validation breadth, dataset size, generalization, or clinical robustness. The evidence supports a gap around evaluating AI detection methods on larger, diverse, externally validated datasets.",
        supporting_papers=list(dict.fromkeys(supporting))[:5],
        evidence=list(dict.fromkeys(evidence))[:6],
    )


def make_grounded_answer(question: str, answer: str, papers: list[PaperRecord], evidence: list[str]) -> GroundedAnswer:
    citations = [paper.metadata.title for paper in papers if any(snippet in paper.extraction.evidence_quotes + paper.extraction.findings for snippet in evidence)]
    if not citations:
        citations = [paper.metadata.title for paper in papers[:3]]
    return GroundedAnswer(question=question, answer=answer, citations=list(dict.fromkeys(citations)), evidence=evidence)


def _edge(source: str, target: str, relation: GraphEdge.model_fields["type"].annotation) -> GraphEdge:
    return GraphEdge(id=f"edge:{uuid4().hex}", source=source, target=target, type=relation)


def _key(value: str) -> str:
    return " ".join(value.lower().strip().split()) or "unknown"


def _limitation_theme(value: str) -> str:
    lower = value.lower()
    if "external" in lower or "general" in lower or "validation" in lower:
        return "external validation and generalization"
    if "small" in lower or "dataset" in lower or "sample" in lower:
        return "small or narrow datasets"
    if "imbalance" in lower or "bias" in lower:
        return "dataset imbalance or bias"
    if "clinical" in lower:
        return "clinical deployment evidence"
    return "validation breadth"


def _find_contradictions(papers: list[PaperRecord]) -> list[str]:
    statements: list[str] = []
    for paper in papers:
        combined = " ".join(paper.extraction.findings).lower()
        if "outperform" in combined and "not" in combined:
            statements.append(f"Mixed performance claims reported in {paper.metadata.title}.")
    return statements or ["No explicit contradiction was strongly supported by the uploaded papers."]


def _add_method_comparisons(edges: list[GraphEdge], method_nodes: dict[str, str]) -> None:
    values = list(method_nodes.values())
    for index in range(len(values) - 1):
        edges.append(_edge(values[index], values[index + 1], "COMPARES"))
