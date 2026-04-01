"""Competitor traffic estimation via DataForSEO."""

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
    """Estimate traffic for competitor domains (and your own)."""
    if not _check_configured(config):
        return

    # Build targets list from args, or fallback to config
    targets: list[str] = []
    if args:
        targets = list(args)
    else:
        if config.domain:
            targets.append(config.domain)
        targets.extend(config.competitors)

    if not targets:
        print("Usage: searchstack bulk domain1 domain2 ...")
        print("Or set domain + competitors in .searchstack.toml")
        return

    body = [
        {
            "targets": targets,
            "location_code": get_location_code(config),
            "language_code": get_language_code(config),
        }
    ]

    data = api_request(
        config, "dataforseo_labs/google/bulk_traffic_estimation/live", body
    )

    if "error" in data:
        print(f"API error: {data['error']}")
        return

    tasks = data.get("tasks", [])
    if not tasks or not tasks[0].get("result"):
        print("No results returned.")
        return

    items = tasks[0]["result"][0].get("items", [])
    if not items:
        print("No traffic data returned.")
        return

    # Build rows: domain, estimated traffic, keyword count
    rows: list[tuple[str, float, int]] = []
    for item in items:
        domain = item.get("target", "")
        metrics = item.get("metrics", {}) or {}
        organic = metrics.get("organic", {}) or {}
        traffic = organic.get("etv", 0) or 0
        keywords = organic.get("count", 0) or 0
        rows.append((domain, traffic, keywords))

    rows.sort(key=lambda r: r[1], reverse=True)

    # Print table
    dom_width = max((len(r[0]) for r in rows), default=6)
    dom_width = max(dom_width, 6)

    print(f"\nTraffic estimation")
    print(f"{'Domain':<{dom_width}}  {'Est. Traffic':>14}  {'Keywords':>10}")
    print(f"{'─' * dom_width}  {'─' * 14}  {'─' * 10}")

    for domain, traffic, keywords in rows:
        print(f"{domain:<{dom_width}}  {traffic:>14,.0f}  {keywords:>10,}")

    print()
