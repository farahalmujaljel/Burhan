"""PyMuPDF-based parser: fast, dependency-light, page-aware text extraction."""

import logging
import re

import pymupdf

from app.core.errors import DocumentParsingError
from app.parsing.base import PAGE_SEPARATOR, DocumentParser
from app.schemas.documents import PageSpan, ParsedDocument

logger = logging.getLogger(__name__)

# Keep whitespace, clip to the page, join words hyphenated across lines. Ligatures are
# deliberately NOT preserved so "ﬁ" becomes "fi" and quotes match plain text later.
TEXT_FLAGS = (
    pymupdf.TEXT_PRESERVE_WHITESPACE | pymupdf.TEXT_MEDIABOX_CLIP | pymupdf.TEXT_DEHYPHENATE
)

_JUNK_TITLES = re.compile(r"^(untitled|microsoft word|title|document\d*)\b", re.IGNORECASE)

pymupdf.TOOLS.mupdf_display_errors(False)  # corrupted files are reported via exceptions


def _clean_page_text(raw: str) -> str:
    text = raw.replace("\r\n", "\n").replace("\r", "\n").replace("\x00", "").replace("­", "")
    return text.rstrip()


class PyMuPDFParser(DocumentParser):
    name = "pymupdf"

    def parse(self, data: bytes, *, paper_id: str, file_name: str) -> ParsedDocument:
        try:
            doc = pymupdf.open(stream=data, filetype="pdf")
        except Exception as exc:
            raise DocumentParsingError(f"Could not open PDF: {exc}") from exc

        with doc:
            if doc.needs_pass:
                raise DocumentParsingError("PDF is password-protected")
            if doc.page_count == 0:
                raise DocumentParsingError("PDF has no pages")

            try:
                page_texts = [
                    _clean_page_text(page.get_text("text", flags=TEXT_FLAGS)) for page in doc
                ]
                title = self._title(doc)
            except Exception as exc:
                raise DocumentParsingError(f"Could not extract text: {exc}") from exc

            page_count = doc.page_count

        if not any(t.strip() for t in page_texts):
            raise DocumentParsingError(
                "PDF contains no extractable text (scanned PDFs need OCR, which is not supported)"
            )

        text_parts: list[str] = []
        pages: list[PageSpan] = []
        cursor = 0
        for number, page_text in enumerate(page_texts, start=1):
            if number > 1:
                text_parts.append(PAGE_SEPARATOR)
                cursor += len(PAGE_SEPARATOR)
            pages.append(
                PageSpan(page_number=number, char_start=cursor, char_end=cursor + len(page_text))
            )
            text_parts.append(page_text)
            cursor += len(page_text)

        return ParsedDocument(
            paper_id=paper_id,
            file_name=file_name,
            title=title,
            parser=self.name,
            page_count=page_count,
            text="".join(text_parts),
            pages=pages,
        )

    @staticmethod
    def _title(doc: pymupdf.Document) -> str | None:
        meta_title = (doc.metadata or {}).get("title", "").strip()
        if len(meta_title) > 3 and not _JUNK_TITLES.match(meta_title):
            return meta_title[:300]

        # Fall back to the largest-font line(s) on the first page.
        lines: list[tuple[float, str]] = []
        for block in doc[0].get_text("dict", flags=TEXT_FLAGS)["blocks"]:
            for line in block.get("lines", []):
                spans = [s for s in line["spans"] if s["text"].strip()]
                if spans:
                    size = max(s["size"] for s in spans)
                    lines.append((size, "".join(s["text"] for s in spans).strip()))
        if not lines:
            return None
        biggest = max(size for size, _ in lines)
        title = " ".join(t for size, t in lines if size >= biggest - 0.5)
        return title[:300] or None
