"""Prompt templates stored as versioned text files in prompts/."""
import hashlib
from pathlib import Path

PROMPT_DIR = Path(__file__).resolve().parents[1] / "prompts"


def load_prompt(name):
    """Return (template_text, short_hash). The hash identifies the exact version in logs."""
    text = (PROMPT_DIR / f"{name}.txt").read_text(encoding="utf-8").rstrip("\n")
    return text, hashlib.sha256(text.encode()).hexdigest()[:10]


def render(template, **values):
    """Fill {placeholders}; fail loudly if one is missing."""
    missing = [k for k in _placeholders(template) if k not in values]
    if missing:
        raise KeyError(f"missing values for placeholders: {missing}")
    out = template
    for k, v in values.items():
        out = out.replace("{" + k + "}", str(v))
    return out


def _placeholders(template):
    import re
    return sorted(set(re.findall(r"\{([a-z_][a-z0-9_]*)\}", template)))
