"""Backlink profile via DataForSEO."""

from __future__ import annotations

from searchstack.config import Config
from searchstack.providers.dataforseo import api_request


def _check_configured(config: Config) -> bool:
    if not config.dataforseo.login or not config.dataforseo.password:
        print("❌ DataForSEO not configured. Set [dataforseo] in .searchstack.toml")
        return False
    return True


def run(config: Config, *args: str) -> None:
    """Show backlink summary and top referring domains."""
    if not _check_configured(config):
        return

    target = args[0] if args else config.domain
    if not target:
        print("Usage: searchstack backlinks [domain]")
        print("Or set domain in .searchstack.toml")
        return

    # --- 1. Backlink summary ---
    summary_body = [{"target": target}]
    summary_data = api_request(config, "backlinks/summary/live", summary_body)

    if "error" in summary_data:
        print(f"API error (summary): {summary_data['error']}")
        return

    summary_tasks = summary_data.get("tasks", [])
    summary_result = None
    if summary_tasks and summary_tasks[0].get("result"):
        summary_result = summary_tasks[0]["result"][0]

    if summary_result:
        total_backlinks = summary_result.get("total_backlinks", 0)
        referring_domains = summary_result.get("referring_domains", 0)
        domain_rank = summary_result.get("rank", 0)

        print(f"\nBacklink profile: {target}")
        print(f"  Total backlinks:    {total_backlinks:,}")
        print(f"  Referring domains:  {referring_domains:,}")
        print(f"  Domain rank:        {domain_rank}")
    else:
        print(f"\nNo backlink summary for {target}.")

    # --- 2. Top referring domains ---
    ref_body = [
        {
            "target": target,
            "limit": 20,
            "order_by": ["rank,desc"],
        }
    ]
    ref_data = api_request(config, "backlinks/referring_domains/live", ref_body)

    if "error" in ref_data:
        print(f"\nAPI error (referring domains): {ref_data['error']}")
        return

    ref_tasks = ref_data.get("tasks", [])
    items = []
    if ref_tasks and ref_tasks[0].get("result"):
        items = ref_tasks[0]["result"][0].get("items", [])

    if not items:
        print("\nNo referring domain data.")
        return

    # Build rows
    rows: list[tuple[str, int, int]] = []
    for item in items:
        domain = item.get("domain", "")
        backlinks = item.get("backlinks", 0)
        rank = item.get("rank", 0)
        rows.append((domain, backlinks, rank))

    rows.sort(key=lambda r: r[2], reverse=True)

    # Print table
    dom_width = max((len(r[0]) for r in rows), default=16)
    dom_width = max(dom_width, 16)

    print(f"\nTop referring domains")
    print(f"{'Referring Domain':<{dom_width}}  {'Backlinks':>10}  {'Rank':>6}")
    print(f"{'─' * dom_width}  {'─' * 10}  {'─' * 6}")

    for domain, backlinks, rank in rows:
        print(f"{domain:<{dom_width}}  {backlinks:>10,}  {rank:>6}")

    print()
