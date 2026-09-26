"""Generate small, realistic research-paper PDFs for tests (no binary fixtures in git)."""

import pymupdf

TITLE = "Graph Neural Networks for Citation Intent Classification"

INTRO = (
    "Citation intent classification assigns a purpose to each citation in a paper. "
    "Prior work relies on handcrafted features and sequence models. "
    "We argue that the citation graph carries complementary signal that text-only models ignore. "
    "In this paper we propose a graph neural network that combines citation context with graph "
    "structure. Our contributions are a new encoder, a benchmark study, and an error analysis."
)
METHOD = (
    "Our model encodes each citation context with a pretrained language model. "
    "A two-layer graph attention network then propagates information across the citation graph. "
    "The final representation is passed to a linear classifier trained with cross-entropy loss."
)
DATASETS = (
    "We evaluate on the ACL-ARC dataset and the SciCite dataset. "
    "ACL-ARC contains 1,941 citations and SciCite contains 11,020 citations."
)
RESULTS = (
    "Our model reaches a macro F1 of 0.71 on ACL-ARC, improving over the strongest baseline by "
    "3.2 points. On SciCite the model reaches 0.86 macro F1, matching prior results. "
    "Gains are largest for rare intent classes such as motivation and future work."
)
LIMITATIONS = (
    "Our study is limited to English-language computer science papers. "
    "The graph encoder requires the full citation graph, which is unavailable for new papers."
)
CONCLUSION = "Graph structure improves citation intent classification on small datasets."
REFERENCE = "[1] A. Smith and B. Jones. Citation function classification. ACL, 2019."

SAMPLE_PAGES: list[list[tuple[str, float]]] = [
    [
        (TITLE, 18),
        ("Alice Researcher, Bob Scientist", 10),
        ("Abstract", 12),
        ("We study citation intent classification with graph neural networks.", 10),
        ("1 Introduction", 12),
        (INTRO, 10),
    ],
    [
        ("2 Method", 12),
        (METHOD, 10),
        ("2.1 Datasets", 11),
        (DATASETS, 10),
        ("3 Results", 12),
        (RESULTS, 10),
    ],
    [
        ("4 Limitations", 12),
        (LIMITATIONS, 10),
        ("5 Conclusion", 12),
        (CONCLUSION, 10),
        ("References", 12),
        (REFERENCE, 9),
    ],
]


def make_pdf(
    pages: list[list[tuple[str, float]]] = SAMPLE_PAGES, *, metadata_title: str | None = None
) -> bytes:
    doc = pymupdf.open()
    for blocks in pages:
        page = doc.new_page()
        y = 72.0
        for text, size in blocks:
            rect = pymupdf.Rect(72, y, page.rect.width - 72, page.rect.height - 72)
            unused = page.insert_textbox(rect, text, fontsize=size)
            assert unused >= 0, "test PDF content overflowed the page"
            y += rect.height - unused + size
    if metadata_title:
        doc.set_metadata({"title": metadata_title})
    data = doc.tobytes()
    doc.close()
    return data


def make_image_only_pdf() -> bytes:
    """A PDF with graphics but no text layer, like a scanned paper."""
    doc = pymupdf.open()
    page = doc.new_page()
    page.draw_rect(pymupdf.Rect(100, 100, 300, 300), color=(0, 0, 0), fill=(0.5, 0.5, 0.5))
    data = doc.tobytes()
    doc.close()
    return data


def make_encrypted_pdf() -> bytes:
    doc = pymupdf.open(stream=make_pdf(), filetype="pdf")
    data = doc.tobytes(encryption=pymupdf.PDF_ENCRYPT_AES_256, user_pw="secret", owner_pw="owner")
    doc.close()
    return data


CORRUPTED_PDF = b"%PDF-1.7\n" + b"\x00garbage\xff" * 200
