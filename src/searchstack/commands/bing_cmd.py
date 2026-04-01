"""Bing Webmaster Tools -- URL submission, sitemap, quota, and query stats."""

from __future__ import annotations

import re
import urllib.request
from typing import Any

from searchstack.config import Config
from searchstack.providers.bing import bing_request, get_site_url


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
# Subcommands
# ---------------------------------------------------------------------------

def _cmd_submit(config: Config) -> None:
    """Submit all sitemap URLs to Bing via SubmitUrl."""
    if not config.sitemap:
        print("  No sitemap configured.")
        return

    urls = _fetch_sitemap_urls(config.sitemap)
    if not urls:
        print("  No URLs found in sitemap.")
        return

    site_url = get_site_url(config)
    print(f"  Submitting {len(urls)} URLs to Bing...\n")

    success = 0
    failed = 0

    for url in urls:
        result = bing_request(
            config,
            f"SubmitUrl?siteUrl={site_url}",
            method="POST",
            body={"siteUrl": site_url, "url": url},
        )

        if "error" in result:
            print(f"  \u274c {url} -- {result['error']}")
            failed += 1
        else:
            print(f"  \u2705 {url}")
            success += 1

    print(f"\n  Done: {success} submitted, {failed} failed\n")


def _cmd_sitemap(config: Config) -> None:
    """Submit sitemap URL to Bing via SubmitFeed."""
    if not config.sitemap:
        print("  No sitemap configured.")
        return

    site_url = get_site_url(config)
    print(f"  Submitting sitemap: {config.sitemap}\n")

    result = bing_request(
        config,
        f"SubmitFeed?siteUrl={site_url}",
        method="POST",
        body={"siteUrl": site_url, "feedUrl": config.sitemap},
    )

    if "error" in result:
        print(f"  \u274c Failed: {result['error']}")
    else:
        print(f"  \u2705 Sitemap submitted to Bing")

    print()


def _cmd_default(config: Config) -> None:
    """Show quota and top query stats."""
    site_url = get_site_url(config)

    # URL Submission Quota
    print(f"\n  Bing Webmaster -- {site_url}\n")
    print("  URL Submission Quota:")

    quota = bing_request(config, f"GetUrlSubmissionQuota?siteUrl={site_url}")
    if "error" in quota:
        print(f"    \u274c {quota['error']}")
    else:
        daily = quota.get("d", {})
        if isinstance(daily, dict):
            print(f"    Daily quota: {daily.get('DailyQuota', '?')}")
            print(f"    Monthly quota: {daily.get('MonthlyQuota', '?')}")
        else:
            print(f"    {quota}")

    # Query Stats (top 10)
    print("\n  Top Search Queries:")

    stats = bing_request(config, f"GetQueryStats?siteUrl={site_url}")
    if "error" in stats:
        print(f"    \u274c {stats['error']}")
    else:
        items = stats.get("d", [])
        if isinstance(items, list) and items:
            kw_w = max(len(str(item.get("Query", ""))) for item in items[:10])
            kw_w = max(kw_w, 5)

            print(f"    {'Query':<{kw_w}}  {'Clicks':>7}  {'Impressions':>12}")
            print(f"    {'─' * kw_w}  {'─' * 7}  {'─' * 12}")

            for item in items[:10]:
                query = str(item.get("Query", ""))
                clicks = item.get("Clicks", 0)
                impressions = item.get("Impressions", 0)
                print(f"    {query:<{kw_w}}  {clicks:>7}  {impressions:>12}")
        elif isinstance(items, list):
            print("    No query data available.")
        else:
            print(f"    {stats}")

    print()


# ---------------------------------------------------------------------------
# Command entry point
# ---------------------------------------------------------------------------

def run(config: Config, *args: str) -> None:
    """Bing Webmaster Tools interface.

    Usage:
        searchstack bing              # show quota + query stats
        searchstack bing submit       # submit all sitemap URLs
        searchstack bing sitemap      # submit sitemap feed
    """
    if not config.bing.api_key:
        print("  No Bing API key configured. Set [bing] api_key in .searchstack.toml")
        return

    subcmd = args[0] if args else ""

    if subcmd == "submit":
        _cmd_submit(config)
    elif subcmd == "sitemap":
        _cmd_sitemap(config)
    else:
        _cmd_default(config)
