<div align="center">

# 🧠 Burhan

### Evidence-Driven Research Intelligence through a Research Digital Twin

*"Transforming research papers into a living representation of scientific knowledge."*

![Status](https://img.shields.io/badge/Status-Prototype-orange)
![License](https://img.shields.io/badge/License-MIT-blue)
![Python](https://img.shields.io/badge/Python-3.11+-green)
![FastAPI](https://img.shields.io/badge/FastAPI-Backend-009688)
![Next.js](https://img.shields.io/badge/Next.js-Frontend-black)
![Neo4j](https://img.shields.io/badge/Neo4j-Knowledge_Graph-blue)

</div>

---

# 📖 What is Burhan?

**Burhan** is an AI-powered **Research Digital Twin** that transforms scientific papers into a structured, continuously evolving representation of a research domain.

Unlike traditional AI tools that retrieve information from PDFs, Burhan understands relationships between research papers and builds a living knowledge model that evolves as new papers are added.

Rather than asking:

> *"What does this paper say?"*

Burhan answers:

> *"What does the research field collectively know?"*

---

# 💡 Why "Burhan"?

**Burhan (بُرهان)** is an Arabic word meaning:

- Proof
- Evidence
- Conclusive Argument

Scientific progress is built on evidence—not isolated documents.

Burhan reflects our mission of transforming scattered research papers into **evidence-based research intelligence**.

---

# 🚨 The Problem

Researchers spend countless hours reading papers to answer questions like:

- Which methods perform best?
- Which datasets are most commonly used?
- What limitations appear repeatedly?
- What research gaps still exist?
- Which papers agree or contradict each other?

Current AI tools can search documents.

Very few can understand an entire research field.

---

# 🚀 Our Solution

Burhan converts research papers into a **Research Digital Twin**.

Instead of storing papers as documents, Burhan extracts structured scientific knowledge and connects it into an evolving representation of the domain.

Every uploaded paper enriches the Digital Twin.

This enables:

- Cross-paper reasoning
- Knowledge exploration
- Relationship discovery
- Evidence-backed research gap detection

---

# ✨ Features

- 📄 Multi-paper PDF upload
- 🤖 AI-powered knowledge extraction
- 🧠 Research Digital Twin generation
- 🌐 Knowledge Graph visualization
- 🔍 Cross-paper comparison
- 💬 Evidence-grounded AI Assistant
- 📊 Research trend exploration
- 🎯 Research gap identification
- 🔄 Automatic Digital Twin updates

---

# 🏗 System Workflow

```mermaid
flowchart LR

    A[📄 Research Papers]
    --> B[📑 PDF Parsing]

    B --> C[🧠 AI Knowledge Extraction]

    C --> D[📊 Structured Entities]

    D --> E[(Neo4j Knowledge Graph)]

    E --> F[🧬 Research Digital Twin]

    C --> G[(Vector Database)]

    G --> H[RAG Engine]

    F --> I[🌐 Relationship Visualization]

    I --> J[🤖 Research Intelligence]

    H --> J
```

---

# 🧬 Research Digital Twin

The Digital Twin models relationships between scientific entities instead of isolated documents.

```mermaid
graph LR

    Paper --> Method

    Paper --> Dataset

    Paper --> Metric

    Paper --> Finding

    Paper --> Limitation

    Paper --> Future_Work

    Method --> Research_Gap

    Dataset --> Finding

    Limitation --> Research_Gap

    Finding --> Evidence
```

---

# 🔄 Knowledge Extraction Pipeline

```mermaid
flowchart TD

    A[Research Papers]

    B[PDF Parsing]

    C[LLM Knowledge Extraction]

    D[Structured Knowledge]

    E[Knowledge Graph]

    F[Research Digital Twin]

    G[Research Intelligence Assistant]

    A --> B
    B --> C
    C --> D
    D --> E
    E --> F
    F --> G
```

---

# 🏛 System Architecture

```mermaid
flowchart TB

    subgraph Input
        A[Research Papers]
    end

    subgraph Processing
        B[PDF Parsing]
        C[AI Knowledge Extraction]
    end

    subgraph Knowledge Layer
        D[(Neo4j)]
        E[Research Digital Twin]
        F[(ChromaDB)]
    end

    subgraph Intelligence Layer
        G[Relationship Visualization]
        H[RAG Engine]
        I[Research Intelligence]
    end

    A --> B
    B --> C

    C --> D
    D --> E

    C --> F

    E --> G
    F --> H

    G --> I
    H --> I
```

---

# 👨‍🔬 Researcher Journey

```mermaid
journey
    title Researcher Experience

    section Build Knowledge

      Upload Research Papers: 5: Researcher

      AI Extracts Knowledge: 5: Burhan

      Build Research Digital Twin: 5: Burhan

    section Explore

      Visualize Relationships: 5: Researcher

      Compare Papers: 5: Researcher

      Discover Research Gaps: 5: Researcher

      Ask Scientific Questions: 5: Researcher
```

---

# 📊 Digital Twin Structure

Each uploaded paper contributes structured knowledge to the Digital Twin.

| Entity | Examples |
|----------|-----------|
| 📄 Paper | Research article |
| ⚙️ Method | CNN, Transformer, YOLO |
| 🗂 Dataset | COCO, ImageNet |
| 📏 Metric | Accuracy, F1-score |
| 📈 Finding | Experimental result |
| ⚠️ Limitation | Small dataset |
| 🚀 Future Work | Suggested improvements |
| 🎯 Research Gap | Missing comparison or unexplored direction |

---

# 🤖 Research Intelligence

Unlike traditional document retrieval systems, Burhan reasons over structured scientific knowledge.

Researchers can ask questions such as:

- Which datasets are used most frequently?
- Which methods consistently outperform others?
- What limitations recur across studies?
- Which findings contradict each other?
- Which research gaps are supported by evidence?
- Which papers use the same methodology?

---

# 🛠 Technology Stack

| Layer | Technology |
|---------|------------|
| Frontend | Next.js + React |
| Backend | FastAPI |
| AI Models | OpenAI GPT / Gemini |
| PDF Processing | PyMuPDF + Docling |
| Knowledge Graph | Neo4j |
| Vector Database | ChromaDB |
| Visualization | React Flow / Cytoscape.js |
| Embeddings | OpenAI / Gemini |

---

# 🎯 MVP Scope

The hackathon prototype focuses on a single research domain.

✅ Upload research papers

✅ Extract structured knowledge

✅ Build a Research Digital Twin

✅ Visualize relationships

✅ Compare papers

✅ Answer evidence-grounded questions

✅ Detect research gaps

---

# 🔮 Future Vision

Burhan is designed to evolve beyond a research assistant.

Future capabilities include:

- Integration with arXiv and Semantic Scholar
- Citation network analysis
- Research trend prediction
- Automatic literature reviews
- Multi-agent scientific reasoning
- Dynamic Digital Twin updates from newly published papers

---

# 🌟 What Makes Burhan Different?

| Traditional RAG | Burhan |
|-----------------|---------|
| Chat with PDFs | ✅ |
| Semantic Search | ✅ |
| Knowledge Graph | ✅ |
| Research Digital Twin | ✅ |
| Cross-paper Reasoning | ✅ |
| Automatic Domain Evolution | ✅ |
| Evidence-based Research Gaps | ✅ |
| Scientific Knowledge Representation | ✅ |

---

# 👥 Team

Developed for **Farq Hackathon**

**Imam Abdulrahman Bin Faisal University**

- Farah Almujaljel
- Aryam Bargash
- Alaa Bughararah
- Raneem Bahobail
- Batool Ashour

### Mentor

Dr. Muzammil

Assistant Professor of AI — KFUPM

Director — BRAIN Lab

---

# 📜 License

This project is licensed under the MIT License.

---

<div align="center">

### ⭐ Burhan

*"From research papers to research intelligence."*

</div>
