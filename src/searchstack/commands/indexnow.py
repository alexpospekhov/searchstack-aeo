"""IndexNow URL submission to Bing and Yandex."""

from __future__ import annotations

import json
import re
import urllib.request
import urllib.error
from typing import Any
from urllib.parse import urlparse

from searchstack.config import Config


_UA = "Mozilla/5.0 SearchStack/1.0"

ENDPOINTS = [
    "https://api.indexnow.org/indexnow",
    "https://yandex.com/indexnow",
]


# ---------------------------------------------------------------------------
# Sitemap
# ---------------------------------------------------------------------------

def _fetch_sitemap_urls(sitemap_url: str) -> list[str]:
    req = urllib.request.Request(sitemap_url, headers={"User-Agent": _UA})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            body = resp.read().decode("utf-8", errors="replace")
    except Exception as exc:
        print(f"  Failed to fetch sitemap: {exc}")
        return []

    if "<sitemapindex" in body:
        nested = re.findall(r"<loc>\s*(.*?)\s*</loc>", body)
        all_urls: list[str] = []
        for sub_url in nested:
            all_urls.extend(_fetch_sitemap_urls(sub_url))
        return all_urls

    return re.findall(r"<loc>\s*(.*?)\s*</loc>", body)


# ---------------------------------------------------------------------------
# IndexNow submission
# ---------------------------------------------------------------------------

def _submit_indexnow(
    endpoint: str,
    host: str,
    key: str,
    urls: list[str],
) -> dict[str, Any]:
    """Submit URLs to an IndexNow endpoint. Returns status dict."""
    payload = {
        "host": host,
        "key": key,
        "keyLocation": f"https://{host}/{key}.txt",
        "urlList": urls,
    }

    data = json.dumps(payload).encode()
    req = urllib.request.Request(
        endpoint,
        data=data,
        headers={
            "Content-Type": "application/json; charset=utf-8",
            "User-Agent": _UA,
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return {
                "endpoint": endpoint,
                "status": resp.status,
                "ok": True,
                "message": f"HTTP {resp.status} -- Accepted",
            }
    except urllib.error.HTTPError as exc:
        body = ""
        try:
            body = exc.read().decode("utf-8", errors="replace")[:200]
        except Exception:
            pass
        return {
            "endpoint": endpoint,
            "status": exc.code,
            "ok": False,
            "message": f"HTTP {exc.code}: {exc.reason}. {body}".strip(),
        }
    except Exception as exc:
        return {
            "endpoint": endpoint,
            "status": 0,
            "ok": False,
            "message": str(exc),
        }


# ---------------------------------------------------------------------------
# Command entry point
# ---------------------------------------------------------------------------

def run(config: Config, *args: str) -> dict[str, Any] | None:
    """Submit all sitemap URLs via IndexNow to Bing and Yandex.

    Returns results dict.
    """
    if not config.indexnow.key:
        print("  No IndexNow key configured. Set [indexnow] key = \"...\" in .searchstack.toml")
        return None

    if not config.sitemap:
        print("  No sitemap configured. Set sitemap = \"...\" in .searchstack.toml")
        return None

    print(f"\n  IndexNow Submission")
    print(f"  Sitemap: {config.sitemap}\n")

    urls = _fetch_sitemap_urls(config.sitemap)
    if not urls:
        print("  No URLs found in sitemap.")
        return None

    host = config.domain
    if not host and urls:
        parsed = urlparse(urls[0])
        host = parsed.netloc

    print(f"  Host: {host}")
    print(f"  Key: {config.indexnow.key[:8]}...")
    print(f"  URLs: {len(urls)}\n")

    # IndexNow allows up to 10,000 URLs per batch
    batch = urls[:10_000]
    results: list[dict[str, Any]] = []

    for endpoint in ENDPOINTS:
        result = _submit_indexnow(endpoint, host, config.indexnow.key, batch)
        results.append(result)

        icon = "\u2705" if result["ok"] else "\u274c"
        print(f"  {icon} {endpoint}")
        print(f"     {result['message']}")

    print(f"\n  Submitted {len(batch)} URLs to {len(ENDPOINTS)} endpoints\n")

    return {
        "host": host,
        "urls_count": len(batch),
        "endpoints": results,
    }
