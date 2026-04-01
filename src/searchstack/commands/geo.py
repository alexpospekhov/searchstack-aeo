"""GEO -- Google AI Overview monitor.

Checks whether Google's AI Overview cites your domain for target keywords.
Uses DataForSEO SERP API with AI Overview extraction.
"""

from __future__ import annotations

from searchstack import snapshots
from searchstack.config import Config


def _parse_ai_overview(item: dict, domain: str) -> dict:
    """Extract citation info from a DataForSEO AI Overview result."""
    ai_overview = item.get("ai_overview") or {}
    ai_present = bool(ai_overview)

    cited_domains: list[str] = []
    cites_us = False

    # AI Overview items contain references with links
    for block in ai_overview.get("items", []):
        for ref in block.get("references", []):
            ref_domain = ref.get("domain", "")
            ref_url = ref.get("url", "")
            if ref_domain:
                cited_domains.append(ref_domain)
            if domain in ref_domain or domain in ref_url:
                cites_us = True

    return {
        "ai_present": ai_present,
        "cites_us": cites_us,
        "cited_domains": cited_domains,
    }


def _parse_organic(items: list[dict], domain: str) -> dict:
    """Extract organic ranking info."""
    position = None
    top_10: list[dict] = []

    for item in items:
        if item.get("type") != "organic":
            continue
        rank = item.get("rank_group", 0)
        item_domain = item.get("domain", "")
        url = item.get("url", "")
        title = item.get("title", "")

        if rank <= 10:
            top_10.append({
                "rank": rank,
                "domain": item_domain,
                "url": url,
                "title": title,
            })

        if position is None and (domain in item_domain or domain in url):
            position = rank

    return {"position": position, "top_10": top_10}


def run(config: Config, *args: str) -> None:
    """Run GEO AI Overview check.

    Usage:
        searchstack geo                    # all configured keywords
        searchstack geo "your keyword"     # single keyword check
    """
    if not config.dataforseo.login or not config.dataforseo.password:
        print("DataForSEO credentials not configured.")
        print("Set dataforseo.login and dataforseo.password in .searchstack.toml")
        print("or DATAFORSEO_LOGIN / DATAFORSEO_PASSWORD environment variables.")
        return

    from searchstack.providers import dataforseo

    # Gather keywords
    if args:
        keywords = [" ".join(args)]
    else:
        keywords = []
        for group_keywords in config.geo_keywords.values():
            keywords.extend(group_keywords)

    if not keywords:
        print("No geo_keywords configured in .searchstack.toml")
        print("Add keywords like:")
        print('  [geo_keywords]')
        print('  brand = ["your brand name", "your brand review"]')
        print('  product = ["best tool for X", "how to do Y"]')
        return

    print(f"\n  Google AI Overview check for {config.domain}")
    print(f"  Checking {len(keywords)} keyword(s)...\n")

    results: list[dict] = []
    ai_present_count = 0
    cites_us_count = 0
    in_top10_count = 0
    all_cited_domains: dict[str, int] = {}

    for keyword in keywords:
        try:
            serp_data = dataforseo.serp_regular(
                keyword=keyword,
                location_code=config.dataforseo.location_code,
                language_code=config.dataforseo.language_code,
                config=config,
                load_ai_overview=True,
            )
        except Exception as e:
            print(f"    {keyword}")
            print(f"      error: {e}")
            results.append({"keyword": keyword, "error": str(e)})
            continue

        # Parse the first task result
        task_result = _extract_task_result(serp_data)
        if task_result is None:
            print(f"    {keyword}")
            print(f"      no result data")
            results.append({"keyword": keyword, "error": "no result data"})
            continue

        items = task_result.get("items", [])

        # AI Overview analysis
        ai_info = _parse_ai_overview(task_result, config.domain)
        organic = _parse_organic(items, config.domain)

        if ai_info["ai_present"]:
            ai_present_count += 1
        if ai_info["cites_us"]:
            cites_us_count += 1
        if organic["position"] is not None and organic["position"] <= 10:
            in_top10_count += 1

        for d in ai_info["cited_domains"]:
            all_cited_domains[d] = all_cited_domains.get(d, 0) + 1

        # Print per-keyword
        ai_icon = "\u2705" if ai_info["ai_present"] else "\u2796"
        cite_icon = "\u2705" if ai_info["cites_us"] else "\u274c"
        pos_str = f"#{organic['position']}" if organic["position"] else "not ranked"

        print(f"    {keyword}")
        print(f"      AI Overview: {ai_icon}  Cites us: {cite_icon}  Organic: {pos_str}")

        results.append({
            "keyword": keyword,
            "ai_overview_present": ai_info["ai_present"],
            "cites_us": ai_info["cites_us"],
            "cited_domains": ai_info["cited_domains"],
            "organic_position": organic["position"],
            "top_10": organic["top_10"],
        })

    # Summary
    total = len(keywords)
    print(f"\n  Summary ({total} keywords):")
    print(f"    AI Overview present:  {ai_present_count}/{total}")
    print(f"    Cites {config.domain}:  {cites_us_count}/{total}")
    print(f"    Organic top-10:       {in_top10_count}/{total}")

    if cites_us_count == 0 and all_cited_domains:
        top_cited = sorted(all_cited_domains.items(), key=lambda x: -x[1])[:10]
        print(f"\n  Top cited domains in AI Overviews:")
        for domain, count in top_cited:
            print(f"    {domain} ({count}x)")

    # Save snapshot
    snapshot_data = {
        "domain": config.domain,
        "keywords_checked": total,
        "ai_overview_present": ai_present_count,
        "cites_us": cites_us_count,
        "organic_top10": in_top10_count,
        "results": results,
    }
    path = snapshots.save_snapshot("geo_overview", snapshot_data)
    print(f"\n  Saved: {path}")


def _extract_task_result(response: dict) -> dict | None:
    """Pull the first result from DataForSEO response structure."""
    tasks = response.get("tasks", [])
    if not tasks:
        return None
    task = tasks[0]
    results = task.get("result", [])
    if not results:
        return None
    return results[0]
