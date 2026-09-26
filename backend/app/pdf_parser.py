from __future__ import annotations

import re
from pathlib import Path

import pymupdf

from .schemas import PaperMetadata


def parse_pdf(path: Path) -> PaperMetadata:
    text = _parse_with_docling(path) or _parse_with_pymupdf(path)
    clean = re.sub(r"\s+", " ", text).strip()
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    title = lines[0][:240] if lines else path.stem
    abstract = _extract_between(clean, "abstract", ["introduction", "keywords"])[:1800]
    sections = _extract_sections(text)
    year = _extract_year(clean)
    authors = _extract_authors(lines)
    return PaperMetadata(title=title, authors=authors, year=year, abstract=abstract, sections=sections)


def full_text(path: Path) -> str:
    return _parse_with_docling(path) or _parse_with_pymupdf(path)


def _parse_with_docling(path: Path) -> str:
    try:
        from docling.document_converter import DocumentConverter

        result = DocumentConverter().convert(str(path))
        return result.document.export_to_markdown()
    except Exception:
        return ""


def _parse_with_pymupdf(path: Path) -> str:
    chunks: list[str] = []
    with pymupdf.open(path) as doc:
        for page in doc:
            chunks.append(page.get_text("text"))
    return "\n".join(chunks)


def _extract_between(text: str, start: str, end_markers: list[str]) -> str:
    lower = text.lower()
    start_index = lower.find(start)
    if start_index == -1:
        return text[:1200]
    content_start = start_index + len(start)
    end_index = len(text)
    for marker in end_markers:
        marker_index = lower.find(marker, content_start)
        if marker_index != -1:
            end_index = min(end_index, marker_index)
    return text[content_start:end_index].strip(" :-")


def _extract_sections(text: str) -> dict[str, str]:
    headings = ["abstract", "introduction", "method", "methodology", "materials", "results", "discussion", "conclusion", "limitations", "future work"]
    sections: dict[str, str] = {}
    lower = text.lower()
    positions = sorted((lower.find(h), h) for h in headings if lower.find(h) != -1)
    for index, (pos, heading) in enumerate(positions):
        end = positions[index + 1][0] if index + 1 < len(positions) else len(text)
        sections[heading.title()] = re.sub(r"\s+", " ", text[pos:end]).strip()[:4000]
    if not sections:
        sections["Full Text"] = re.sub(r"\s+", " ", text).strip()[:8000]
    return sections


def _extract_year(text: str) -> int | None:
    match = re.search(r"\b(20[0-2][0-9]|19[8-9][0-9])\b", text)
    return int(match.group(1)) if match else None


def _extract_authors(lines: list[str]) -> list[str]:
    if len(lines) < 2:
        return []
    candidate = lines[1]
    if len(candidate) > 240 or "abstract" in candidate.lower():
        return []
    parts = re.split(r",| and |\u2022|\|", candidate)
    return [part.strip() for part in parts if 2 < len(part.strip()) < 80][:12]
