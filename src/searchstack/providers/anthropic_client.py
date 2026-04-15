"""Anthropic (Claude) citation-check provider.

Named anthropic_client.py to avoid conflict with the anthropic package.
All HTTP via urllib.request.

Two routing paths:

  * Native: Anthropic Messages API (``/v1/messages``, ``x-api-key`` header,
    content-block response format).
  * OpenRouter: OpenAI-compatible Chat Completions (``/chat/completions``,
    Bearer auth, ``choices[0].message.content`` response format). Activated
    when ``config.openrouter.api_key`` is set. OpenRouter doesn't speak
    Anthropic's native Messages API — it exposes every model including
    Claude via standard OpenAI Chat Completions format — so the routed
    request needs a different payload shape and different response parsing
    than the native path.
"""

from __future__ import annotations

import json
import urllib.request
import urllib.error

from searchstack.config import Config

API_URL = "https://api.anthropic.com/v1/messages"
MODEL = "claude-haiku-4-5-20251001"
API_VERSION = "2023-06-01"


def check_citation(config: Config, query_text: str, domain: str) -> dict[str, object]:
    """Ask Claude a query and check whether the response mentions *domain*.

    Returns:
        {"cited": bool, "text": str, "model": str, "error": str | None}
    """
    if config.openrouter.api_key:
        return _check_via_openrouter(config, query_text, domain)

    payload = {
        "model": MODEL,
        "max_tokens": 500,
        "messages": [
            {"role": "user", "content": query_text},
        ],
    }
    data = json.dumps(payload).encode()
    headers = {
        "x-api-key": config.anthropic.api_key,
        "anthropic-version": API_VERSION,
        "Content-Type": "application/json",
    }
    req = urllib.request.Request(API_URL, data=data, headers=headers, method="POST")

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            result = json.loads(resp.read())

        # Anthropic returns content as a list of blocks
        text_blocks = [b["text"] for b in result.get("content", []) if b.get("type") == "text"]
        text = "\n".join(text_blocks)
        cited = domain.lower() in text.lower()

        return {
            "cited": cited,
            "text": text[:300],
            "model": MODEL,
            "error": None,
        }
    except urllib.error.HTTPError as exc:
        return {"cited": False, "text": "", "model": MODEL, "error": f"HTTP {exc.code}: {exc.reason}"}
    except Exception as exc:
        return {"cited": False, "text": "", "model": MODEL, "error": str(exc)}


def _check_via_openrouter(config: Config, query_text: str, domain: str) -> dict[str, object]:
    """Route Claude through OpenRouter's OpenAI-compatible endpoint.

    OpenRouter doesn't speak Anthropic's native Messages API — it exposes
    every model including Claude via standard OpenAI Chat Completions format.
    That means a different payload shape (``messages`` still works but
    system prompts and ``max_tokens`` placement match OpenAI conventions) and
    different response parsing (``choices[0].message.content`` instead of
    Anthropic's content-block list).
    """
    api_url = f"{config.openrouter.base_url.rstrip('/')}/chat/completions"
    model = config.openrouter.claude_model

    payload = {
        "model": model,
        "max_tokens": 500,
        "messages": [
            {"role": "user", "content": query_text},
        ],
    }
    data = json.dumps(payload).encode()
    headers = {
        "Authorization": f"Bearer {config.openrouter.api_key}",
        "Content-Type": "application/json",
    }
    req = urllib.request.Request(api_url, data=data, headers=headers, method="POST")

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            result = json.loads(resp.read())

        text = result["choices"][0]["message"]["content"]
        cited = domain.lower() in text.lower()
        return {
            "cited": cited,
            "text": text[:300],
            "model": model,
            "error": None,
        }
    except urllib.error.HTTPError as exc:
        return {"cited": False, "text": "", "model": model, "error": f"HTTP {exc.code}: {exc.reason}"}
    except Exception as exc:
        return {"cited": False, "text": "", "model": model, "error": str(exc)}
