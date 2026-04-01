"""Keyword suggestions via DataForSEO."""

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
    """Fetch keyword suggestions for a phrase (default: config.domain)."""
    if not _check_configured(config):
        return

    phrase = " ".join(args) if args else config.domain
    if not phrase:
        print("Usage: searchstack keywords \"phrase\"")
        return

    body = [
        {
            "keyword": phrase,
            "location_code": get_location_code(config),
            "language_code": get_language_code(config),
            "include_seed_keyword": True,
            "limit": 30,
        }
    ]

    data = api_request(config, "dataforseo_labs/google/keyword_suggestions/live", body)

    if "error" in data:
        print(f"API error: {data['error']}")
        return

    tasks = data.get("tasks", [])
    if not tasks or not tasks[0].get("result"):
        print("No results returned.")
        return

    items = tasks[0]["result"][0].get("items", [])
    if not items:
        print(f"No keyword suggestions for \"{phrase}\".")
        return

    # Extract keyword + volume, filter volume >= 10
    rows: list[tuple[int, str]] = []
    for item in items:
        kw_data = item.get("keyword_data", item)
        info = kw_data.get("keyword_info", {})
        volume = info.get("search_volume") or 0
        keyword = kw_data.get("keyword", item.get("keyword", ""))
        if volume >= 10:
            rows.append((volume, keyword))

    rows.sort(key=lambda r: r[0], reverse=True)

    if not rows:
        print(f"No keywords with volume >= 10 for \"{phrase}\".")
        return

    # Print table
    kw_width = max(len(r[1]) for r in rows)
    kw_width = max(kw_width, 7)  # minimum "Keyword" header

    print(f"\nKeyword suggestions for \"{phrase}\"")
    print(f"{'Volume':>8}  {'Keyword':<{kw_width}}")
    print(f"{'─' * 8}  {'─' * kw_width}")

    for volume, keyword in rows:
        print(f"{volume:>8,}  {keyword:<{kw_width}}")

    print(f"\n{len(rows)} keywords (volume >= 10)")
