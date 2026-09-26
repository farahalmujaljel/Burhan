"""Heuristic section detection over plain text.

Parser-independent: it only needs the document text, so any parser that does not provide
its own structure can reuse it. Headings are recognized when a short standalone line is
either a known scientific section name (optionally numbered) or a numbered title.
"""

import re
from collections.abc import Iterator

from app.schemas.documents import ParsedDocument, Section, SectionKind

# Priority order matters: "Limitations and Future Work" -> LIMITATIONS,
# "Conclusion and Future Work" -> CONCLUSION.
_KIND_KEYWORDS: list[tuple[SectionKind, str]] = [
    (SectionKind.ABSTRACT, r"abstract"),
    (SectionKind.INTRODUCTION, r"introduction"),
    (SectionKind.LIMITATIONS, r"limitations?|threats to validity"),
    (SectionKind.CONCLUSION, r"conclusions?|concluding remarks"),
    (SectionKind.FUTURE_WORK, r"future (work|directions|research)"),
    (SectionKind.RELATED_WORK, r"related work|background|literature review|prior work"),
    (SectionKind.RESULTS, r"results?"),
    (SectionKind.EXPERIMENTS, r"experiments?|experimental|evaluation"),
    (SectionKind.METHODS, r"methods?|methodology|approach|proposed|materials"),
    (SectionKind.DISCUSSION, r"discussion|analysis"),
    (SectionKind.ACKNOWLEDGMENTS, r"acknowledge?ments?"),
    (SectionKind.REFERENCES, r"references|bibliography"),
    (SectionKind.APPENDIX, r"appendix|appendices|supplementary"),
]
_KIND_RES = [(kind, re.compile(rf"\b({pat})\b", re.IGNORECASE)) for kind, pat in _KIND_KEYWORDS]

_NUMBERING = r"(?:\d{1,2}(?:\.\d{1,2}){0,2}\.?|[IVX]{1,6}\.)"

# A standalone line that is a known section name, optionally numbered.
_KNOWN_HEADING = re.compile(
    rf"^(?P<num>{_NUMBERING}\s+)?(?P<title>"
    r"abstract|introduction|related work|background|literature review|prior work|"
    r"methods?|methodology|approach|proposed (method|approach|framework)|materials and methods|"
    r"experiments?|experimental (setup|results|evaluation|design)|evaluation|"
    r"results?( and discussion)?|discussion|analysis|"
    r"limitations?( and future work)?|threats to validity|"
    r"future (work|directions|research)|"
    r"conclusions?( and future (work|directions))?|concluding remarks|"
    r"acknowledge?ments?|references|bibliography|appendix( [a-z])?|appendices|"
    r"supplementary material"
    r")\s*$",
    re.IGNORECASE,
)

# A numbered, title-like line: "3 Proposed Graph Encoder", "IV. EXPERIMENTS".
_NUMBERED_HEADING = re.compile(
    rf"^(?P<num>{_NUMBERING})\s+(?P<title>[A-Z][A-Za-z0-9 ,:&()'/\-]{{1,70}})$"
)

# "Abstract—We propose ..." / "Abstract: We ..." (heading inline with body text).
_INLINE_ABSTRACT = re.compile(r"^(?P<title>abstract)\s*[—–:.\-]\s*\S", re.IGNORECASE)

MAX_HEADING_WORDS = 10


def classify(title: str) -> SectionKind:
    for kind, pattern in _KIND_RES:
        if pattern.search(title):
            return kind
    return SectionKind.OTHER


def _lines(text: str) -> Iterator[tuple[int, str]]:
    offset = 0
    for line in text.splitlines(keepends=True):
        yield offset, line
        offset += len(line)


def _match_heading(line: str) -> tuple[str, str | None] | None:
    """Return (title, numbering) if the line looks like a section heading."""
    stripped = line.strip()
    if not 2 <= len(stripped) <= 80 or len(stripped.split()) > MAX_HEADING_WORDS:
        return None
    if m := _INLINE_ABSTRACT.match(stripped):
        return m.group("title"), None
    if m := _KNOWN_HEADING.match(stripped):
        return m.group("title"), (m.group("num") or "").strip() or None
    if m := _NUMBERED_HEADING.match(stripped):
        title = m.group("title").strip()
        letters = sum(c.isalpha() for c in title)
        if (
            letters >= 3
            and letters >= 0.6 * len(title.replace(" ", ""))
            and title[-1] not in ".,;:"
        ):
            return title, m.group("num")
    return None


def _is_subsection(numbering: str | None) -> bool:
    return bool(numbering) and bool(re.match(r"^\d+\.\d", numbering))


def detect_sections(doc: ParsedDocument) -> list[Section]:
    text = doc.text
    headings: list[tuple[int, str, SectionKind]] = []
    parent_kind = SectionKind.OTHER

    for offset, line in _lines(text):
        match = _match_heading(line)
        if not match:
            continue
        title, numbering = match
        start = offset + (len(line) - len(line.lstrip()))
        kind = classify(title)
        if _is_subsection(numbering) and kind == SectionKind.OTHER:
            kind = parent_kind  # "2.1 Datasets" inherits from "2 Methods"
        elif not _is_subsection(numbering):
            parent_kind = kind
        display = f"{numbering} {title}" if numbering else title
        headings.append((start, " ".join(display.split()), kind))

    if not headings:
        return [_section(doc, "Full Text", SectionKind.OTHER, 0, len(text))] if text.strip() else []

    sections: list[Section] = []
    first_start = headings[0][0]
    if text[:first_start].strip():
        sections.append(_section(doc, "Front Matter", SectionKind.FRONT_MATTER, 0, first_start))

    for i, (start, title, kind) in enumerate(headings):
        end = headings[i + 1][0] if i + 1 < len(headings) else len(text)
        if end > start:
            sections.append(_section(doc, title, kind, start, end))
    return sections


def _section(doc: ParsedDocument, title: str, kind: SectionKind, start: int, end: int) -> Section:
    return Section(
        title=title,
        kind=kind,
        page_start=doc.page_for_offset(start),
        char_start=start,
        char_end=end,
    )
