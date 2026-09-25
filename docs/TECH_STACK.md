# Tech Stack

## Selection Principle

Burhan's stack is selected to support an Agentic AI Research Scientist that builds a living Research Digital Twin. Each technology exists to support extraction, orchestration, graph reasoning, evidence grounding, validation, or researcher-facing interaction.

| Layer | Technology | Rationale |
|---|---|---|
| LLM | GPT-5 preferred, GPT-4.1 fallback | Strong reasoning and structured extraction for scientific text |
| Embeddings | text-embedding-3-large | High-quality semantic retrieval for evidence passages |
| Agent framework | LangGraph | Explicit stateful orchestration for multi-agent workflows |
| Knowledge graph | Neo4j | Native graph representation for scientific entities and relationships |
| Vector database | Qdrant | Efficient similarity search for RAG evidence retrieval |
| Parser | Docling and PyMuPDF | Robust PDF parsing and text extraction paths |
| Validation | Pydantic | Strict schemas for extracted knowledge and API contracts |
| Backend | FastAPI | Python-native backend suited for AI workflows and rapid APIs |
| Frontend | Next.js | Modern interface for dashboards, graph exploration, and assistant UI |

## AI Models

### GPT-5 or GPT-4.1

The LLM is used for scientific text understanding, structured extraction, normalization, cross-paper reasoning, and explanation generation. GPT-5 is the preferred model because Burhan depends on strong reasoning and reliable instruction following. GPT-4.1 is an appropriate fallback for structured extraction and prototype development.

The model should be used with:

- schema-constrained outputs;
- explicit extraction targets;
- evidence preservation;
- validation and retry logic;
- no unsupported benchmark claims.

### text-embedding-3-large

Embeddings are used for evidence retrieval, not as the full intelligence layer. The vector store helps retrieve relevant passages when the Research Assistant needs to support an answer or when the verification agent checks a claim against source text.

## Agent Framework: LangGraph

LangGraph is recommended because Burhan's workflow is naturally multi-step and stateful. The system needs to pass validated research state from planning to extraction, verification, graph construction, and reasoning. LangGraph makes these transitions explicit and easier to inspect.

## Knowledge Graph: Neo4j

Neo4j fits Burhan because scientific knowledge is relational. A graph can represent how papers use methods, evaluate datasets, compare techniques, cite earlier work, improve prior methods, contradict findings, and suggest research gaps.

## Vector Database: Qdrant

Qdrant supports similarity search over embedded evidence chunks. It is used by the RAG subsystem to retrieve source passages and ground assistant responses.

## Parsing: Docling and PyMuPDF

Docling is recommended for richer document parsing and structure extraction. PyMuPDF is lightweight and practical for PDF text extraction in a prototype. Using both gives the project a path from quick MVP parsing to more reliable document processing.

## Validation: Pydantic

Pydantic defines the expected schema for papers, methods, datasets, metrics, findings, limitations, evidence, and relationships. This prevents unstructured LLM output from entering the Research Digital Twin without checks.

## Backend: FastAPI

FastAPI is well suited for Python AI systems. It can expose ingestion, extraction, graph update, and assistant endpoints while keeping the codebase accessible for a hackathon team.

## Frontend: Next.js

Next.js supports the researcher-facing experience: upload flow, dashboard, graph visualization, comparison views, gap cards, and grounded assistant responses.
