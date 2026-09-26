"""Parser interface. Implementations turn PDF bytes into page-aware text.

A parser returns a `ParsedDocument` with `text` and `pages` filled in. It may also return
`sections` if it understands document structure (e.g. Docling); otherwise the ingestion
service runs the heuristic sectioner. Chunking is always done downstream so every parser
produces chunks with identical provenance guarantees.
"""

from abc import ABC, abstractmethod

from app.schemas.documents import ParsedDocument

# Inserted between pages in ParsedDocument.text; never part of any page's span.
PAGE_SEPARATOR = "\n\n"


class DocumentParser(ABC):
    name: str

    @abstractmethod
    def parse(self, data: bytes, *, paper_id: str, file_name: str) -> ParsedDocument:
        """Parse PDF bytes. Raise `DocumentParsingError` for unreadable input."""
