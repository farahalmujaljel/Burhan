import pytest
from pydantic import ValidationError

from app.core.config import REPO_ROOT, Settings


def test_defaults_are_demo_safe():
    s = Settings(_env_file=None)
    assert s.graph_backend == "memory"
    assert s.vector_backend == "local"
    assert s.llm_provider == "groq"


def test_relative_data_dir_resolves_to_repo_root():
    s = Settings(_env_file=None)
    assert s.data_dir == REPO_ROOT / "data"
    assert s.uploads_dir == REPO_ROOT / "data" / "uploads"


def test_cors_origins_are_comma_separated():
    s = Settings(_env_file=None, cors_origins="http://a.com, http://b.com,")
    assert s.cors_origin_list == ["http://a.com", "http://b.com"]


def test_neo4j_backend_requires_password():
    with pytest.raises(ValidationError, match="NEO4J_PASSWORD"):
        Settings(_env_file=None, graph_backend="neo4j")
    assert Settings(_env_file=None, graph_backend="neo4j", neo4j_password="pw").graph_backend


def test_env_vars_override_defaults(monkeypatch):
    monkeypatch.setenv("LLM_MODEL", "some-other-model")
    monkeypatch.setenv("GROQ_API_KEY", "")  # empty values fall back to defaults
    s = Settings(_env_file=None)
    assert s.llm_model == "some-other-model"
    assert s.llm_configured is False
