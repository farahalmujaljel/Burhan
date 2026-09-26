# Development

## Layout

```
backend/        FastAPI service (Python 3.11+)
  app/core/     settings (env vars), logging, error handling
  app/schemas/  the data contract: entities, relations, evidence, parsed documents, twin
  app/parsing/  parser interface, PyMuPDF parser, section detection, chunking
  app/llm/      provider-agnostic LLM client (Groq), structured output, prompts/*.md
  app/services/ ingestion, extraction, quote grounding, evidence verification, document store
  app/knowledge/ entity resolution, graph stores (memory, Neo4j), vector store (Qdrant)
  app/embeddings/ local embedders (model2vec default, fastembed, hashing)
  app/twin/     Research Twin Builder, evidence index, update log, twin service
  app/api/      HTTP routes
  tests/        pytest suite
frontend/       Next.js interface (dashboard, papers, graph, evidence, twin evolution)
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

## Frontend

```bash
make frontend-install
make dev            # backend on :8000 (terminal 1)
make frontend-dev   # frontend on :3000 (terminal 2)
make frontend-check # lint + type-check + production build
```

`frontend/.env.local` sets `NEXT_PUBLIC_API_URL` (default `http://localhost:8000`). After changing
backend schemas, run `npm run gen:api` in `frontend/` to regenerate the TypeScript API types.

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
| `POST /api/papers/{paper_id}/process` | Re-parse a stored PDF (clears any extraction result) |
| `POST /api/papers/{paper_id}/extract` | Run LLM extraction + evidence verification (202, or 200 with `?wait=true`) |
| `GET /api/papers/{paper_id}/knowledge` | Stored `PaperKnowledge`: entities, relations, evidence, run metadata |

Traceability guarantee: for every chunk, `document.text[chunk.char_start:chunk.char_end] == chunk.text`,
and `chunk.page`/`chunk.page_end` identify the PDF pages it came from. Corrupted, encrypted, or
text-less (scanned) PDFs are stored with `status: failed` and a reason; they never break a batch.

## Scientific extraction

```
POST /api/papers/{paper_id}/extract          (background; ?wait=true to run synchronously)
  -> windows of chunks (EXTRACTION_WINDOW_CHARS), chunk IDs shown to the LLM
  -> Groq JSON mode -> DraftExtraction (Pydantic), up to LLM_MAX_RETRIES repair retries
  -> merge duplicates across windows
  -> ground: locate each quote in the parsed text (exact -> normalized -> fuzzy in cited chunk)
            no located quote => item dropped and listed in meta.dropped
  -> verify: entity names found in their quote are verified deterministically;
            claims are checked by the LLM verifier (supported / partially / not supported)
  -> PaperKnowledge validated and saved to data/uploads/<paper_id>/knowledge.json
GET /api/papers/{paper_id}/knowledge
```

Evidence status meanings: `verified` (quote located and supports the claim), `flagged`
(located but the verifier judged it partially or not supported; confidence capped at 0.5/0.2),
`unverified` (located, but the semantic check could not run). Flagged items are kept, not hidden.

Groq free tier: `openai/gpt-oss-120b` allows about 8,000 tokens per minute, and Groq counts the
requested `LLM_MAX_OUTPUT_TOKENS` toward it. The defaults (`EXTRACTION_WINDOW_CHARS=8000`,
`LLM_MAX_OUTPUT_TOKENS=4096`, `LLM_HTTP_RETRIES=6`) keep each call under that limit; the SDK waits
out 429s. A 15-page paper takes roughly 8 calls, ~28k tokens, and 2-3 minutes on the free tier.

Tests use `tests/fake_llm.py` and never call Groq. Prompts live in `backend/app/llm/prompts/`;
bump `PROMPT_VERSION` when changing them.

## Knowledge layer and Research Digital Twin

After a successful extraction the paper is merged into the twin automatically
(`POST /api/twin/papers/{paper_id}` re-applies it manually; it is idempotent).

```
PaperKnowledge
  -> entity resolution   Method/Dataset/Metric names matched against the graph (conservative:
                         exact, connector/plural-insensitive, trailing acronym, fuzzy >= 95 with
                         identical numbers). Originals kept as aliases; near misses are only reported.
  -> graph               deterministic node/edge IDs; the paper's previous contribution is detached,
                         the new one merged, and only differences are written
  -> evidence index      chunks + evidence quotes embedded locally, stored in Qdrant with paper,
                         page, section, chunk, evidence, entity, and verification metadata
  -> TwinUpdate          added / strengthened / changed / removed entities and relations, merges
```

| Endpoint | Purpose |
|---|---|
| `POST /api/twin/papers/{paper_id}` | Apply (or re-apply) a paper; returns the `TwinUpdate` |
| `DELETE /api/twin/papers/{paper_id}` | Remove a paper's contribution; shared entities keep other support |
| `GET /api/twin/summary` | Counts, verification stats, top methods/datasets/metrics, last update |
| `GET /api/twin/snapshot` | Full validated `TwinSnapshot` (entities, relations with evidence, history) |
| `GET /api/twin/updates` | Change history, newest first |
| `GET /api/graph` | Nodes + edges for visualization (`paper_id`, `type`, `limit` filters) |
| `GET /api/graph/nodes/{node_id}` | Node, edges, neighbors, and full evidence |
| `GET /api/evidence/search?q=` | Semantic search over evidence/chunks (`paper_id`, `kind` filters) |

Backends are explicit: `GRAPH_BACKEND=memory` persists to `data/twin/graph.json`;
`GRAPH_BACKEND=neo4j` uses Docker Neo4j. `VECTOR_BACKEND=local` uses embedded Qdrant in
`data/qdrant_local`; `qdrant` uses the Docker server. There is no silent fallback between them.

Embeddings: `model2vec` (default, `minishlab/potion-retrieval-32M`, ~131 MB, downloaded to the
Hugging Face cache on first use). `fastembed` needs onnxruntime, which has no Intel-macOS wheels.
When installing on Intel Macs use `pip install --only-binary=:all: -r backend/requirements.txt`
so pip does not try to compile grpcio from source.

Neo4j contract tests run when a server is available:
`NEO4J_TEST_URI=bolt://localhost:7687 NEO4J_TEST_PASSWORD=... make test`.

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
