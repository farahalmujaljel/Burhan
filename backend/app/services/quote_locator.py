"""Deterministic evidence grounding: find an LLM-provided quote in the parsed document.

Search order (first hit wins):
  1. exact substring in the cited chunk
  2. normalized match (case, whitespace, quotes/dashes, ligatures) in the cited chunk
  3. normalized match in any other chunk (the LLM may cite the wrong chunk)
  4. high-threshold fuzzy match in the cited chunk (tolerates tiny transcription slips)

A match always resolves to exact character offsets in `ParsedDocument.text`, and the stored
evidence quote is replaced by that verbatim source slice, never the LLM's version.
"""

from dataclasses import dataclass
from typing import Literal

from rapidfuzz import fuzz

from app.schemas.documents import Chunk, ParsedDocument

MIN_QUOTE_CHARS = 8
MIN_FUZZY_QUOTE_CHARS = 30
FUZZY_THRESHOLD = 92.0

# Written as escapes on purpose: these characters are visually indistinguishable.
CHAR_MAP = str.maketrans(
    {
        "“": '"',  # left double quote
        "”": '"',  # right double quote
        "‘": "'",  # left single quote
        "’": "'",  # right single quote
        "‐": "-",  # hyphen
        "‑": "-",  # non-breaking hyphen
        "‒": "-",  # figure dash
        "–": "-",  # en dash
        "—": "-",  # em dash
        "−": "-",  # minus sign
        " ": " ",  # non-breaking space
        "ﬀ": "ff",
        "ﬁ": "fi",
        "ﬂ": "fl",
        "ﬃ": "ffi",
        "ﬄ": "ffl",
    }
)


@dataclass(frozen=True)
class QuoteMatch:
    char_start: int
    char_end: int
    text: str  # verbatim source slice
    chunk_id: str
    page: int | None
    section: str | None
    method: Literal["exact", "normalized", "fuzzy"]
    score: float  # 100 for exact/normalized


def normalize_with_map(text: str) -> tuple[str, list[int]]:
    """Normalize text and return, for each normalized char, its index in the original.

    Lowercases, collapses whitespace, unifies quotes/dashes/ligatures, and drops hyphens plus
    any whitespace after them, so "state-of-the-art", "state\u2011of\u2011the\u2011art" and a
    PDF line-break split like "sur- prisingly" all compare equal to their unhyphenated forms.
    """
    out: list[str] = []
    index: list[int] = []
    prev_space = True  # drops leading whitespace
    after_hyphen = False
    for i, ch in enumerate(text):
        for c in ch.translate(CHAR_MAP):
            if c == "-":
                after_hyphen = True
                continue
            if c.isspace():
                if prev_space or after_hyphen:
                    continue
                c, prev_space = " ", True
            else:
                prev_space = after_hyphen = False
            out.append(c.lower())
            index.append(i)
    while out and out[-1] == " ":
        out.pop()
        index.pop()
    return "".join(out), index


def _clean_quote(quote: str) -> str:
    return quote.strip().strip("\"'“”‘’").strip()


class QuoteLocator:
    def __init__(self, doc: ParsedDocument) -> None:
        self.doc = doc
        self._chunks = {c.id: c for c in doc.chunks}
        self._norm_cache: dict[str, tuple[str, list[int]]] = {}

    def locate(self, quote: str, chunk_id: str | None = None) -> QuoteMatch | None:
        quote = _clean_quote(quote)
        if len(quote) < MIN_QUOTE_CHARS or "..." in quote or "\u2026" in quote:
            return None
        norm_quote, _ = normalize_with_map(quote)
        cited = self._chunks.get(chunk_id) if chunk_id else None

        if cited and (idx := cited.text.find(quote)) != -1:
            start = cited.char_start + idx
            return self._match(start, start + len(quote), "exact", 100.0, cited)

        # Cited chunk first, then every other chunk (the LLM may cite the wrong one).
        ordered = ([cited] if cited else []) + [c for c in self.doc.chunks if c is not cited]
        for chunk in ordered:
            norm_text, index = self._norm(chunk)
            pos = norm_text.find(norm_quote)
            if pos != -1:
                start = chunk.char_start + index[pos]
                end = chunk.char_start + index[pos + len(norm_quote) - 1] + 1
                return self._match(start, end, "normalized", 100.0, chunk)

        if cited and len(norm_quote) >= MIN_FUZZY_QUOTE_CHARS:
            norm_text, index = self._norm(cited)
            aln = fuzz.partial_ratio_alignment(norm_quote, norm_text)
            if aln and aln.score >= FUZZY_THRESHOLD and aln.dest_end > aln.dest_start:
                start = cited.char_start + index[aln.dest_start]
                end = cited.char_start + index[aln.dest_end - 1] + 1
                return self._match(start, end, "fuzzy", round(aln.score, 1), cited)
        return None

    def _norm(self, chunk: Chunk) -> tuple[str, list[int]]:
        if chunk.id not in self._norm_cache:
            self._norm_cache[chunk.id] = normalize_with_map(chunk.text)
        return self._norm_cache[chunk.id]

    def _match(self, start: int, end: int, method: str, score: float, chunk: Chunk) -> QuoteMatch:
        # Never start/end on whitespace: evidence quotes are stored stripped and must still
        # equal text[char_start:char_end] exactly.
        text = self.doc.text
        while start < end and text[start].isspace():
            start += 1
        while end > start and text[end - 1].isspace():
            end -= 1
        return QuoteMatch(
            char_start=start,
            char_end=end,
            text=self.doc.text[start:end],
            chunk_id=chunk.id,
            page=self.doc.page_for_offset(start),
            section=chunk.section_title,
            method=method,
            score=score,
        )
