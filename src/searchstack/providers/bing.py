"""Bing Webmaster Tools API provider.

All HTTP via urllib.request.
"""

from __future__ import annotations

import json
import urllib.request
import urllib.error
from typing import Any

from searchstack.config import Config

BASE = "https://ssl.bing.com/webmaster/api.svc/json"


def bing_request(
    config: Config,
    endpoint: str,
    method: str = "GET",
    body: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Make a Bing Webmaster API request.

    Appends the apikey query parameter automatically.
    Returns parsed JSON on success, or {"error": str} on failure.
    """
    sep = "&" if "?" in endpoint else "?"
    url = f"{BASE}/{endpoint.lstrip('/')}{sep}apikey={config.bing.api_key}"

    data = json.dumps(body).encode() if body else None
    headers = {"Content-Type": "application/json"}
    req = urllib.request.Request(url, data=data, headers=headers, method=method)

    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read())  # type: ignore[no-any-return]
    except urllib.error.HTTPError as exc:
        return {"error": f"HTTP {exc.code}: {exc.reason}"}
    except Exception as exc:
        return {"error": str(exc)}


def get_site_url(config: Config) -> str:
    """Return the full site URL derived from the configured domain.

    Example: domain='example.com' -> 'https://example.com/'
    """
    domain = config.domain.rstrip("/")
    if not domain.startswith(("http://", "https://")):
        domain = f"https://{domain}"
    return f"{domain}/"


def get_inbound_links(config: Config) -> dict[str, Any]:
    """Fetch free inbound link counts from Bing Webmaster Tools."""
    site_url = get_site_url(config)
    endpoint = f"GetLinkCounts?siteUrl={urllib.request.quote(site_url, safe='')}"
    return bing_request(config, endpoint)


def get_query_stats(config: Config) -> dict[str, Any]:
    """Fetch organic queries, impressions, and clicks from Bing Webmaster Tools."""
    site_url = get_site_url(config)
    endpoint = f"GetQueryStats?siteUrl={urllib.request.quote(site_url, safe='')}"
    return bing_request(config, endpoint)


def get_keyword_stats(config: Config, keyword: str) -> dict[str, Any]:
    """Fetch free keyword search stats from Bing Webmaster Tools."""
    endpoint = f"GetKeywordStats?q={urllib.request.quote(keyword, safe='')}"
    return bing_request(config, endpoint)

