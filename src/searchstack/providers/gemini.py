"""Gemini (Google) AEO citation-check provider.

Mirrors what a real user sees in the Gemini chat: queries the current flagship
model **with Google Search grounding enabled** (`tools:[{google_search:{}}]`), so
Gemini actually retrieves live and returns real source citations in
`groundingMetadata.groundingChunks[].web.uri` — exactly the signal AEO needs.

Model verified live 2026-07-07: `gemini-3.5-flash` (newest available to the key;
resolved from the live `models` list, NOT hardcoded from memory). All HTTP via
urllib.request. Key from `config.gemini.api_key` (GSM `gemini-api-key`).
"""

from __future__ import annotations

import json
import urllib.request
import urllib.error

from searchstack.config import Config

API_BASE = "https://generativelanguage.googleapis.com/v1beta/models"
MODEL = "gemini-3.5-flash"


def check_citation(config: Config, query_text: str, domain: str) -> dict[str, object]:
    """Ask Gemini (with Search grounding) a query; check whether *domain* is cited.

    Returns:
        {"cited": bool, "text": str, "citations": list[str], "model": str, "error": str | None}
    """
    url = f"{API_BASE}/{MODEL}:generateContent?key={config.gemini.api_key}"
    payload = {
        "contents": [{"parts": [{"text": query_text}]}],
        "tools": [{"google_search": {}}],
    }
    data = json.dumps(payload).encode()
    req = urllib.request.Request(
        url, data=data, headers={"Content-Type": "application/json"}, method="POST"
    )

    try:
        with urllib.request.urlopen(req, timeout=90) as resp:
            result = json.loads(resp.read())

        candidate = (result.get("candidates") or [{}])[0]
        content = candidate.get("content", {}) if isinstance(candidate, dict) else {}
        parts = content.get("parts", []) if isinstance(content, dict) else []
        text = "".join(p.get("text", "") for p in parts if isinstance(p, dict) and "text" in p)

        # Real citations live in groundingMetadata (the retrieved web sources).
        citations: list[str] = []
        grounding = candidate.get("groundingMetadata", {}) if isinstance(candidate, dict) else {}
        for chunk in grounding.get("groundingChunks", []) or []:
            web = chunk.get("web", {}) if isinstance(chunk, dict) else {}
            uri = web.get("uri")
            if uri:
                citations.append(uri)

        search_queries = grounding.get("webSearchQueries", []) or []

        domain_lower = domain.lower()
        cited_in_citations = any(domain_lower in c.lower() for c in citations)
        cited_in_text = domain_lower in text.lower()

        return {
            "cited": cited_in_citations or cited_in_text,
            "text": text[:300],
            "citations": citations,
            "search_queries": search_queries,
            "model": MODEL,
            "error": None,
        }
    except urllib.error.HTTPError as exc:
        return {"cited": False, "text": "", "citations": [], "model": MODEL, "error": _http_err(exc)}
    except Exception as exc:
        return {"cited": False, "text": "", "citations": [], "model": MODEL, "error": str(exc)}


def _http_err(exc: urllib.error.HTTPError) -> str:
    """Surface the API's real error message (Gemini returns {"error":{"message":...}})."""
    try:
        body = json.loads(exc.read())
        msg = body.get("error", {}).get("message")
        if msg:
            return f"HTTP {exc.code}: {msg}"
    except Exception:
        pass
    return f"HTTP {exc.code}: {exc.reason}"
