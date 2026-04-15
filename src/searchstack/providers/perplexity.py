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

        choice0 = result.get("choices", [{}])[0] if result.get("choices") else {}
        message = choice0.get("message", {}) if isinstance(choice0, dict) else {}
        text = message.get("content", "") if isinstance(message, dict) else ""

        # Citations can live in four different places depending on which
        # Perplexity-compatible backend answered the request:
        #   1. top-level `citations` (array of URL strings) — native
        #      Perplexity API on older Sonar models
        #   2. `choices[0].citations` — older passthrough wrappers
        #   3. `choices[0].message.citations` — some wrappers
        #   4. `choices[0].message.annotations[]` with
        #      `type == "url_citation"` and a nested
        #      `url_citation: {url, title, ...}` object — the current
        #      Perplexity annotation format (2026-04+), also used by
        #      OpenAI-compatible passthroughs such as OpenRouter
        # The original code only probed (1), so responses from backends
        # that returned (4) looked like they had zero citations when they
        # actually had 10+. We probe all four and concatenate.
        citations: list[str] = list(result.get("citations") or [])
        if isinstance(choice0, dict):
            citations.extend(choice0.get("citations") or [])
        if isinstance(message, dict):
            citations.extend(message.get("citations") or [])
            for ann in (message.get("annotations") or []):
                if isinstance(ann, dict) and ann.get("type") == "url_citation":
                    url_obj = ann.get("url_citation") or {}
                    if isinstance(url_obj, dict):
                        url = url_obj.get("url")
                        if url:
                            citations.append(url)

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
