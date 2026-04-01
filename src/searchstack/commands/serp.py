"""Live SERP top-10 via DataForSEO."""

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
    """Fetch live Google SERP top-10 for a query."""
    if not _check_configured(config):
        return

    query = " ".join(args) if args else ""
    if not query:
        print("Usage: searchstack serp \"query\"")
        return

    body = [
        {
            "keyword": query,
            "location_code": get_location_code(config),
            "language_code": get_language_code(config),
            "depth": 10,
            "device": "desktop",
        }
    ]

    data = api_request(config, "serp/google/organic/live/advanced", body)

    if "error" in data:
        print(f"API error: {data['error']}")
        return

    tasks = data.get("tasks", [])
    if not tasks or not tasks[0].get("result"):
        print("No results returned.")
        return

    items = tasks[0]["result"][0].get("items", [])
    if not items:
        print(f"No SERP results for \"{query}\".")
        return

    # Filter organic results only
    organic = [i for i in items if i.get("type") == "organic"]
    if not organic:
        print(f"No organic results for \"{query}\".")
        return

    own_domain = config.domain.lower().replace("www.", "")

    # Print table
    print(f"\nSERP top-10: \"{query}\"")
    print(f"{'#':>3}  {'Domain':<35}  Title")
    print(f"{'─' * 3}  {'─' * 35}  {'─' * 40}")

    for rank, item in enumerate(organic[:10], 1):
        domain = item.get("domain", "")
        title = item.get("title", "")[:60]
        marker = ""
        if own_domain and own_domain in domain.lower().replace("www.", ""):
            marker = " ← YOU"
        print(f"{rank:>3}  {domain:<35}  {title}{marker}")

    print()
