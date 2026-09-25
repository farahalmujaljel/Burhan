# Architecture

## Overview

Burhan is an Agentic AI Research Scientist that builds a living Research Digital Twin from research papers. The architecture is organized around a grounded multi-agent pipeline.

```mermaid
flowchart TD
    A[Research Papers]
    B[Research Planning Agent]
    C[Scientific Understanding Agent]
    D[Knowledge Extraction Agent]
    E[Research Twin Builder]
    F[Evidence Verification Agent]
    G[Cross-Paper Reasoning Agent]
    H[Research Gap Discovery Agent]
    I[Research Assistant]

    A --> B --> C --> D --> E --> F --> G --> H --> I
```

## Layered System

```mermaid
flowchart TB
    subgraph Input
        A[Research Papers]
        B[Parsed Text and Sections]
    end

    subgraph AgenticLayer[Agentic AI Layer]
        C[Research Planning Agent]
        D[Scientific Understanding Agent]
        E[Knowledge Extraction Agent]
        F[Evidence Verification Agent]
        G[Cross-Paper Reasoning Agent]
        H[Research Gap Discovery Agent]
    end

    subgraph KnowledgeLayer[Knowledge Layer]
        I[(Scientific Knowledge Graph)]
        J[(Vector Evidence Store)]
        K[Validated Extraction Schemas]
    end

    subgraph TwinLayer[Research Digital Twin]
        L[Entity Memory]
        M[Relationship Model]
        N[Contradiction Map]
        O[Research Gap Map]
    end

    subgraph Experience
        P[Research Assistant]
        Q[Graph Visualization]
        R[Gap and Evidence Dashboard]
    end

    A --> B
    B --> C --> D --> E
    E --> K
    K --> I
    B --> J
    K --> F
    F --> L
    I --> M
    M --> G
    G --> N
    G --> H
    H --> O
    L --> P
    M --> Q
    N --> R
    O --> R
    J --> P
```

## Agent Responsibilities

| Agent | Responsibility | Output |
|---|---|---|
| Research Planning Agent | Defines the research scope and extraction priorities | Domain plan and extraction objectives |
| Scientific Understanding Agent | Interprets paper structure, sections, and scientific context | Section-aware paper representation |
| Knowledge Extraction Agent | Extracts scientific entities and relationships | Structured JSON validated by schema |
| Research Twin Builder | Merges extracted knowledge into the twin | Updated entities and graph relationships |
| Evidence Verification Agent | Checks that claims are grounded in source passages | Verified or flagged claims |
| Cross-Paper Reasoning Agent | Compares knowledge across papers | Comparisons, contradictions, and trends |
| Research Gap Discovery Agent | Converts limitations and missing links into candidate gaps | Evidence-backed research gaps |
| Research Assistant | Presents answers and explanations | Grounded research responses |

## Scientific Knowledge Graph Schema

```mermaid
graph LR
    Author -->|AUTHORED| Paper
    Paper -->|CITES| Paper
    Paper -->|USES| Method
    Paper -->|EVALUATES| Dataset
    Paper -->|REPORTS| Metric
    Paper -->|CLAIMS| Finding
    Paper -->|STATES| Limitation
    Method -->|COMPARES| Method
    Method -->|IMPROVES| Method
    Finding -->|CONTRADICTS| Finding
    Limitation -->|SUGGESTS| ResearchGap
```

Required node types:

- Paper
- Method
- Dataset
- Metric
- Finding
- Limitation
- Research Gap
- Author

Required relationship types:

- USES
- EVALUATES
- COMPARES
- CITES
- IMPROVES
- CONTRADICTS
- SUGGESTS

## Data Flow

```mermaid
sequenceDiagram
    participant Researcher
    participant UI as Next.js Interface
    participant API as FastAPI Backend
    participant Parser as Docling/PyMuPDF
    participant Agents as LangGraph Agents
    participant Graph as Neo4j
    participant Vector as Qdrant
    participant Twin as Research Digital Twin

    Researcher->>UI: Upload or select research papers
    UI->>API: Send paper files and domain context
    API->>Parser: Extract text, sections, and metadata
    Parser->>Agents: Provide structured document text
    Agents->>Agents: Extract, validate, and verify scientific knowledge
    Agents->>Graph: Store entities and relationships
    API->>Vector: Store evidence chunks and embeddings
    Graph->>Twin: Update domain knowledge structure
    Vector->>Twin: Provide evidence grounding
    Twin->>UI: Return comparisons, gaps, contradictions, and grounded answers
```

## RAG Boundary

RAG grounds the Research Assistant with evidence passages. It is not the main architecture. The primary intelligence layer is the Research Digital Twin, supported by the Scientific Knowledge Graph and cross-paper reasoning.

## Implementation Boundary

This documentation describes the intended architecture and recommended implementation direction. The current repository remains a prototype and should evolve incrementally without overclaiming finished capabilities.
