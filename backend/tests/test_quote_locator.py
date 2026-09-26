import pytest

from app.schemas.documents import Chunk, PageSpan, ParsedDocument
from app.services.quote_locator import QuoteLocator, normalize_with_map


def chunk_with(doc, needle):
    return next(c for c in doc.chunks if needle in c.text)


def assert_traceable(doc, match):
    assert doc.text[match.char_start : match.char_end] == match.text
    chunk = next(c for c in doc.chunks if c.id == match.chunk_id)
    assert chunk.char_start <= match.char_start and match.char_end <= chunk.char_end
    assert match.page == doc.page_for_offset(match.char_start)
    assert match.section == chunk.section_title


def test_normalize_with_map_tracks_original_positions():
    text = "  The  “BERT” model\n uses ﬁne-tuning. "
    norm, index = normalize_with_map(text)
    assert norm == 'the "bert" model uses finetuning.'
    assert len(norm) == len(index)
    assert text[index[norm.index("uses")]] == "u"


def test_exact_match_in_cited_chunk(parsed_doc):
    quote = "Our study is limited to English-language computer science papers."
    chunk = chunk_with(parsed_doc, "Our study is limited")
    match = QuoteLocator(parsed_doc).locate(quote, chunk.id)
    assert match.method == "exact"
    assert match.chunk_id == chunk.id
    assert match.page == 3
    assert match.section == "4 Limitations"
    assert_traceable(parsed_doc, match)


def test_normalized_match_handles_whitespace_case_and_quotes(parsed_doc):
    # The PDF text wraps this sentence across lines; the LLM quotes it on one line.
    quote = "“A TWO-LAYER graph attention network then propagates information”"
    chunk = chunk_with(parsed_doc, "two-layer")
    match = QuoteLocator(parsed_doc).locate(quote, chunk.id)
    assert match.method == "normalized"
    assert match.text.lower().startswith("a two-layer graph")
    assert "\n" in match.text  # stored quote is the verbatim source, not the LLM's version
    assert_traceable(parsed_doc, match)


def test_wrong_or_missing_chunk_id_still_resolves_to_containing_chunk(parsed_doc):
    quote = "Graph structure improves citation intent classification on small datasets."
    wrong = parsed_doc.chunks[0].id
    for cited in (wrong, None, "chunk_does_not_exist"):
        match = QuoteLocator(parsed_doc).locate(quote, cited)
        assert match is not None
        assert match.chunk_id == chunk_with(parsed_doc, "Graph structure improves").id
        assert_traceable(parsed_doc, match)


def test_fuzzy_match_tolerates_small_slip_in_cited_chunk(parsed_doc):
    quote = "Our study is limitted to English language computer science papers."
    chunk = chunk_with(parsed_doc, "Our study is limited")
    match = QuoteLocator(parsed_doc).locate(quote, chunk.id)
    assert match.method == "fuzzy"
    assert match.score >= 92
    assert "limited" in match.text  # verbatim source text replaces the slip
    assert_traceable(parsed_doc, match)


@pytest.mark.parametrize(
    "quote",
    [
        "This sentence does not appear anywhere in the paper at all.",
        "Our study is limited ... computer science papers.",  # ellipsis = not verbatim
        "graph",  # too short to be meaningful evidence
        "",
    ],
)
def test_unlocatable_quotes_are_rejected(parsed_doc, quote):
    chunk = chunk_with(parsed_doc, "Our study is limited")
    assert QuoteLocator(parsed_doc).locate(quote, chunk.id) is None


def test_fuzzy_is_not_used_without_a_cited_chunk(parsed_doc):
    quote = "Our study is limitted to English language computer science papers."
    assert QuoteLocator(parsed_doc).locate(quote, None) is None


@pytest.mark.parametrize(
    ("a", "b"),
    [
        ("performs sur- prisingly well", "performs surprisingly well"),  # PDF line-break hyphen
        ("English-\nto-German", "English-to-German"),
        ("state\u2011of\u2011the\u2011art", "state-of-the-art"),  # non-breaking hyphens
    ],
)
def test_hyphenation_variants_normalize_equal(a, b):
    assert normalize_with_map(a)[0] == normalize_with_map(b)[0]


def _single_chunk_doc(text: str) -> ParsedDocument:
    return ParsedDocument(
        paper_id="paper_0123456789ab",
        file_name="x.pdf",
        parser="test",
        page_count=1,
        text=text,
        pages=[PageSpan(page_number=1, char_start=0, char_end=len(text))],
        chunks=[
            Chunk(
                id="chunk_a",
                paper_id="paper_0123456789ab",
                text=text,
                page=1,
                page_end=1,
                char_start=0,
                char_end=len(text),
            )
        ],
    )


def test_line_break_hyphen_in_source_still_matches():
    doc = _single_chunk_doc("Our model performs sur-\nprisingly well on parsing tasks.")
    match = QuoteLocator(doc).locate("Our model performs surprisingly well", "chunk_a")
    assert match is not None
    assert match.text == "Our model performs sur-\nprisingly well"


def test_match_never_starts_or_ends_on_whitespace():
    doc = _single_chunk_doc("Intro.\n  The key result holds.  \nMore.")
    locator = QuoteLocator(doc)
    start = doc.text.index("  The")
    end = doc.text.index("\nMore")
    match = locator._match(start, end, "fuzzy", 95.0, doc.chunks[0])
    assert match.text == "The key result holds."
    assert doc.text[match.char_start : match.char_end] == match.text
