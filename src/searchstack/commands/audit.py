"""Full SEO audit -- GSC data + keyword volumes (Google Ads KP / DataForSEO).

Combines search performance data with keyword volume data to find
opportunities, quick wins, and content gaps.
"""

from __future__ import annotations

from datetime import date, timedelta
from typing import Any

from searchstack.config import Config
from searchstack.providers.gsc import gsc_request, get_gsc_token, get_gsc_site_url_encoded
from searchstack.snapshots import save_snapshot


DATE_RANGE_DAYS = 28


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _date_range() -> tuple[str, str]:
    end = date.today() - timedelta(days=3)
    start = end - timedelta(days=DATE_RANGE_DAYS)
    return start.isoformat(), end.isoformat()


def _fmt_ctr(ctr: float) -> str:
    return f"{ctr * 100:.1f}%"


def _fmt_pos(pos: float) -> str:
    return f"{pos:.1f}"


def _short_url(url: str, domain: str) -> str:
    for prefix in (f"https://{domain}", f"http://{domain}"):
        if url.startswith(prefix):
            path = url[len(prefix):]
            return path if path else "/"
    return url


def _ensure_gsc(config: Config) -> bool:
    if not config.gsc.site_url:
        print("GSC site_url not configured.  Set [gsc] site_url in .searchstack.toml")
        return False
    token = get_gsc_token(config)
    if not token:
        print("GSC authentication failed.  Check token.pickle / credentials.")
        return False
    return True


# ---------------------------------------------------------------------------
# 1-2. Fetch GSC queries with best page
# ---------------------------------------------------------------------------

def _fetch_gsc_queries(config: Config) -> list[dict]:
    """Fetch GSC queries (query + page) for the last 28 days."""
    start, end = _date_range()
    site_url_enc = get_gsc_site_url_encoded(config)

    body = {
        "startDate": start,
        "endDate": end,
        "dimensions": ["query", "page"],
        "rowLimit": 200,
    }

    data = gsc_request(
        config,
        f"webmasters/v3/sites/{site_url_enc}/searchAnalytics/query",
        method="POST",
        body=body,
    )

    if data is None or "error" in data:
        print(f"  Error fetching GSC data: {data}")
        return []

    rows = data.get("rows", [])
    if not rows:
        print("  No GSC query data for this period.")
        return []

    # Deduplicate: keep the best-performing page per query (by clicks)
    best: dict[str, dict] = {}
    for row in rows:
        keys = row.get("keys", [])
        if len(keys) < 2:
            continue
        query, page = keys[0], keys[1]
        clicks = row.get("clicks", 0)
        impressions = row.get("impressions", 0)
        ctr = row.get("ctr", 0.0)
        position = row.get("position", 0.0)

        if query not in best or clicks > best[query]["clicks"]:
            best[query] = {
                "query": query,
                "page": page,
                "clicks": clicks,
                "impressions": impressions,
                "ctr": ctr,
                "position": position,
            }

    return list(best.values())


# ---------------------------------------------------------------------------
# 3. Get keyword volumes (Google Ads KP -> DataForSEO fallback)
# ---------------------------------------------------------------------------

def _get_volumes_google_ads(config: Config, keywords: list[str]) -> dict[str, dict] | None:
    """Try Google Ads Keyword Planner for volumes. Returns None if unconfigured."""
    if not config.google_ads.customer_id or not config.google_ads.developer_token:
        return None

    try:
        from searchstack.providers.google_ads import get_keyword_volumes
    except ImportError:
        return None

    results = get_keyword_volumes(config, keywords)
    if not results:
        return None

    return {r["keyword"].lower(): r for r in results}


def _get_volumes_dataforseo(config: Config, keywords: list[str]) -> dict[str, dict] | None:
    """Fallback: get keyword suggestions from DataForSEO."""
    if not config.dataforseo.login or not config.dataforseo.password:
        return None

    try:
        from searchstack.providers.dataforseo import api_request, get_location_code, get_language_code
    except ImportError:
        return None

    volumes: dict[str, dict] = {}

    # DataForSEO keyword_suggestions takes one seed at a time; batch the top keywords
    for kw in keywords[:20]:
        body = [
            {
                "keyword": kw,
                "location_code": get_location_code(config),
                "language_code": get_language_code(config),
                "include_seed_keyword": True,
                "limit": 5,
            }
        ]

        data = api_request(config, "dataforseo_labs/google/keyword_suggestions/live", body)
        if "error" in data:
            continue

        tasks = data.get("tasks", [])
        if not tasks or not tasks[0].get("result"):
            continue

        items = tasks[0]["result"][0].get("items", [])
        for item in items:
            kw_data = item.get("keyword_data", item)
            info = kw_data.get("keyword_info", {})
            keyword = kw_data.get("keyword", "").lower()
            volume = info.get("search_volume") or 0
            competition = info.get("competition", 0)
            cpc = info.get("cpc") or 0.0

            if keyword and keyword not in volumes:
                volumes[keyword] = {
                    "keyword": keyword,
                    "volume": volume,
                    "competition": str(competition),
                    "cpc_low": 0.0,
                    "cpc_high": round(cpc, 2),
                }

    return volumes if volumes else None


def _get_keyword_volumes(config: Config, keywords: list[str]) -> dict[str, dict]:
    """Get volumes: try Google Ads KP first, fall back to DataForSEO."""
    # Try Google Ads Keyword Planner
    result = _get_volumes_google_ads(config, keywords)
    if result:
        print("  Volume source: Google Ads Keyword Planner")
        return result

    # Fallback to DataForSEO
    result = _get_volumes_dataforseo(config, keywords)
    if result:
        print("  Volume source: DataForSEO")
        return result

    print("  No keyword volume provider configured (google_ads or dataforseo).")
    return {}


# ---------------------------------------------------------------------------
# 4-6. Merge, score, find gaps
# ---------------------------------------------------------------------------

def _merge_and_score(
    gsc_queries: list[dict],
    volumes: dict[str, dict],
) -> list[dict]:
    """Merge GSC data with volumes, calculate opportunity score."""
    merged: list[dict] = []

    for q in gsc_queries:
        query = q["query"]
        vol_data = volumes.get(query.lower(), {})
        volume = vol_data.get("volume", 0)

        # Opportunity score: volume * max(0, position - 3)
        # Higher = more opportunity to improve
        pos = q["position"]
        opportunity = volume * max(0, pos - 3) if volume and pos > 3 else 0

        merged.append({
            **q,
            "volume": volume,
            "competition": vol_data.get("competition", ""),
            "cpc_low": vol_data.get("cpc_low", 0.0),
            "cpc_high": vol_data.get("cpc_high", 0.0),
            "opportunity": round(opportunity),
        })

    merged.sort(key=lambda r: r["opportunity"], reverse=True)
    return merged


def _find_content_gaps(
    gsc_queries: list[dict],
    volumes: dict[str, dict],
) -> list[dict]:
    """Find high-volume keywords from KP that are NOT in GSC data."""
    gsc_keywords = {q["query"].lower() for q in gsc_queries}
    gaps: list[dict] = []

    for kw, data in volumes.items():
        if kw not in gsc_keywords and data.get("volume", 0) > 0:
            gaps.append(data)

    gaps.sort(key=lambda r: r.get("volume", 0), reverse=True)
    return gaps


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def run(config: Config, *args: str) -> None:
    """Full SEO audit with keyword volumes.

    Usage:
        searchstack audit
    """
    if not _ensure_gsc(config):
        return

    start, end = _date_range()
    print(f"\n  SEO Audit")
    print(f"  Period: {start} to {end}")
    print(f"  {'=' * 70}\n")

    # 1-2. Fetch GSC queries with best page
    print("  Fetching GSC query data...")
    gsc_queries = _fetch_gsc_queries(config)
    if not gsc_queries:
        return

    print(f"  Found {len(gsc_queries)} unique queries.\n")

    # 3. Get keyword volumes for top 20 queries
    top_keywords = [q["query"] for q in sorted(gsc_queries, key=lambda x: x["clicks"], reverse=True)[:20]]
    print(f"  Fetching volumes for top {len(top_keywords)} queries...")
    volumes = _get_keyword_volumes(config, top_keywords)
    print(f"  Got volumes for {len(volumes)} keywords.\n")

    # 4-5. Merge and score
    merged = _merge_and_score(gsc_queries, volumes)

    # 7. Print merged table
    print(f"  Audit Results (sorted by opportunity score)")
    print(f"  {'─' * 110}")

    kw_w = 35
    pg_w = 30
    print(
        f"    {'Query':<{kw_w}}  {'Best Page':<{pg_w}}  "
        f"{'Clicks':>7} {'Impr':>7} {'CTR':>6} {'Pos':>5}  "
        f"{'Vol':>7} {'Opp':>7}"
    )
    print(
        f"    {'─' * kw_w}  {'─' * pg_w}  "
        f"{'─' * 7} {'─' * 7} {'─' * 6} {'─' * 5}  "
        f"{'─' * 7} {'─' * 7}"
    )

    for row in merged[:50]:
        query = row["query"]
        if len(query) > kw_w:
            query = query[:kw_w - 3] + "..."

        page = _short_url(row["page"], config.domain)
        if len(page) > pg_w:
            page = page[:pg_w - 3] + "..."

        print(
            f"    {query:<{kw_w}}  {page:<{pg_w}}  "
            f"{row['clicks']:7,d} {row['impressions']:7,d} "
            f"{_fmt_ctr(row['ctr']):>6s} {_fmt_pos(row['position']):>5s}  "
            f"{row['volume']:7,d} {row['opportunity']:7,d}"
        )

    # 6. Content gaps (KP keywords not in GSC)
    gaps = _find_content_gaps(gsc_queries, volumes)
    if gaps:
        print(f"\n  New Content Opportunities ({len(gaps)} keywords not in GSC)")
        print(f"  {'─' * 60}")
        print(f"    {'Keyword':<{kw_w}}  {'Volume':>7}  {'Competition':<12}  {'CPC':>7}")
        print(f"    {'─' * kw_w}  {'─' * 7}  {'─' * 12}  {'─' * 7}")

        for gap in gaps[:20]:
            kw = gap.get("keyword", "")
            if len(kw) > kw_w:
                kw = kw[:kw_w - 3] + "..."
            cpc = gap.get("cpc_high", 0) or gap.get("cpc_low", 0)
            print(
                f"    {kw:<{kw_w}}  {gap.get('volume', 0):7,d}  "
                f"{gap.get('competition', ''):<12s}  ${cpc:6.2f}"
            )

    # 8. Summary
    pages_with_traffic = len([q for q in gsc_queries if q["clicks"] > 0])
    total_clicks = sum(q["clicks"] for q in gsc_queries)
    total_impressions = sum(q["impressions"] for q in gsc_queries)
    avg_ctr = total_clicks / total_impressions if total_impressions else 0

    print(f"\n  Summary")
    print(f"  {'─' * 60}")
    print(f"    Queries with traffic:  {pages_with_traffic}")
    print(f"    Total clicks:          {total_clicks:,}")
    print(f"    Total impressions:     {total_impressions:,}")
    print(f"    Average CTR:           {_fmt_ctr(avg_ctr)}")

    # 9. Quick wins (volume >= 200, position > 20)
    quick_wins = [
        r for r in merged
        if r["volume"] >= 200 and r["position"] > 20
    ]

    if quick_wins:
        print(f"\n  Quick Wins ({len(quick_wins)}) -- volume >= 200, position > 20")
        print(f"  {'─' * 80}")
        print(f"    {'Query':<{kw_w}}  {'Pos':>5}  {'Vol':>7}  {'Best Page'}")
        print(f"    {'─' * kw_w}  {'─' * 5}  {'─' * 7}  {'─' * 30}")

        for qw in quick_wins:
            query = qw["query"]
            if len(query) > kw_w:
                query = query[:kw_w - 3] + "..."
            page = _short_url(qw["page"], config.domain)
            print(
                f"    {query:<{kw_w}}  {_fmt_pos(qw['position']):>5s}  "
                f"{qw['volume']:7,d}  {page}"
            )
    else:
        print(f"\n  Quick Wins: none found (volume >= 200, position > 20)")

    # 10. Save snapshot
    snapshot = {
        "date": date.today().isoformat(),
        "period": {"start": start, "end": end},
        "queries": merged,
        "content_gaps": gaps,
        "summary": {
            "queries_with_traffic": pages_with_traffic,
            "total_clicks": total_clicks,
            "total_impressions": total_impressions,
            "avg_ctr": avg_ctr,
            "quick_wins_count": len(quick_wins),
            "content_gaps_count": len(gaps),
        },
    }

    path = save_snapshot("audit", snapshot)
    print(f"\n  Snapshot saved: {path}")
