# Development

## Layout

```
backend/        FastAPI service (Python 3.11+)
  app/core/     settings (env vars), logging, error handling
  app/schemas/  the data contract: entities, relations, evidence, parsed documents, twin
  app/parsing/  parser interface, PyMuPDF parser, section detection, chunking
  app/services/ ingestion pipeline and file-based document store
  app/api/      HTTP routes
  tests/        pytest suite
data/           demo papers, cached twin snapshots, uploads (gitignored)
docs/           product and architecture documentation
```

## Setup

```bash
python3 -m venv .venv
make install
cp .env.example .env   # then fill in GROQ_API_KEY
```

## Run

```bash
make dev    # http://localhost:8000/api/health, docs at http://localhost:8000/docs
make test
make lint
```

## Configuration

All configuration comes from environment variables (or the repo-root `.env`). See `.env.example`.
Secrets (`GROQ_API_KEY`, `NEO4J_PASSWORD`, `QDRANT_API_KEY`) are never logged or returned by the API.

The defaults are demo-safe and need no infrastructure:

| Setting | Default | Alternative |
|---|---|---|
| `GRAPH_BACKEND` | `memory` | `neo4j` (requires `NEO4J_PASSWORD`) |
| `VECTOR_BACKEND` | `local` (embedded Qdrant on disk) | `qdrant` (server) |
| `LLM_PROVIDER` | `groq` | provider-agnostic interface, more providers can be added |
| `EMBEDDING_MODEL` | `BAAI/bge-small-en-v1.5` (local) | any local embedding model |

To run Neo4j and Qdrant:

```bash
make infra-up     # Neo4j browser: http://localhost:7474, Qdrant: http://localhost:6333
make infra-down
```

## Ingestion pipeline

```
POST /api/papers (multipart, 1..N PDFs)
  -> validate (.pdf extension, content type, %PDF header, size limit)
  -> store data/uploads/<paper_id>/source.pdf (identical files are deduplicated by SHA-256)
  -> DocumentParser.parse    page-aware text + PageSpan offsets (PyMuPDF today, Docling later)
  -> detect_sections         heuristic headings -> Section(kind=abstract|methods|limitations|...)
  -> chunk_document          section-bounded chunks, exact slices of the text, with page ranges
  -> data/uploads/<paper_id>/parsed.json + record.json
```

| Endpoint | Purpose |
|---|---|
| `POST /api/papers` | Upload one or more PDFs; returns a per-file result (parsed, failed, rejected, duplicate) |
| `GET /api/papers` | List ingestion records |
| `GET /api/papers/{paper_id}` | One record (status, counts, error) |
| `GET /api/papers/{paper_id}/document` | Full `ParsedDocument`: text, pages, sections, chunks |
| `POST /api/papers/{paper_id}/process` | Re-parse a stored PDF |

Traceability guarantee: for every chunk, `document.text[chunk.char_start:chunk.char_end] == chunk.text`,
and `chunk.page`/`chunk.page_end` identify the PDF pages it came from. Corrupted, encrypted, or
text-less (scanned) PDFs are stored with `status: failed` and a reason; they never break a batch.

## Data contract rules

The schemas in `backend/app/schemas/` enforce Burhan's provenance guarantees:

- Every `Finding`, `Limitation`, `FutureWork`, and `ResearchGap` must carry at least one `Evidence`.
- Evidence on a paper-bound claim must come from that same paper.
- `Evidence` stores the verbatim quote, section, chunk, page/character span, the extracting agent,
  model, confidence, and a `verification_status` (`unverified` / `verified` / `flagged`).
- Relations are type-checked against the graph schema (e.g. `USES` is only `Paper -> Method`).
  Claim-like relations (`REPORTS`, `COMPARES`, `IMPROVES`, `CONTRADICTS`, `SUGGESTS`) require evidence.
- A `ResearchGap` must cite at least one structured `GapSignal` and the entities it came from.
- `ParsedDocument` chunks must match their character offsets exactly, so quotes can be anchored.
- `TwinSnapshot` rejects dangling relations, duplicate IDs, and evidence citing unknown papers.
- All models reject unknown fields, so extra keys in LLM output fail validation.
