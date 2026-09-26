"""A scriptable fake LLM so tests never call Groq or spend tokens."""

import json
import re
from collections.abc import Callable, Iterable

from app.llm.base import ChatMessage, LLMClient, LLMResponse
from app.services.quote_locator import normalize_with_map

Handler = Callable[[list[ChatMessage]], str]

_HEADER = re.compile(r"^\[chunk_id=(?P<id>\S+) \| section=.*?\]$", re.MULTILINE)


def passages(messages: list[ChatMessage]) -> dict[str, str]:
    """Parse {chunk_id: text} from an extraction prompt."""
    user = next(m.content for m in messages if m.role == "user")
    matches = list(_HEADER.finditer(user))
    out = {}
    for i, m in enumerate(matches):
        end = matches[i + 1].start() if i + 1 < len(matches) else len(user)
        out[m.group("id")] = user[m.end() : end].strip()
    return out


def verification_items(messages: list[ChatMessage]) -> list[dict]:
    user = next(m.content for m in messages if m.role == "user")
    return [json.loads(line) for line in user.splitlines() if line.startswith("{")]


class FakeLLM(LLMClient):
    provider = "fake"

    def __init__(
        self,
        extraction: Handler | Iterable[str] | None = None,
        verification: Handler | Iterable[str] | None = None,
        model: str = "fake-model",
    ) -> None:
        self._extraction = self._handler(extraction or sample_extraction)
        self._verification = self._handler(verification or verdicts_by_claim())
        self.model = model
        self.calls: list[list[ChatMessage]] = []

    @staticmethod
    def _handler(source: Handler | Iterable[str]) -> Handler:
        if callable(source):
            return source
        replies = iter(source)
        return lambda _messages: next(replies)

    @property
    def extraction_calls(self) -> int:
        return sum("Knowledge Extraction Agent" in c[0].content for c in self.calls)

    @property
    def verification_calls(self) -> int:
        return sum("Evidence Verification Agent" in c[0].content for c in self.calls)

    def complete(self, messages, *, json_mode=False, temperature=None, max_tokens=None):
        self.calls.append(list(messages))
        handler = (
            self._extraction
            if "Knowledge Extraction Agent" in messages[0].content
            else self._verification
        )
        return LLMResponse(content=handler(messages), model=self.model)


def verdicts_by_claim(rules: dict[str, str] | None = None, default: str = "supported") -> Handler:
    """Verifier that returns `default`, or a verdict for claims containing a rule's key."""
    rules = rules or {}

    def handler(messages):
        results = []
        for item in verification_items(messages):
            verdict = next((v for k, v in rules.items() if k in item["claim"]), default)
            results.append(
                {"id": item["id"], "verdict": verdict, "confidence": 0.9, "reason": "fake"}
            )
        return json.dumps({"results": results})

    return handler


# Items the fake "model" extracts from the sample paper (tests/pdf_factory.py). Each item is
# only emitted when its quote is present in the current window, like a real model would.
SAMPLE_ITEMS = {
    "research_problem": {
        "text": "Assigning a purpose to each citation in a paper.",
        "quote": "Citation intent classification assigns a purpose to each citation in a paper.",
    },
    "methods": {
        "name": "Graph attention network",
        "role": "proposed",
        # different whitespace from the PDF text: exercises normalized matching
        "quote": "A two-layer graph attention network   then propagates information across the "
        "citation graph.",
    },
    "datasets": [
        {"name": "ACL-ARC", "quote": "We evaluate on the ACL-ARC dataset and the SciCite dataset."},
        {"name": "SciCite", "quote": "We evaluate on the ACL-ARC dataset and the SciCite dataset."},
    ],
    "metrics": {
        "name": "macro F1",
        "higher_is_better": True,
        "quote": "Our model reaches a macro F1 of 0.71 on ACL-ARC",
    },
    "results": {
        "metric": "macro F1",
        "value": "0.71",
        "method": "Graph attention network",
        "dataset": "ACL-ARC",
        "quote": "Our model reaches a macro F1 of 0.71 on ACL-ARC",
    },
    "findings": {
        "text": "Graph structure improves citation intent classification on small datasets.",
        "quote": "Graph structure improves citation intent classification on small datasets.",
    },
    "limitations": {
        "text": "The study only covers English-language computer science papers.",
        "quote": "Our study is limited to English-language computer science papers.",
    },
}

# Always emitted, always wrong: must be rejected during grounding.
HALLUCINATED_FUTURE_WORK = {
    "text": "Extend the model to multilingual corpora.",
    "confidence": 0.8,
    "evidence": [
        {
            "chunk_id": "chunk_000000000000",
            "quote": "We will extend the model to multilingual corpora in future work.",
        }
    ],
}
UNGROUNDED_FINDING = {"text": "The model is state of the art.", "confidence": 0.7, "evidence": []}


def _present(quote: str, texts: dict[str, str]) -> str | None:
    norm = normalize_with_map(quote)[0]
    return next((cid for cid, t in texts.items() if norm in normalize_with_map(t)[0]), None)


def sample_extraction(messages: list[ChatMessage]) -> str:
    texts = passages(messages)
    out: dict = {
        "research_questions": [],
        "methods": [],
        "datasets": [],
        "metrics": [],
        "results": [],
        "findings": [],
        "limitations": [],
        "future_work": [HALLUCINATED_FUTURE_WORK],
        "research_problem": None,
        "unexpected_key": "ignored",
    }
    out["findings"].append(UNGROUNDED_FINDING)

    for field, spec in SAMPLE_ITEMS.items():
        for item in spec if isinstance(spec, list) else [spec]:
            cid = _present(item["quote"], texts)
            if not cid:
                continue
            body = {k: v for k, v in item.items() if k != "quote"}
            body.update(confidence=0.9, evidence=[{"chunk_id": cid, "quote": item["quote"]}])
            if field == "research_problem":
                out[field] = body
            else:
                out[field].append(body)
    return json.dumps(out)


def sample_extraction_renamed(renames: dict[str, str]) -> Handler:
    """Like `sample_extraction`, but entity names are replaced (e.g. "ACL-ARC" -> "ACL ARC")."""

    def handler(messages):
        data = json.loads(sample_extraction(messages))
        for field in ("methods", "datasets", "metrics"):
            for item in data[field]:
                item["name"] = renames.get(item["name"], item["name"])
        for result in data["results"]:
            for key in ("metric", "method", "dataset"):
                if result.get(key):
                    result[key] = renames.get(result[key], result[key])
        return json.dumps(data)

    return handler
