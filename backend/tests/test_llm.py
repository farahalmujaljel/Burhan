import json
from types import SimpleNamespace

import groq
import httpx
import pytest

from app.core.config import Settings
from app.llm.base import ChatMessage, LLMNotConfiguredError, LLMOutputError, LLMProviderError
from app.llm.factory import create_llm_client
from app.llm.groq_client import GroqClient
from app.llm.prompts import render_prompt
from app.llm.structured import extract_json, generate_structured
from app.schemas.extraction import DraftVerificationBatch
from tests.fake_llm import FakeLLM

VALID = json.dumps({"results": [{"id": "a", "verdict": "supported", "confidence": 0.8}]})
MESSAGES = [ChatMessage("system", "Evidence Verification Agent"), ChatMessage("user", "x")]


# --- JSON parsing & structured generation -------------------------------------


@pytest.mark.parametrize(
    "text",
    [
        '{"a": 1}',
        '```json\n{"a": 1}\n```',
        'Sure! Here is the JSON:\n{"a": 1}\nHope this helps.',
    ],
)
def test_extract_json_tolerates_wrappers(text):
    assert extract_json(text) == {"a": 1}


def test_extract_json_rejects_non_json():
    with pytest.raises(json.JSONDecodeError):
        extract_json("no json here")


def test_structured_retries_then_succeeds():
    bad_schema = json.dumps({"results": [{"id": "a", "verdict": "maybe"}]})
    llm = FakeLLM(verification=["not json at all", bad_schema, VALID])
    result = generate_structured(llm, MESSAGES, DraftVerificationBatch, max_attempts=3)

    assert result.attempts == 3
    assert result.value.results[0].verdict == "supported"
    assert result.model == "fake-model"
    # The validation error is fed back to the model on retry.
    retry_prompt = llm.calls[2][-1].content
    assert "not valid" in retry_prompt and "verdict" in retry_prompt


def test_structured_gives_up_after_max_attempts():
    llm = FakeLLM(verification=["nope"] * 5)
    with pytest.raises(LLMOutputError, match="after 2 attempts"):
        generate_structured(llm, MESSAGES, DraftVerificationBatch, max_attempts=2)
    assert len(llm.calls) == 2


# --- Prompts ------------------------------------------------------------------


def test_prompts_render_from_files():
    assert "Knowledge Extraction Agent" in render_prompt("extraction_system")
    user = render_prompt("extraction_user", title="T", window_label="1 of 1", passages="P")
    assert "Paper: T" in user and "P" in user
    with pytest.raises(KeyError):
        render_prompt("extraction_user", title="T")


# --- Groq client & factory ----------------------------------------------------


class FakeCompletions:
    def __init__(self, fail_models=()):
        self.fail_models = set(fail_models)
        self.calls = []

    def create(self, **kwargs):
        self.calls.append(kwargs)
        if kwargs["model"] in self.fail_models:
            raise groq.APIError("model unavailable", httpx.Request("POST", "https://x"), body=None)
        message = SimpleNamespace(content='{"ok": true}')
        return SimpleNamespace(choices=[SimpleNamespace(message=message)], model=kwargs["model"])


def fake_sdk(completions):
    return SimpleNamespace(chat=SimpleNamespace(completions=completions))


def test_groq_client_sends_json_mode():
    completions = FakeCompletions()
    client = GroqClient(api_key="k", model="primary", sdk_client=fake_sdk(completions))
    resp = client.complete(MESSAGES, json_mode=True)
    assert resp.content == '{"ok": true}'
    assert resp.model == "primary"
    call = completions.calls[0]
    assert call["response_format"] == {"type": "json_object"}
    assert call["messages"][0] == {"role": "system", "content": "Evidence Verification Agent"}
    assert "reasoning_effort" not in call


def test_groq_client_passes_reasoning_effort_when_configured():
    completions = FakeCompletions()
    client = GroqClient(
        api_key="k", model="m", reasoning_effort="low", sdk_client=fake_sdk(completions)
    )
    client.complete(MESSAGES)
    assert completions.calls[0]["reasoning_effort"] == "low"


def test_groq_client_falls_back_to_second_model():
    completions = FakeCompletions(fail_models={"primary"})
    client = GroqClient(
        api_key="k", model="primary", fallback_model="backup", sdk_client=fake_sdk(completions)
    )
    assert client.complete(MESSAGES).model == "backup"


def test_groq_client_raises_provider_error_when_all_models_fail():
    completions = FakeCompletions(fail_models={"primary", "backup"})
    client = GroqClient(
        api_key="k", model="primary", fallback_model="backup", sdk_client=fake_sdk(completions)
    )
    with pytest.raises(LLMProviderError):
        client.complete(MESSAGES)


def test_factory_requires_api_key():
    with pytest.raises(LLMNotConfiguredError):
        create_llm_client(Settings(_env_file=None))
    client = create_llm_client(Settings(_env_file=None, groq_api_key="gsk_test"))
    assert isinstance(client, GroqClient)
    assert client.provider == "groq"
