"""cloro API provider.

cloro returns parsed results from the consumer interfaces of ChatGPT,
Google AI Mode and Gemini, and Google results with the AI Overview.
Docs: https://cloro.dev/docs?utm_source=searchstack-aeo&utm_medium=byok

Key from `config.cloro.api_key` (env CLORO_API_KEY).
"""

from __future__ import annotations

from typing import Any
from urllib.parse import urlparse

import requests

from searchstack.config import Config

API_BASE = "https://api.cloro.dev/v1/monitor"

# searchstack `ai` provider name -> cloro monitor endpoint.
ENGINES = {
    "cloro-chatgpt": "chatgpt",
    "cloro-aimode": "aimode",
    "cloro-gemini": "gemini",
}


def api_request(config: Config, endpoint: str, body: dict[str, Any]) -> dict[str, Any]:
    """POST to https://api.cloro.dev/v1/monitor/{endpoint}.

    Returns the `result` object, or {"error": str} on failure.
    """
    headers = {
        "Authorization": f"Bearer {config.cloro.api_key}",
        "Content-Type": "application/json",
    }
    try:
        resp = requests.post(f"{API_BASE}/{endpoint}", json=body, headers=headers, timeout=180)
    except requests.exceptions.RequestException as exc:
        return {"error": str(exc)}

    try:
        data = resp.json()
    except ValueError:
        return {"error": f"HTTP {resp.status_code}: {resp.text[:500]}"}

    if resp.status_code >= 400 or not data.get("success"):
        err = data.get("error") or {}
        code = err.get("code", "") if isinstance(err, dict) else ""
        msg = err.get("message", "") if isinstance(err, dict) else str(err)
        return {"error": f"HTTP {resp.status_code}: {code} {msg}".strip()}

    result = data.get("result")
    return result if isinstance(result, dict) else {"error": "no result data"}


def _host(url: str) -> str:
    return urlparse(url).netloc.lower().removeprefix("www.")


def _is_usable(url: str) -> bool:
    """Skip empty links and Google redirect links (google.com/goto)."""
    if not url:
        return False
    parsed = urlparse(url)
    return not (parsed.netloc.endswith("google.com") and parsed.path.startswith("/goto"))


def google_search(*, keyword: str, config: Config) -> dict[str, Any]:
    """Google results with the AI Overview (7 credits)."""
    body = {
        "query": keyword,
        "country": config.cloro.country,
        "include": {"aioverview": True},
    }
    return api_request(config, "google", body)


def parse_ai_overview(result: dict[str, Any], domain: str) -> dict[str, Any]:
    """Same shape as geo._parse_ai_overview, from a cloro Google result."""
    aio = result.get("aioverview")
    aio = aio if isinstance(aio, dict) else {}
    cited_domains: list[str] = []
    cites_us = False
    for src in aio.get("sources") or []:
        url = src.get("url", "")
        if not _is_usable(url):
            continue
        ref_domain = _host(url)
        cited_domains.append(ref_domain)
        if domain in ref_domain or domain in url:
            cites_us = True
    return {"ai_present": bool(aio), "cites_us": cites_us, "cited_domains": cited_domains}


def parse_organic(result: dict[str, Any], domain: str) -> dict[str, Any]:
    """Same shape as geo._parse_organic, from a cloro Google result."""
    position = None
    top_10: list[dict[str, Any]] = []
    for item in result.get("organicResults") or []:
        url = item.get("link", "")
        if not _is_usable(url):
            continue
        rank = item.get("position", 0)
        item_domain = _host(url)
        if rank <= 10:
            top_10.append({"rank": rank, "domain": item_domain, "url": url, "title": item.get("title", "")})
        if position is None and (domain in item_domain or domain in url):
            position = rank
    return {"position": position, "top_10": top_10}


def check_citation(config: Config, query_text: str, domain: str, *, engine: str) -> dict[str, object]:
    """Send a prompt to ChatGPT, AI Mode or Gemini through cloro; check whether *domain* is cited.

    *engine* is "chatgpt", "aimode" or "gemini".

    Returns:
        {"cited": bool, "text": str, "citations": list[str], "model": str, "error": str | None}
    """
    model = f"cloro/{engine}"
    result = api_request(config, engine, {"prompt": query_text, "country": config.cloro.country})
    if "error" in result:
        return {"cited": False, "text": "", "citations": [], "model": model, "error": result["error"]}

    text = result.get("text") or ""
    citations = [s.get("url", "") for s in result.get("sources") or [] if _is_usable(s.get("url", ""))]

    domain_lower = domain.lower()
    cited_in_citations = any(domain_lower in c.lower() for c in citations)
    cited_in_text = domain_lower in text.lower()

    return {
        "cited": cited_in_citations or cited_in_text,
        "text": text[:300],
        "citations": citations,
        "model": result.get("model") or model,
        "error": None,
    }
