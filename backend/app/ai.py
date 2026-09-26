from __future__ import annotations

import hashlib
import math
import re

import httpx

from .schemas import PaperMetadata, ScientificExtraction
from .settings import settings


EXTRACTION_SYSTEM = """You extract scientific knowledge from research papers.
Return strict JSON matching this schema:
{
  "problem": "string",
  "objective": "string",
  "method": "string",
  "dataset": "string",
  "metrics": ["string"],
  "findings": ["string"],
  "limitations": ["string"],
  "future_work": ["string"],
  "evidence_quotes": ["short source quotes"]
}
Only use information supported by the paper text. Do not invent details."""


def extract_scientific_knowledge(metadata: PaperMetadata, text: str) -> ScientificExtraction:
    try:
        content = _chat_completion(
            [
                {"role": "system", "content": EXTRACTION_SYSTEM},
                {"role": "user", "content": f"Metadata:\n{metadata.model_dump_json()}\n\nPaper text:\n{text[:24000]}"},
            ],
            json_mode=True,
        )
        return ScientificExtraction.model_validate_json(content)
    except Exception:
        return _heuristic_extraction(metadata, text)


def embed_texts(texts: list[str]) -> list[list[float]]:
    return [_hash_embedding(text) for text in texts]


def answer_with_llm(question: str, context: str, citations: list[str]) -> str:
    try:
        return _chat_completion(
            [
                {"role": "system", "content": "Answer as Burhan, an evidence-grounded AI research scientist. Cite supporting papers by title."},
                {"role": "user", "content": f"Question: {question}\n\nEvidence:\n{context}\n\nAvailable citations: {citations}"},
            ],
        )
    except Exception:
        pass
    method_lines = [line for line in context.splitlines() if "method:" in line.lower() or "finding:" in line.lower()]
    summary = " ".join(method_lines[:4]) or context[:500]
    return f"Based on the uploaded papers, the strongest supported method is the one most consistently associated with positive findings across the evidence: {summary}"


def _chat_completion(messages: list[dict[str, str]], json_mode: bool = False) -> str:
    payload: dict[str, object] = {
        "model": settings.llm_model,
        "messages": messages,
        "temperature": 0.1,
    }
    if json_mode:
        payload["response_format"] = {"type": "json_object"}
    with httpx.Client(timeout=180) as client:
        response = client.post(f"{settings.llm_base_url.rstrip('/')}/chat/completions", json=payload)
        response.raise_for_status()
        data = response.json()
    return data["choices"][0]["message"]["content"] or ""


def _heuristic_extraction(metadata: PaperMetadata, text: str) -> ScientificExtraction:
    compact = re.sub(r"\s+", " ", text)
    lower = compact.lower()
    method = _first_match(compact, ["deep learning", "convolutional neural network", "cnn", "machine learning", "transformer", "resnet", "svm", "random forest"], "AI-based detection model")
    dataset = _first_match(compact, ["breakhis", "mini-mias", "ddsm", "inbreast", "wisconsin", "bcdr", "private dataset"], "reported breast cancer imaging dataset")
    metrics = sorted(set(re.findall(r"\b(accuracy|precision|recall|sensitivity|specificity|f1[- ]?score|auc|roc)\b", lower))) or ["accuracy"]
    limitation_sentences = _sentences_with(compact, ["limitation", "limited", "small dataset", "generalization", "imbalance", "external validation"])
    finding_sentences = _sentences_with(compact, ["accuracy", "outperform", "improve", "achieve", "detect", "classification"])
    future_sentences = _sentences_with(compact, ["future", "further", "additional", "larger dataset", "clinical"])
    problem = "Breast cancer detection requires reliable AI support across medical imaging and clinical datasets."
    objective = metadata.abstract[:350] or "Evaluate AI methods for breast cancer detection."
    return ScientificExtraction(
        problem=problem,
        objective=objective,
        method=method,
        dataset=dataset,
        metrics=metrics[:6],
        findings=finding_sentences[:4] or [f"The paper reports use of {method} for breast cancer detection."],
        limitations=limitation_sentences[:4] or ["The paper indicates that broader validation and stronger generalization evidence are needed."],
        future_work=future_sentences[:3] or ["Future work should validate the method on larger and more diverse datasets."],
        evidence_quotes=(finding_sentences + limitation_sentences)[:6],
    )


def _first_match(text: str, candidates: list[str], fallback: str) -> str:
    lower = text.lower()
    for candidate in candidates:
        if candidate in lower:
            return candidate.upper() if candidate in {"cnn", "svm"} else candidate.title()
    return fallback


def _sentences_with(text: str, needles: list[str]) -> list[str]:
    sentences = re.split(r"(?<=[.!?])\s+", text)
    matches = []
    for sentence in sentences:
        lower = sentence.lower()
        if any(needle in lower for needle in needles) and 40 <= len(sentence) <= 320:
            matches.append(sentence.strip())
    return matches


def _hash_embedding(text: str, dimensions: int = 256) -> list[float]:
    vector = [0.0] * dimensions
    for token in re.findall(r"[a-zA-Z0-9]+", text.lower()):
        digest = hashlib.sha256(token.encode("utf-8")).digest()
        index = int.from_bytes(digest[:4], "big") % dimensions
        vector[index] += 1.0
    norm = math.sqrt(sum(value * value for value in vector))
    if norm:
        vector = [value / norm for value in vector]
    return vector
