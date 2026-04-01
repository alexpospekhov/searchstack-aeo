"""Keyword gaps -- high-volume keywords where you rank poorly."""

from __future__ import annotations

from searchstack.config import Config
from searchstack.providers.dataforseo import (
    api_request,
    get_language_code,
    get_location_code,
)


def _check_configured(config: Config) -> bool:
    if not config.dataforseo.login or not config.dataforseo.password:
        print("❌ DataForSEO not configured. Set [dataforseo] in .searchstack.toml")
        return False
    return True


def run(config: Config, *args: str) -> None:
    """Find keywords with position > 10 and volume >= 50 (opportunity gaps)."""
    if not _check_configured(config):
        return

    target = config.domain
    if not target:
        print("Set domain in .searchstack.toml")
        return

    body = [
        {
            "target": target,
            "location_code": get_location_code(config),
            "language_code": get_language_code(config),
            "limit": 100,
        }
    ]

    data = api_request(config, "dataforseo_labs/google/ranked_keywords/live", body)

    if "error" in data:
        print(f"API error: {data['error']}")
        return

    tasks = data.get("tasks", [])
    if not tasks or not tasks[0].get("result"):
        print("No results returned.")
        return

    items = tasks[0]["result"][0].get("items", [])
    if not items:
        print(f"No ranked keywords for {target}.")
        return

    # Filter: position > 10 AND volume >= 50
    gaps: list[tuple[int, int, str, str]] = []
    for item in items:
        kw_data = item.get("keyword_data", {})
        info = kw_data.get("keyword_info", {})
        ranked = item.get("ranked_serp_element", {}) or {}
        serp_item = ranked.get("serp_item", {}) or {}

        position = serp_item.get("rank_absolute") or item.get("rank_absolute", 0)
        volume = info.get("search_volume") or 0
        keyword = kw_data.get("keyword", "")
        page = serp_item.get("url", serp_item.get("relative_url", ""))

        if position > 10 and volume >= 50:
            gaps.append((position, volume, keyword, page))

    if not gaps:
        print("No gaps found.")
        return

    gaps.sort(key=lambda r: r[1], reverse=True)
    gaps = gaps[:30]

    # Print table
    kw_width = max(len(r[2]) for r in gaps)
    kw_width = max(kw_width, 7)

    print(f"\nKeyword gaps for {target} (pos > 10, vol >= 50)")
    print(f"{'Pos':>5}  {'Volume':>8}  {'Keyword':<{kw_width}}  Page")
    print(f"{'─' * 5}  {'─' * 8}  {'─' * kw_width}  {'─' * 40}")

    for pos, vol, kw, page in gaps:
        page_display = page[:50] if page else ""
        print(f"{pos:>5}  {vol:>8,}  {kw:<{kw_width}}  {page_display}")

    print(f"\n{len(gaps)} gaps (showing top 30 by volume)")
