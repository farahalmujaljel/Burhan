"""Prompt templates live as Markdown files next to this module.

Templates use `$name` placeholders (string.Template) so JSON examples with braces need no escaping.
Bump PROMPT_VERSION whenever a prompt changes; it is stored with every extraction for provenance.
"""

from functools import cache
from pathlib import Path
from string import Template

PROMPT_VERSION = "2026-09-26.1"
_DIR = Path(__file__).parent


@cache
def _template(name: str) -> Template:
    return Template((_DIR / f"{name}.md").read_text("utf-8"))


def render_prompt(name: str, **values: object) -> str:
    """Render a prompt; raises KeyError if a placeholder is missing."""
    return _template(name).substitute({k: str(v) for k, v in values.items()})
