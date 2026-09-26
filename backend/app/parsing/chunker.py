"""Section-aware chunking by character offsets.

Chunks never cross section boundaries and are always exact slices of the document text
(`doc.text[chunk.char_start:chunk.char_end] == chunk.text`), so every chunk, and any
evidence quote inside it, can be traced back to its page in the original PDF.
"""

import re

from app.schemas.documents import Chunk, ParsedDocument, Section, SectionKind

DEFAULT_EXCLUDED_KINDS = frozenset({SectionKind.REFERENCES})

_SENTENCE_END = re.compile(r"[.!?][\"')\]]?\s")


def _find_break(text: str, start: int, hard_end: int, min_len: int) -> int:
    """Best cut position in (start + min_len, hard_end]: paragraph > sentence > word."""
    lo = start + min_len
    para = text.rfind("\n\n", lo, hard_end)
    if para != -1:
        return para
    last_sentence = None
    for m in _SENTENCE_END.finditer(text, lo, hard_end):
        last_sentence = m
    if last_sentence:
        return last_sentence.start() + len(last_sentence.group().rstrip())
    for i in range(hard_end - 1, lo - 1, -1):
        if text[i].isspace():
            return i
    return hard_end


def _skip_space(text: str, pos: int, end: int) -> int:
    while pos < end and text[pos].isspace():
        pos += 1
    return pos


def _trim_end(text: str, start: int, end: int) -> int:
    while end > start and text[end - 1].isspace():
        end -= 1
    return end


def _chunk_section(doc: ParsedDocument, section: Section, size: int, overlap: int) -> list[Chunk]:
    text = doc.text
    sec_end = section.char_end
    chunks: list[Chunk] = []
    start = _skip_space(text, section.char_start, sec_end)

    while start < sec_end:
        hard_end = min(start + size, sec_end)
        end = hard_end if hard_end == sec_end else _find_break(text, start, hard_end, size // 2)
        end = _trim_end(text, start, end)
        if end <= start:  # only whitespace left
            break

        chunks.append(
            Chunk(
                paper_id=doc.paper_id,
                section_id=section.id,
                section_title=section.title,
                text=text[start:end],
                page=doc.page_for_offset(start),
                page_end=doc.page_for_offset(end - 1),
                char_start=start,
                char_end=end,
            )
        )
        if hard_end == sec_end:
            break

        # Step back by `overlap`, then realign to the next word so chunks start cleanly.
        next_start = max(end - overlap, start + 1)
        while next_start < end and not text[next_start - 1].isspace():
            next_start += 1
        start = _skip_space(text, next_start, sec_end)

    return chunks


def chunk_document(
    doc: ParsedDocument,
    *,
    size: int = 1200,
    overlap: int = 200,
    exclude_kinds: frozenset[SectionKind] = DEFAULT_EXCLUDED_KINDS,
) -> list[Chunk]:
    if overlap * 2 > size:
        raise ValueError("overlap must be at most half of size")
    return [
        chunk
        for section in doc.sections
        if section.kind not in exclude_kinds
        for chunk in _chunk_section(doc, section, size, overlap)
    ]
