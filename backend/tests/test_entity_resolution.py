import pytest

from app.knowledge.entity_resolution import EntityResolver, base_key, canonical_id, loose_key
from app.schemas.entities import EntityType
from app.schemas.graph import GraphNode

D, M, MT = EntityType.DATASET, EntityType.METHOD, EntityType.METRIC


def test_keys():
    assert base_key("Multi‑Head  Attention") == "multi head attention"
    assert loose_key("WMT 2014 English-to-German") == "wmt 2014 english german"
    assert loose_key("Positional Encodings") == "positional encoding"
    assert loose_key("Loss") == "loss"  # "ss" endings are not plurals


@pytest.mark.parametrize(
    ("first", "second", "method"),
    [
        ("WMT 2014 English-German", "WMT 2014 English-to-German", "normalized"),
        ("Multi‑Head Attention", "multi-head attention", "exact"),
        ("Graph attention network", "Graph Attention Networks", "normalized"),
        ("Perplexity (PPL)", "Perplexity", "acronym"),
        ("Perplexity", "Perplexity (PPL)", "acronym"),
        ("Perplexity (PPL)", "PPL", "acronym"),
        ("BerkeleyParser corpus", "BerkleyParser corpus", "fuzzy"),
    ],
)
def test_high_confidence_variants_merge(first, second, method):
    r = EntityResolver([])
    a = r.resolve(D, first)
    b = r.resolve(D, second)
    assert b.canonical_id == a.canonical_id
    assert b.canonical_name == first  # the first-seen name stays canonical
    assert b.decision.method == method
    assert not b.is_new


@pytest.mark.parametrize(
    ("first", "second"),
    [
        ("WMT 2014 English-to-German", "WMT 2014 German-to-English"),  # direction matters
        ("Transformer", "Transformer (big)"),  # qualifiers are not dropped
        ("ResNet-50", "ResNet-101"),  # numbers must match, even for fuzzy
        ("WMT 2014 English-German", "WMT 2016 English-German"),
        ("Adam", "Adam optimizer"),
        ("BERT-base", "BERT-large"),
        ("Sinusoidal positional encoding", "Positional encoding (sinusoidal)"),  # word order
    ],
)
def test_distinct_entities_are_not_merged(first, second):
    r = EntityResolver([])
    assert r.resolve(M, first).canonical_id != r.resolve(M, second).canonical_id


def test_same_name_different_types_stay_separate():
    r = EntityResolver([])
    assert r.resolve(M, "ImageNet").canonical_id != r.resolve(D, "ImageNet").canonical_id


def test_near_misses_are_reported_not_merged():
    r = EntityResolver([])
    r.resolve(M, "Sinusoidal positional encoding")
    b = r.resolve(M, "Positional encoding (sinusoidal)")
    assert b.is_new
    [dup] = r.possible_duplicates
    assert dup.candidate_name == "Sinusoidal positional encoding"
    assert dup.score >= 85


def test_resolves_against_existing_graph_nodes_and_aliases():
    existing = GraphNode(
        id="dataset_abc", type=D, name="SQuAD 2.0", aliases=["Stanford Question Answering 2.0"]
    )
    r = EntityResolver([existing])
    assert r.resolve(D, "squad 2.0").canonical_id == "dataset_abc"
    assert r.resolve(D, "Stanford Question Answering 2.0").canonical_id == "dataset_abc"


def test_canonical_ids_are_deterministic():
    assert canonical_id(MT, "Macro F1") == canonical_id(MT, "macro-F1")
    assert canonical_id(MT, "Macro F1") != canonical_id(D, "Macro F1")
    assert canonical_id(MT, "BLEU").startswith("metric_")
