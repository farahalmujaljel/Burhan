"""Conservative entity resolution for shared scientific concepts (Method, Dataset, Metric).

Two names are merged only when one of these high-precision rules holds:

  exact       identical after case/whitespace/punctuation/hyphen normalization
              ("Multi‑Head Attention" == "multi-head attention")
  normalized  identical after also dropping connector words (to, the, a, an) and a plural "s"
              on the last word ("WMT 2014 English-German" == "WMT 2014 English-to-German")
  acronym     one name is the other plus a trailing ALL-CAPS acronym in parentheses
              ("Perplexity (PPL)" == "Perplexity" == "PPL")
  fuzzy       ratio >= 95 on names of 10+ chars with identical numbers ("BerkleyParser" ~
              "BerkeleyParser"); numbers must match so "ResNet-50" never merges with "ResNet-101"

Word order is always significant ("English-to-German" never merges with "German-to-English"),
and qualifiers are never dropped ("Transformer (big)" stays separate from "Transformer").
Close-but-not-merged pairs are reported as possible duplicates for human review.
"""

import hashlib
import re
from dataclasses import dataclass, field

from rapidfuzz import fuzz

from app.schemas.entities import EntityType
from app.schemas.graph import GraphNode, PossibleDuplicate, ResolutionDecision
from app.services.quote_locator import CHAR_MAP

CONNECTORS = {"to", "the", "a", "an"}
FUZZY_MERGE = 95.0
FUZZY_MIN_CHARS = 10
REVIEW_THRESHOLD = 85.0

CONFIDENCE = {"exact": 1.0, "normalized": 0.95, "acronym": 0.9, "fuzzy": 0.9}

_TRAILING_ACRONYM = re.compile(r"^(?P<base>.+?)\s*\((?P<acro>[A-Z][A-Z0-9\-]{1,9})\)\s*$")
_PREFIX = {EntityType.METHOD: "method", EntityType.DATASET: "dataset", EntityType.METRIC: "metric"}


def base_key(name: str) -> str:
    """Case/punctuation/hyphen-insensitive key; word order preserved."""
    text = name.translate(CHAR_MAP).lower()
    text = re.sub(r"[^\w\s]|_", " ", text)
    return " ".join(text.split())


def loose_key(name: str) -> str:
    tokens = [t for t in base_key(name).split() if t not in CONNECTORS]
    if (
        tokens
        and len(tokens[-1]) > 3
        and tokens[-1].endswith("s")
        and not tokens[-1].endswith("ss")
    ):
        tokens[-1] = tokens[-1][:-1]
    return " ".join(tokens)


def _numbers(name: str) -> tuple[str, ...]:
    return tuple(re.findall(r"\d+", name))


def canonical_id(entity_type: EntityType, name: str) -> str:
    """Deterministic ID, so re-ingesting the same paper yields the same nodes."""
    digest = hashlib.sha1(f"{entity_type}:{loose_key(name)}".encode()).hexdigest()[:12]
    return f"{_PREFIX[entity_type]}_{digest}"


@dataclass
class _Canonical:
    id: str
    name: str
    exact: set[str] = field(default_factory=set)
    loose: set[str] = field(default_factory=set)
    acronyms: set[str] = field(default_factory=set)

    def add_name(self, name: str) -> None:
        self.exact.add(base_key(name))
        self.loose.add(loose_key(name))
        if m := _TRAILING_ACRONYM.match(name.strip()):
            self.acronyms.add(base_key(m.group("acro")))
            self.acronyms.add(loose_key(m.group("base")))


@dataclass
class Resolution:
    canonical_id: str
    canonical_name: str
    decision: ResolutionDecision
    is_new: bool


class EntityResolver:
    """Resolves names of one paper against canonical nodes already in the graph."""

    def __init__(self, existing: list[GraphNode]) -> None:
        self._by_type: dict[EntityType, list[_Canonical]] = {}
        self.possible_duplicates: list[PossibleDuplicate] = []
        for node in existing:
            canon = _Canonical(node.id, node.name)
            for n in [node.name, *node.aliases]:
                canon.add_name(n)
            self._by_type.setdefault(node.type, []).append(canon)

    def resolve(self, entity_type: EntityType, name: str) -> Resolution:
        candidates = self._by_type.setdefault(entity_type, [])
        match = self._match(entity_type, name, candidates)
        if match:
            canon, method = match
            canon.add_name(name)
            return self._resolution(entity_type, name, canon, method, is_new=False)

        canon = _Canonical(canonical_id(entity_type, name), name)
        canon.add_name(name)
        self._report_near_misses(entity_type, name, candidates)
        candidates.append(canon)
        return self._resolution(entity_type, name, canon, "new", is_new=True)

    def _match(
        self, entity_type: EntityType, name: str, candidates: list[_Canonical]
    ) -> tuple[_Canonical, str] | None:
        exact, loose = base_key(name), loose_key(name)
        acro = _TRAILING_ACRONYM.match(name.strip())
        acro_keys = {base_key(acro.group("acro")), loose_key(acro.group("base"))} if acro else set()

        for canon in candidates:
            if exact in canon.exact:
                return canon, "exact"
        for canon in candidates:
            if loose in canon.loose:
                return canon, "normalized"
        for canon in candidates:
            if exact in canon.acronyms or loose in canon.acronyms or acro_keys & canon.loose:
                return canon, "acronym"

        if len(exact) >= FUZZY_MIN_CHARS:
            best, best_score = None, 0.0
            for canon in candidates:
                if _numbers(canon.name) != _numbers(name):
                    continue
                score = fuzz.ratio(exact, base_key(canon.name))
                if score > best_score:
                    best, best_score = canon, score
            if best and best_score >= FUZZY_MERGE:
                return best, "fuzzy"
        return None

    def _report_near_misses(
        self, entity_type: EntityType, name: str, candidates: list[_Canonical]
    ) -> None:
        key = base_key(name)
        for canon in candidates:
            score = fuzz.token_sort_ratio(key, base_key(canon.name))
            if score >= REVIEW_THRESHOLD:
                self.possible_duplicates.append(
                    PossibleDuplicate(
                        entity_type=entity_type,
                        name=name,
                        candidate_id=canon.id,
                        candidate_name=canon.name,
                        score=round(score, 1),
                    )
                )

    @staticmethod
    def _resolution(
        entity_type: EntityType, name: str, canon: _Canonical, method: str, *, is_new: bool
    ) -> Resolution:
        decision = ResolutionDecision(
            entity_type=entity_type,
            original_name=name,
            canonical_id=canon.id,
            canonical_name=canon.name,
            method=method,
            confidence=1.0 if method == "new" else CONFIDENCE[method],
        )
        return Resolution(canon.id, canon.name, decision, is_new)
