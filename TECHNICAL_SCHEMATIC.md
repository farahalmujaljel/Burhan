# Burhan — Technical Schematic

> **Agentic AI Research Scientist**
>
> Technical architecture and system workflow for Burhan's Research Digital Twin.

---

# System Overview

Burhan transforms unstructured scientific literature into a continuously evolving **Research Digital Twin (RDT)**.

Unlike traditional RAG systems, Burhan builds structured scientific knowledge that supports evidence-grounded reasoning across an entire research domain.

```mermaid
flowchart TB

    PDF[Scientific Papers]

    Parse[Document Parsing]

    Extract[Knowledge Extraction]

    Graph[Scientific Knowledge Graph]

    Twin[Research Digital Twin]

    Reason[Cross-Paper Reasoning]

    Assistant[Research Assistant]

    PDF --> Parse
    Parse --> Extract
    Extract --> Graph
    Graph --> Twin
    Twin --> Reason
    Reason --> Assistant
```

---

# Core Intelligence Layer

```mermaid
flowchart TB

    Twin[Research Digital Twin]

    KG[Knowledge Graph]
    VS[Vector Store]
    EV[Evidence Repository]

    Reason[Cross-Paper Reasoning Engine]

    Twin --> KG
    Twin --> VS
    Twin --> EV

    KG --> Reason
    VS --> Reason
    EV --> Reason
```

The Research Digital Twin is Burhan's persistent scientific memory.

It continuously evolves as new papers are uploaded.

---

# End-to-End Processing Pipeline

```mermaid
flowchart LR

    A[Scientific PDFs]

    B[Document Parsing<br/>Docling / PyMuPDF]

    C[Scientific Understanding Agent]

    D[Knowledge Extraction Agent]

    E[Evidence Validation]

    F[Scientific Knowledge Graph]

    G[Research Digital Twin]

    H[Cross-Paper Reasoning]

    I[Research Assistant]

    A --> B
    B --> C
    C --> D
    D --> E
    E --> F
    F --> G
    G --> H
    H --> I
```

---

# Multi-Agent Architecture

```mermaid
flowchart TD

    Planner[Research Planning Agent]

    Understanding[Scientific Understanding Agent]

    Extraction[Knowledge Extraction Agent]

    TwinBuilder[Research Twin Builder]

    Validation[Evidence Verification Agent]

    Reasoning[Cross-Paper Reasoning Agent]

    GapDiscovery[Research Gap Discovery Agent]

    Assistant[Research Assistant]

    Planner
        --> Understanding
        --> Extraction
        --> TwinBuilder
        --> Validation
        --> Reasoning
        --> GapDiscovery
        --> Assistant
```

---

# Scientific Knowledge Graph

```mermaid
graph LR

    Paper -->|USES| Method

    Paper -->|EVALUATES| Dataset

    Paper -->|REPORTS| Metric

    Paper -->|CLAIMS| Finding

    Finding -->|SUPPORTED BY| Evidence

    Finding -->|CONTRADICTS| Finding

    Method -->|IMPROVES| Method

    Method -->|COMPARES| Method

    Paper -->|CITES| Paper

    Limitation -->|SUGGESTS| ResearchGap

    Author -->|AUTHORED| Paper
```

---

# Scientific Entity Extraction

```mermaid
mindmap
  root((Scientific Entities))

    Papers

    Authors

    Methods

    Datasets

    Metrics

    Findings

    Evidence

    Limitations

    Future Work

    Research Gaps
```

---

# AI Methodology Stack

```mermaid
flowchart TB

    Agentic[Agentic AI]

    LLM[LLM Reasoning]

    Extraction[Scientific Information Extraction]

    Graph[Knowledge Graph]

    Verification[Evidence Verification]

    Reasoning[Cross-Paper Reasoning]

    Gap[Research Gap Detection]

    RAG[Evidence-Grounded RAG]

    Agentic --> LLM
    LLM --> Extraction
    Extraction --> Graph
    Graph --> Verification
    Verification --> Reasoning
    Reasoning --> Gap
    Gap --> RAG
```

---

# Storage Architecture

```mermaid
flowchart LR

    Papers[(Scientific PDFs)]

    Neo4j[(Neo4j)]

    Qdrant[(Qdrant)]

    Metadata[(Metadata)]

    Papers --> Neo4j

    Papers --> Qdrant

    Papers --> Metadata

    Neo4j --> Twin[Research Digital Twin]

    Qdrant --> Twin

    Metadata --> Twin
```

---

# Research Digital Twin Lifecycle

```mermaid
flowchart TD

    Upload[Upload Paper]

    Parse[Parse Document]

    Extract[Extract Scientific Knowledge]

    Validate[Validate Evidence]

    Graph[Update Knowledge Graph]

    Twin[Update Research Digital Twin]

    Compare[Cross-Paper Comparison]

    Discover[Discover Research Gaps]

    Upload --> Parse
    Parse --> Extract
    Extract --> Validate
    Validate --> Graph
    Graph --> Twin
    Twin --> Compare
    Compare --> Discover
```

---

# Research Intelligence Pipeline

```mermaid
flowchart LR

    Twin[Research Digital Twin]

    Methods[Method Comparison]

    Trends[Trend Detection]

    Evidence[Evidence Aggregation]

    Contradictions[Contradiction Detection]

    Gaps[Research Gap Discovery]

    Twin --> Methods

    Twin --> Trends

    Twin --> Evidence

    Twin --> Contradictions

    Twin --> Gaps
```

---

# Burhan Technology Stack

```mermaid
graph TD

    GPT[GPT-5]

    LangGraph[LangGraph]

    Docling[Docling]

    PyMuPDF[PyMuPDF]

    Neo4j[Neo4j]

    Qdrant[Qdrant]

    FastAPI[FastAPI]

    NextJS[Next.js]

    GPT --> LangGraph

    LangGraph --> FastAPI

    FastAPI --> Neo4j

    FastAPI --> Qdrant

    Docling --> FastAPI

    PyMuPDF --> FastAPI

    FastAPI --> NextJS
```

---

# Traditional RAG vs Burhan

```mermaid
flowchart LR

subgraph Traditional_RAG

PDF1[PDF]

Chunk[Chunks]

Embedding[Embeddings]

RAG[RAG]

Answer[Answer]

PDF1 --> Chunk --> Embedding --> RAG --> Answer

end

subgraph Burhan

PDF2[Research Papers]

Extract[Scientific Extraction]

KG[Knowledge Graph]

Twin[Research Digital Twin]

Reason[Cross-Paper Reasoning]

Assistant[Research Assistant]

PDF2 --> Extract --> KG --> Twin --> Reason --> Assistant

end
```

---

# Burhan's Innovation

Burhan is **not another Chat-with-PDF system**.

Its core innovation is the **Research Digital Twin**, a continuously evolving scientific intelligence layer that:

- models scientific entities
- stores explicit relationships
- validates evidence
- reasons across multiple papers
- discovers contradictions
- identifies recurring limitations
- detects research gaps
- powers evidence-grounded scientific assistance

The Retrieval-Augmented Generation (RAG) subsystem consumes the Digital Twin rather than replacing it.
