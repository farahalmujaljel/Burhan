# Setup

## Prerequisites

- Python 3.11+
- Node.js 20+
- Docker Desktop or Docker Engine
- Ollama running locally
- `llama3.2:3b` pulled in Ollama

## 1. Start Data Services

```bash
docker compose up -d
```

This starts PostgreSQL, Qdrant, and Neo4j.

## 2. Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload
```

Run Ollama locally:

```bash
ollama pull llama3.2:3b
ollama serve
```

The backend defaults to:

```env
LLM_BASE_URL=http://localhost:11434/v1
LLM_MODEL=llama3.2:3b
```

Docling is supported as the preferred parser when installed. PyMuPDF is included as the reliable fallback. To enable Docling in environments with compatible wheels, run:

```bash
pip install -r requirements-docling.txt
```

The backend exposes:

- API: `http://127.0.0.1:8000`
- OpenAPI docs: `http://127.0.0.1:8000/docs`

## 3. Frontend

```bash
cd frontend
npm install
cp .env.example .env.local
npm run dev
```

Open `http://localhost:3000`.

## Demo Flow

1. Upload exactly five PDF papers from one focused research domain.
2. Wait for parsing, extraction, storage, graph building, and reasoning.
3. Review AI Analysis.
4. Inspect Structured Extraction.
5. Explore the Knowledge Graph.
6. Review the Research Gap.
7. Ask: `What is the most effective method?`
