"""Anthropic (Claude) citation-check provider.

Named anthropic_client.py to avoid conflict with the anthropic package.
All HTTP via urllib.request.
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
