import pymupdf
import pytest

from app.core.errors import DocumentParsingError
from app.parsing.chunker import chunk_document
from app.parsing.pymupdf_parser import TEXT_FLAGS, PyMuPDFParser, _clean_page_text
from app.parsing.sectioner import classify, detect_sections
from app.schemas.documents import PageSpan, ParsedDocument, SectionKind
from tests.pdf_factory import (
    CORRUPTED_PDF,
    TITLE,
    make_encrypted_pdf,
    make_image_only_pdf,
    make_pdf,
)

PAPER_ID = "paper_000000000001"


def parse(data: bytes) -> ParsedDocument:
    return PyMuPDFParser().parse(data, paper_id=PAPER_ID, file_name="sample.pdf")


def plain_doc(text: str) -> ParsedDocument:
    return ParsedDocument(
        paper_id=PAPER_ID,
        file_name="x.pdf",
        parser="test",
        page_count=1,
        text=text,
        pages=[PageSpan(page_number=1, char_start=0, char_end=len(text))],
    )


# --- PyMuPDF parser -----------------------------------------------------------


def test_parser_extracts_pages_with_exact_offsets():
    data = make_pdf()
    doc = parse(data)
    assert doc.parser == "pymupdf"
    assert doc.page_count == 3
    assert [p.page_number for p in doc.pages] == [1, 2, 3]

    # Each page span must equal an independent re-extraction of that PDF page.
    with pymupdf.open(stream=data, filetype="pdf") as pdf:
        for span, page in zip(doc.pages, pdf, strict=True):
            expected = _clean_page_text(page.get_text("text", flags=TEXT_FLAGS))
            assert doc.text[span.char_start : span.char_end] == expected


def test_parser_maps_offsets_to_pages():
    doc = parse(make_pdf())
    assert doc.page_for_offset(doc.text.index("1 Introduction")) == 1
    assert doc.page_for_offset(doc.text.index("3 Results")) == 2
    assert doc.page_for_offset(doc.text.index("4 Limitations")) == 3


def test_parser_title_from_largest_font_when_metadata_missing():
    assert parse(make_pdf()).title == TITLE


def test_parser_title_ignores_rotated_margin_stamp():
    assert parse(make_pdf(arxiv_stamp=True)).title == TITLE


def test_parser_prefers_metadata_title():
    assert parse(make_pdf(metadata_title="A Metadata Title")).title == "A Metadata Title"


@pytest.mark.parametrize(
    ("data", "message"),
    [
        (CORRUPTED_PDF, None),
        (b"not a pdf at all", None),
        (make_encrypted_pdf(), "password"),
        (make_image_only_pdf(), "no extractable text"),
    ],
    ids=["corrupted", "garbage", "encrypted", "scanned"],
)
def test_parser_rejects_unreadable_pdfs(data, message):
    with pytest.raises(DocumentParsingError, match=message):
        parse(data)


# --- Section detection --------------------------------------------------------


def test_sections_detected_on_sample_paper():
    doc = parse(make_pdf())
    sections = detect_sections(doc)
    kinds = [s.kind for s in sections]
    assert kinds == [
        SectionKind.FRONT_MATTER,
        SectionKind.ABSTRACT,
        SectionKind.INTRODUCTION,
        SectionKind.METHODS,
        SectionKind.METHODS,  # "2.1 Datasets" inherits from "2 Method"
        SectionKind.RESULTS,
        SectionKind.LIMITATIONS,
        SectionKind.CONCLUSION,
        SectionKind.REFERENCES,
    ]
    assert sections[6].title == "4 Limitations"
    assert sections[6].page_start == 3
    # Sections tile the document with no gaps.
    assert sections[0].char_start == 0
    assert sections[-1].char_end == len(doc.text)
    for a, b in zip(sections, sections[1:], strict=False):
        assert a.char_end == b.char_start


@pytest.mark.parametrize(
    ("line", "title", "kind"),
    [
        ("I. INTRODUCTION", "I. INTRODUCTION", SectionKind.INTRODUCTION),
        ("Related Work", "Related Work", SectionKind.RELATED_WORK),
        ("6 Limitations and Future Work", "6 Limitations and Future Work", SectionKind.LIMITATIONS),
        ("Conclusions and Future Work", "Conclusions and Future Work", SectionKind.CONCLUSION),
        ("3.2 Experimental Setup", "3.2 Experimental Setup", SectionKind.EXPERIMENTS),
        ("4 Proposed Graph Encoder", "4 Proposed Graph Encoder", SectionKind.METHODS),
    ],
)
def test_heading_variants(line, title, kind):
    text = f"Some preamble text here.\n{line}\nBody text follows the heading."
    sections = detect_sections(plain_doc(text))
    assert sections[1].title == title
    assert sections[1].kind == kind


def test_section_number_on_its_own_line():
    # LaTeX PDFs often extract as "3\nModel Architecture".
    text = "Intro text.\n3\nModel Architecture\nBody.\n3.1\nEncoder Stacks\nMore body."
    sections = detect_sections(plain_doc(text))
    assert [s.title for s in sections] == [
        "Front Matter",
        "3 Model Architecture",
        "3.1 Encoder Stacks",
    ]
    assert sections[1].char_start == text.index("3\nModel")


def test_inline_abstract_heading():
    text = "Title\nAbstract—We propose a method.\n1 Introduction\nText."
    sections = detect_sections(plain_doc(text))
    assert [s.kind for s in sections] == [
        SectionKind.FRONT_MATTER,
        SectionKind.ABSTRACT,
        SectionKind.INTRODUCTION,
    ]


@pytest.mark.parametrize(
    "line",
    [
        "3 0.91 0.88 0.75",  # table row
        "1 We propose a novel method that outperforms every baseline we tried.",  # sentence
        "2 Results are shown below.",  # ends with a period
        "91.7\nTransformer (4 layers)",  # table value followed by a row label
    ],
)
def test_non_headings_are_ignored(line):
    sections = detect_sections(plain_doc(f"Intro text.\n{line}\nMore text."))
    assert len(sections) == 1
    assert sections[0].title == "Full Text"


def test_classify_unknown_title():
    assert classify("Graph Encoder") == SectionKind.OTHER


# --- Chunking -----------------------------------------------------------------


@pytest.fixture
def sectioned_doc() -> ParsedDocument:
    doc = parse(make_pdf())
    return doc.model_copy(update={"sections": detect_sections(doc)})


def test_chunks_are_exact_slices_within_sections(sectioned_doc):
    chunks = chunk_document(sectioned_doc, size=300, overlap=50)
    sections = {s.id: s for s in sectioned_doc.sections}
    assert chunks
    for c in chunks:
        assert sectioned_doc.text[c.char_start : c.char_end] == c.text
        assert c.text == c.text.strip()
        assert len(c.text) <= 300
        sec = sections[c.section_id]
        assert sec.char_start <= c.char_start < c.char_end <= sec.char_end
        assert c.section_title == sec.title
        assert c.page == sectioned_doc.page_for_offset(c.char_start)
        assert c.page_end == sectioned_doc.page_for_offset(c.char_end - 1)


def test_chunks_cover_all_non_whitespace_text(sectioned_doc):
    chunks = chunk_document(sectioned_doc, size=300, overlap=50)
    covered = set()
    for c in chunks:
        covered.update(range(c.char_start, c.char_end))
    for sec in sectioned_doc.sections:
        if sec.kind == SectionKind.REFERENCES:
            continue
        for i in range(sec.char_start, sec.char_end):
            if not sectioned_doc.text[i].isspace():
                assert i in covered, f"offset {i} not covered"


def test_long_sections_split_with_overlap(sectioned_doc):
    intro = [
        c
        for c in chunk_document(sectioned_doc, size=300, overlap=50)
        if c.section_title == "1 Introduction"
    ]
    assert len(intro) >= 2
    assert intro[1].char_start < intro[0].char_end  # overlap
    assert intro[1].char_start > intro[0].char_start  # progress


def test_references_excluded_by_default(sectioned_doc):
    titles = {c.section_title for c in chunk_document(sectioned_doc)}
    assert "References" not in titles
    assert "4 Limitations" in titles


def test_chunk_spanning_pages_records_both_pages():
    text = "First page text here.\n\nSecond page text here."
    doc = ParsedDocument(
        paper_id=PAPER_ID,
        file_name="x.pdf",
        parser="test",
        page_count=2,
        text=text,
        pages=[
            PageSpan(page_number=1, char_start=0, char_end=21),
            PageSpan(page_number=2, char_start=23, char_end=len(text)),
        ],
    )
    doc = doc.model_copy(update={"sections": detect_sections(doc)})
    [chunk] = chunk_document(doc)
    assert (chunk.page, chunk.page_end) == (1, 2)


def test_chunker_rejects_bad_overlap(sectioned_doc):
    with pytest.raises(ValueError):
        chunk_document(sectioned_doc, size=300, overlap=200)
