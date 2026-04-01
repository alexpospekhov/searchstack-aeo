"""Perplexity citation-check provider.

Checks both the citations array and response text for domain presence.
All HTTP via urllib.request.
"""

from __future__ import annotations

import json
import urllib.request
import urllib.error

from searchstack.config import Config

API_URL = "https://api.perplexity.ai/chat/completions"
MODEL = "sonar"


def check_citation(config: Config, query_text: str, domain: str) -> dict[str, object]:
    """Ask Perplexity a query and check whether citations or text mention *domain*.

    Returns:
        {"cited": bool, "text": str, "citations": list[str], "model": str, "error": str | None}
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
        "Authorization": f"Bearer {config.perplexity.api_key}",
        "Content-Type": "application/json",
    }
    req = urllib.request.Request(API_URL, data=data, headers=headers, method="POST")

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            result = json.loads(resp.read())

        text = result["choices"][0]["message"]["content"]
        citations: list[str] = result.get("citations", [])
        domain_lower = domain.lower()

        cited_in_citations = any(domain_lower in c.lower() for c in citations)
        cited_in_text = domain_lower in text.lower()

        return {
            "cited": cited_in_citations or cited_in_text,
            "text": text[:300],
            "citations": citations,
            "model": MODEL,
            "error": None,
        }
    except urllib.error.HTTPError as exc:
        return {
            "cited": False,
            "text": "",
            "citations": [],
            "model": MODEL,
            "error": f"HTTP {exc.code}: {exc.reason}",
        }
    except Exception as exc:
        return {
            "cited": False,
            "text": "",
            "citations": [],
            "model": MODEL,
            "error": str(exc),
        }
