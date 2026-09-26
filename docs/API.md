# API Documentation

Base URL: `http://127.0.0.1:8000`

## Health

```http
GET /health
```

Returns service status.

## Create Run

```http
POST /api/runs
Content-Type: multipart/form-data
```

Form field:

- `files`: exactly five PDF files.

Response:

```json
{
  "run_id": "string",
  "status": "complete",
  "progress": 100,
  "message": "Research Digital Twin built successfully.",
  "twin": {
    "papers": [],
    "nodes": [],
    "edges": [],
    "analysis": {},
    "research_gap": {}
  }
}
```

## Get Run

```http
GET /api/runs/{run_id}
```

Returns an in-memory run or loads the saved local artifact from `storage/runs/{run_id}.json`.

## Ask Burhan

```http
POST /api/runs/{run_id}/ask
Content-Type: application/json
```

Request:

```json
{
  "question": "What is the most effective method?"
}
```

Response:

```json
{
  "question": "What is the most effective method?",
  "answer": "string",
  "citations": ["Paper title"],
  "evidence": ["Evidence snippet"]
}
```
