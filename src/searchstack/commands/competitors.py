"""Ranked keywords + competitor overlap via DataForSEO."""

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
    """Show ranked keywords for the configured domain."""
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
            "limit": 30,
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

    # Build rows: position, volume, keyword, url
    rows: list[tuple[int, int, str, str]] = []
    for item in items:
        kw_data = item.get("keyword_data", {})
        info = kw_data.get("keyword_info", {})
        ranked = item.get("ranked_serp_element", {}) or {}
        serp_item = ranked.get("serp_item", {}) or {}

        position = serp_item.get("rank_absolute") or item.get("rank_absolute", 999)
        volume = info.get("search_volume") or 0
        keyword = kw_data.get("keyword", "")
        url = serp_item.get("url", serp_item.get("relative_url", ""))

        rows.append((position, volume, keyword, url))

    rows.sort(key=lambda r: r[0])

    # Print table
    kw_width = max((len(r[2]) for r in rows), default=7)
    kw_width = max(kw_width, 7)

    print(f"\nRanked keywords for {target}")
    print(f"{'Pos':>5}  {'Volume':>8}  {'Keyword':<{kw_width}}  URL")
    print(f"{'─' * 5}  {'─' * 8}  {'─' * kw_width}  {'─' * 40}")

    for pos, vol, kw, url in rows:
        # Truncate URL for display
        url_display = url[:50] if url else ""
        print(f"{pos:>5}  {vol:>8,}  {kw:<{kw_width}}  {url_display}")

    print(f"\n{len(rows)} keywords")
