# AI Methodology

## Purpose

Burhan is an Agentic AI Research Scientist that builds and continuously evolves a Research Digital Twin. Its AI methodology is designed around one goal: transform research papers into structured, evidence-backed scientific understanding.

Burhan does not treat "LLM" as a complete technical explanation. The system combines agentic workflow control, LLM reasoning, scientific information extraction, graph representation, retrieval, validation, and cross-paper reasoning.

## Agentic AI

Agentic AI is used to decompose the research workflow into specialized steps. A single prompt can summarize a paper, but Burhan needs to plan, extract, verify, connect, reason, and update knowledge over time.

The agentic workflow separates responsibilities:

- Research Planning Agent decides the research scope and extraction objectives.
- Scientific Understanding Agent interprets paper structure and scientific context.
- Knowledge Extraction Agent converts text into structured entities and relationships.
- Research Twin Builder updates the Research Digital Twin.
- Evidence Verification Agent checks that claims remain grounded in source text.
- Cross-Paper Reasoning Agent compares findings, methods, datasets, and limitations.
- Research Gap Discovery Agent surfaces gaps supported by evidence.
- Research Assistant presents grounded answers to the researcher.

## Multi-Agent System

Burhan uses a multi-agent system because research intelligence requires multiple reasoning modes. Extraction, verification, graph construction, and gap detection should not be collapsed into one undifferentiated output.

The system can be implemented with LangGraph so each agent operates as a stateful node in a controlled workflow. This makes intermediate outputs inspectable, allows retries or human review, and keeps the architecture practical for a prototype.

## LLM Reasoning

Burhan uses LLM reasoning for tasks that require language understanding:

- identifying methods, datasets, metrics, findings, limitations, and future work;
- interpreting claims in scientific context;
- normalizing similar terms across papers;
- generating structured explanations for researchers.

Recommended model: GPT-5. If GPT-5 is unavailable, GPT-4.1 is the preferred fallback. The model should be called with strict extraction instructions and schema-constrained outputs rather than free-form summaries.

## Scientific Information Extraction

Scientific information extraction converts paper text into validated structured data.

Expected extracted entities include:

- Paper
- Method
- Dataset
- Metric
- Finding
- Limitation
- Research Gap
- Author

Each extracted claim should preserve evidence text, paper source, and section context where available. This keeps later reasoning traceable.

## Knowledge Graph

The Scientific Knowledge Graph represents the structure of the research field explicitly. A graph is used because scientific understanding is relational: papers use methods, methods evaluate datasets, findings contradict other findings, and limitations suggest research gaps.

Core relationships:

- USES
- EVALUATES
- COMPARES
- CITES
- IMPROVES
- CONTRADICTS
- SUGGESTS

Neo4j is recommended for the graph layer because it supports direct traversal of scientific relationships and can answer questions that are awkward in a flat document store.

## Retrieval-Augmented Generation

RAG is a supporting subsystem, not the product. Burhan uses retrieval to ground answers, retrieve evidence passages, and reduce unsupported generation.

Recommended embedding model: text-embedding-3-large. Recommended vector database: Qdrant.

RAG supports:

- evidence retrieval for extracted claims;
- grounded answers in the Research Assistant;
- source traceability during verification;
- fallback context when graph relationships alone are insufficient.

## Cross-Paper Reasoning

Cross-paper reasoning compares structured knowledge across multiple papers. It allows Burhan to answer questions such as:

- Which methods are evaluated on the same datasets?
- Which findings support or contradict one another?
- Which limitations repeat across independent studies?
- Which datasets dominate a domain?
- Which research directions are repeatedly suggested but unresolved?

This reasoning operates over the Research Digital Twin and Scientific Knowledge Graph, with RAG used to retrieve supporting evidence.

## Evidence Verification

Evidence verification checks whether generated insights are supported by source material. Burhan should not present a finding, contradiction, or research gap without a link back to extracted evidence.

Verification should include:

- schema validation with Pydantic;
- source paper references;
- evidence passage references;
- confidence labels for prototype outputs;
- human-review hooks for uncertain claims.

## Research Gap Detection

Research gap detection is based on structured signals, not unsupported speculation. Candidate gaps can come from:

- repeated limitations;
- unresolved contradictions;
- missing comparisons between methods and datasets;
- underexplored metrics;
- future work statements repeated across papers;
- weak evidence coverage for important claims.

The MVP can begin with rule-based aggregation over extracted limitations and future work. Later versions can add graph analytics and LLM-assisted gap ranking.

## Research Digital Twin

The Research Digital Twin is Burhan's evolving intelligence layer. It represents papers, methods, datasets, metrics, findings, limitations, future work, evidence, relationships, contradictions, gaps, and trends.

The twin evolves whenever new papers are uploaded. New papers can add entities, update relationships, confirm findings, introduce contradictions, or reveal new gaps.
