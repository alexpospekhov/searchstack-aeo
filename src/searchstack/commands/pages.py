"""Indexing status check via Google Search Console URL Inspection API."""

from __future__ import annotations

import re
import urllib.request
from typing import Any
from urllib.parse import quote

from searchstack.config import Config
from searchstack.providers.gsc import gsc_request, get_gsc_site_url_encoded


_UA = "Mozilla/5.0 SearchStack/1.0"


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
# URL Inspection
# ---------------------------------------------------------------------------

def _inspect_url(config: Config, url: str) -> dict[str, Any]:
    """Inspect a single URL via GSC URL Inspection API."""
    body = {
        "inspectionUrl": url,
        "siteUrl": config.gsc.site_url,
    }

    result = gsc_request(
        config,
        "v1/urlInspection/index:inspect",
        method="POST",
        body=body,
    )

    if result is None:
        return {"url": url, "error": "No GSC token"}

    if "error" in result:
        return {"url": url, "error": result["error"]}

    inspection = result.get("inspectionResult", {})
    index_status = inspection.get("indexStatusResult", {})

    coverage_state = index_status.get("coverageState", "Unknown")
    verdict = index_status.get("verdict", "Unknown")
    last_crawl = index_status.get("lastCrawlTime", "")
    crawled_as = index_status.get("crawledAs", "")
    indexing_state = index_status.get("indexingState", "")

    return {
        "url": url,
        "coverage_state": coverage_state,
        "verdict": verdict,
        "last_crawl": last_crawl[:10] if last_crawl else "",
        "crawled_as": crawled_as,
        "indexing_state": indexing_state,
    }


def _verdict_icon(verdict: str) -> str:
    """Map verdict to status icon."""
    v = verdict.upper()
    if v == "PASS":
        return "\u2705"
    elif v in ("PARTIAL", "NEUTRAL"):
        return "\u26a0\ufe0f"
    else:
        return "\u274c"


# ---------------------------------------------------------------------------
# Command entry point
# ---------------------------------------------------------------------------

def _short_url(url: str, domain: str) -> str:
    for prefix in (f"https://{domain}", f"http://{domain}"):
        if url.startswith(prefix):
            path = url[len(prefix):]
            return path if path else "/"
    return url


def run(config: Config, *args: str) -> dict[str, Any] | None:
    """Check indexing status for all sitemap URLs via GSC URL Inspection API.

    Returns results dict (also used by report module).
    """
    if not config.sitemap:
        print("  No sitemap configured. Set sitemap = \"...\" in .searchstack.toml")
        return None

    if not config.gsc.site_url:
        print("  No GSC site_url configured. Set [gsc] site_url in .searchstack.toml")
        return None

    print(f"\n  Indexing Status Check")
    print(f"  Sitemap: {config.sitemap}\n")

    all_urls = _fetch_sitemap_urls(config.sitemap)
    if not all_urls:
        print("  No URLs found in sitemap.")
        return None

    print(f"  Inspecting {len(all_urls)} URLs...\n")

    results: list[dict[str, Any]] = []
    indexed = 0
    not_indexed = 0
    errors = 0

    for url in all_urls:
        result = _inspect_url(config, url)
        results.append(result)

        if "error" in result:
            errors += 1
            continue

        verdict = result.get("verdict", "")
        if verdict.upper() == "PASS":
            indexed += 1
        elif verdict.upper() in ("FAIL", "ERROR"):
            errors += 1
        else:
            not_indexed += 1

    # Print table
    page_w = max(len(_short_url(r["url"], config.domain)) for r in results)
    page_w = max(page_w, 4)
    page_w = min(page_w, 50)

    print(f"  {'':>3} {'URL':<{page_w}}  {'Coverage':<25}  {'Last Crawl':<12}")
    print(f"  {'':>3} {'─' * page_w}  {'─' * 25}  {'─' * 12}")

    for r in results:
        path = _short_url(r["url"], config.domain)
        if len(path) > page_w:
            path = path[:page_w - 2] + ".."

        if "error" in r:
            icon = "\u274c"
            coverage = f"Error: {r['error'][:20]}"
            crawl = ""
        else:
            icon = _verdict_icon(r.get("verdict", ""))
            coverage = r.get("coverage_state", "Unknown")
            crawl = r.get("last_crawl", "")

        print(f"  {icon:>3} {path:<{page_w}}  {coverage:<25}  {crawl:<12}")

    print(f"\n  Summary: \u2705 {indexed} indexed | \u26a0\ufe0f {not_indexed} not indexed | \u274c {errors} errors")
    print(f"  Total: {len(results)} URLs\n")

    return {
        "pages": results,
        "indexed": indexed,
        "not_indexed": not_indexed,
        "errors": errors,
        "total": len(results),
    }
