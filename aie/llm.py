"""
One function to talk to a language model, whichever provider runs it.

    from aie.llm import chat
    reply = chat([{"role": "user", "content": "Hello"}])
    print(reply["text"])

Providers: "ollama" (local, default) and "anthropic" (paid API; needs ANTHROPIC_API_KEY).
"""
from __future__ import annotations

import os
import time

import requests

DEFAULT_PROVIDER = os.environ.get("AIE_PROVIDER", "ollama")
DEFAULT_MODEL = os.environ.get("AIE_MODEL", "qwen3.5:4b")
OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434")
ANTHROPIC_URL = "https://api.anthropic.com/v1/messages"


class LLMError(Exception):
    """Raised when the model cannot be reached or answers with an error."""


def _post(url, payload, headers, timeout, retries):
    last = None
    for attempt in range(retries + 1):
        try:
            r = requests.post(url, json=payload, headers=headers, timeout=timeout)
            if r.status_code in (429, 500, 502, 503, 529):        # temporary errors: wait and retry
                last = LLMError(f"HTTP {r.status_code}: {r.text[:200]}")
                if attempt < retries:                                  # no wait after the last attempt
                    time.sleep(min(2 ** attempt, 8))
                continue
            if r.status_code != 200:
                raise LLMError(f"HTTP {r.status_code}: {r.text[:200]}")
            return r.json()
        except requests.exceptions.ConnectionError as err:
            last = LLMError(f"cannot reach {url}: {err}")
            if attempt < retries:
                time.sleep(min(2 ** attempt, 8))
        except requests.exceptions.Timeout:
            last = LLMError(f"no answer from {url} within {timeout} s")
    raise last


def chat(messages, model=None, provider=None, system=None, temperature=0.0, seed=42,
         max_tokens=1024, format=None, tools=None, timeout=300, retries=2):
    """Send a conversation to a model. Returns a dict with text, tool_calls, token counts and timing."""
    provider = provider or DEFAULT_PROVIDER
    model = model or DEFAULT_MODEL
    start = time.perf_counter()

    if provider == "ollama":
        msgs = ([{"role": "system", "content": system}] if system else []) + list(messages)
        payload = {"model": model, "messages": msgs, "stream": False,
                   "options": {"temperature": temperature, "num_predict": max_tokens}}
        if seed is not None:
            payload["options"]["seed"] = seed
        if format is not None:
            payload["format"] = format          # "json" or a JSON schema (dict)
        if tools is not None:
            payload["tools"] = tools
        out = _post(f"{OLLAMA_URL}/api/chat", payload, {}, timeout, retries)
        msg = out.get("message", {})
        result = {"text": msg.get("content", ""),
                  "tool_calls": [tc["function"] for tc in msg.get("tool_calls", []) or []],
                  "input_tokens": out.get("prompt_eval_count", 0),
                  "output_tokens": out.get("eval_count", 0)}
    elif provider == "anthropic":
        key = os.environ.get("ANTHROPIC_API_KEY")
        if not key:
            raise LLMError("set the ANTHROPIC_API_KEY environment variable")
        payload = {"model": model, "max_tokens": max_tokens, "messages": list(messages),
                   "temperature": temperature}
        if system:
            payload["system"] = system
        headers = {"x-api-key": key, "anthropic-version": "2023-06-01"}
        out = _post(ANTHROPIC_URL, payload, headers, timeout, retries)
        result = {"text": "".join(b.get("text", "") for b in out.get("content", []) if b.get("type") == "text"),
                  "tool_calls": [],
                  "input_tokens": out.get("usage", {}).get("input_tokens", 0),
                  "output_tokens": out.get("usage", {}).get("output_tokens", 0)}
    else:
        raise ValueError(f"unknown provider: {provider}")

    result.update(provider=provider, model=model, seconds=round(time.perf_counter() - start, 3))
    return result


def embed(texts, model="nomic-embed-text"):
    """Return one embedding vector per text, computed by Ollama."""
    out = _post(f"{OLLAMA_URL}/api/embed", {"model": model, "input": list(texts)}, {}, 300, 2)
    return out["embeddings"]
