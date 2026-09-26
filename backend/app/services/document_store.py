"""File-based storage for uploaded PDFs, ingestion records, and parsed documents.

Layout: <uploads_dir>/<paper_id>/{source.pdf, record.json, parsed.json}
Plain files keep the MVP dependency-free and make parsed output easy to inspect or cache.
"""

import os
import re
import tempfile
import threading
from pathlib import Path

from app.core.errors import NotFoundError
from app.schemas.common import new_id
from app.schemas.documents import PaperRecord, ParsedDocument

_PAPER_ID = re.compile(r"^paper_[0-9a-f]{12}$")


def _atomic_write(path: Path, data: bytes) -> None:
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=f".{path.name}.")
    try:
        with os.fdopen(fd, "wb") as fh:
            fh.write(data)
        os.replace(tmp, path)
    except BaseException:
        Path(tmp).unlink(missing_ok=True)
        raise


class DocumentStore:
    def __init__(self, root: Path) -> None:
        self.root = root
        self._lock = threading.Lock()

    def _dir(self, paper_id: str) -> Path:
        # Validating the ID format also prevents path traversal via the URL.
        if not _PAPER_ID.match(paper_id) or not (self.root / paper_id).is_dir():
            raise NotFoundError(f"Paper '{paper_id}' not found", details={"paper_id": paper_id})
        return self.root / paper_id

    def create(self, *, file_name: str, data: bytes, sha256: str) -> tuple[PaperRecord, bool]:
        """Store a new upload. Returns (record, created); identical files are deduplicated."""
        with self._lock:
            existing = self.find_by_sha256(sha256)
            if existing:
                return existing, False
            record = PaperRecord(
                paper_id=new_id("paper"), file_name=file_name, sha256=sha256, size_bytes=len(data)
            )
            paper_dir = self.root / record.paper_id
            paper_dir.mkdir(parents=True)
            _atomic_write(paper_dir / "source.pdf", data)
            self.save_record(record)
            return record, True

    def find_by_sha256(self, sha256: str) -> PaperRecord | None:
        return next((r for r in self.list_records() if r.sha256 == sha256), None)

    def list_records(self) -> list[PaperRecord]:
        if not self.root.is_dir():
            return []
        records = [
            PaperRecord.model_validate_json(p.read_text("utf-8"))
            for p in self.root.glob("paper_*/record.json")
        ]
        return sorted(records, key=lambda r: r.created_at)

    def get_record(self, paper_id: str) -> PaperRecord:
        return PaperRecord.model_validate_json(
            (self._dir(paper_id) / "record.json").read_text("utf-8")
        )

    def save_record(self, record: PaperRecord) -> None:
        path = self.root / record.paper_id / "record.json"
        _atomic_write(path, record.model_dump_json(indent=2).encode("utf-8"))

    def read_source(self, paper_id: str) -> bytes:
        return (self._dir(paper_id) / "source.pdf").read_bytes()

    def save_document(self, doc: ParsedDocument) -> None:
        path = self._dir(doc.paper_id) / "parsed.json"
        _atomic_write(path, doc.model_dump_json().encode("utf-8"))

    def delete_document(self, paper_id: str) -> None:
        (self._dir(paper_id) / "parsed.json").unlink(missing_ok=True)

    def get_document(self, paper_id: str) -> ParsedDocument:
        path = self._dir(paper_id) / "parsed.json"
        if not path.exists():
            raise NotFoundError(
                f"Paper '{paper_id}' has not been parsed", details={"paper_id": paper_id}
            )
        return ParsedDocument.model_validate_json(path.read_text("utf-8"))
