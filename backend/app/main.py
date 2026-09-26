from __future__ import annotations

import shutil
from pathlib import Path
from uuid import uuid4

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from .ai import answer_with_llm, embed_texts, extract_scientific_knowledge
from .pdf_parser import full_text, parse_pdf
from .persistence import Persistence
from .reasoning import build_twin, make_grounded_answer
from .schemas import GroundedAnswer, PaperRecord, RunSummary, TwinState
from .settings import settings

app = FastAPI(title="Burhan MVP API", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

persistence = Persistence()
runs: dict[str, RunSummary] = {}


class QuestionRequest(BaseModel):
    question: str = "What is the most effective method?"


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "burhan-mvp"}


@app.post("/api/runs", response_model=RunSummary)
async def create_run(files: list[UploadFile] = File(...)) -> RunSummary:
    if len(files) != 5:
        raise HTTPException(status_code=400, detail="Upload exactly five PDF papers for the FARQ MVP workflow.")
    if any(file.content_type not in {"application/pdf", "application/octet-stream"} for file in files):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")

    run_id = uuid4().hex
    summary = RunSummary(run_id=run_id, status="queued", progress=5, message="Run created.")
    runs[run_id] = summary
    try:
        twin = await _process_run(run_id, files)
        summary.status = "complete"
        summary.progress = 100
        summary.message = "Research Digital Twin built successfully."
        summary.twin = twin
    except Exception as exc:
        summary.status = "failed"
        summary.message = str(exc)
        summary.progress = 100
    return summary


@app.get("/api/runs/{run_id}", response_model=RunSummary)
def get_run(run_id: str) -> RunSummary:
    if run_id not in runs:
        path = Path(settings.storage_dir) / "runs" / f"{run_id}.json"
        if path.exists():
            twin = TwinState.model_validate_json(path.read_text(encoding="utf-8"))
            return RunSummary(run_id=run_id, status="complete", progress=100, message="Loaded from local artifact.", twin=twin)
        raise HTTPException(status_code=404, detail="Run not found.")
    return runs[run_id]


@app.post("/api/runs/{run_id}/ask", response_model=GroundedAnswer)
def ask(run_id: str, body: QuestionRequest) -> GroundedAnswer:
    summary = get_run(run_id)
    if not summary.twin:
        raise HTTPException(status_code=409, detail="Run is not complete yet.")
    evidence = []
    for paper in summary.twin.papers:
        evidence.extend(paper.extraction.findings[:2])
        evidence.extend(paper.extraction.evidence_quotes[:2])
    context = "\n".join(f"{paper.metadata.title}\nMethod: {paper.extraction.method}\nFinding: {' '.join(paper.extraction.findings[:2])}" for paper in summary.twin.papers)
    answer = answer_with_llm(body.question, context, [paper.metadata.title for paper in summary.twin.papers])
    grounded = make_grounded_answer(body.question, answer, summary.twin.papers, evidence[:8])
    summary.twin.grounded_answer = grounded
    persistence.save_run_artifact(summary.twin)
    return grounded


async def _process_run(run_id: str, files: list[UploadFile]) -> TwinState:
    upload_dir = Path(settings.storage_dir) / "uploads" / run_id
    upload_dir.mkdir(parents=True, exist_ok=True)
    papers: list[PaperRecord] = []
    embeddings: list[tuple[str, list[float], dict]] = []

    runs[run_id].status = "parsing"
    runs[run_id].message = "Saving and parsing PDFs."
    runs[run_id].progress = 15

    for index, file in enumerate(files):
        safe_name = Path(file.filename or f"paper-{index + 1}.pdf").name
        path = upload_dir / safe_name
        with path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        metadata = parse_pdf(path)
        text = full_text(path)
        runs[run_id].status = "extracting"
        runs[run_id].message = f"Extracting scientific knowledge from {safe_name}."
        runs[run_id].progress = 25 + index * 10
        extraction = extract_scientific_knowledge(metadata, text)
        paper = PaperRecord(id=uuid4().hex, filename=safe_name, local_path=str(path), metadata=metadata, extraction=extraction)
        papers.append(paper)

        chunks = [metadata.abstract, extraction.problem, extraction.objective, extraction.method, " ".join(extraction.findings), " ".join(extraction.limitations)]
        vectors = embed_texts([chunk for chunk in chunks if chunk])
        for vector_index, vector in enumerate(vectors):
            embeddings.append((f"{paper.id}:{vector_index}", vector, {"paper_id": paper.id, "title": metadata.title, "filename": safe_name}))

    runs[run_id].status = "reasoning"
    runs[run_id].message = "Building graph, twin, cross-paper analysis, and research gap."
    runs[run_id].progress = 82
    twin = build_twin(run_id, papers)

    runs[run_id].status = "storing"
    runs[run_id].message = "Persisting metadata, embeddings, relationships, and local artifact."
    runs[run_id].progress = 92
    persistence.save_metadata_postgres(run_id, papers)
    persistence.save_embeddings_qdrant(run_id, embeddings)
    persistence.save_graph_neo4j(run_id, twin.nodes, twin.edges)
    persistence.save_run_artifact(twin)
    return twin
