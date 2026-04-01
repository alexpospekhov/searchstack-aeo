"""Full 14-section Markdown report generator.

Aggregates data from Plausible, GSC, GEO/AI snapshots, DataForSEO,
and site crawl into a comprehensive SEO/AEO report.
"""

from __future__ import annotations

import json
import re
import urllib.request
from datetime import datetime, timezone
from typing import Any
from urllib.parse import quote

from searchstack import snapshots
from searchstack.config import Config


_UA = "Mozilla/5.0 SearchStack/1.0"


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

def _today() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def _fetch_sitemap_urls(sitemap_url: str) -> list[str]:
    req = urllib.request.Request(sitemap_url, headers={"User-Agent": _UA})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            body = resp.read().decode("utf-8", errors="replace")
    except Exception:
        return []

    if "<sitemapindex" in body:
        nested = re.findall(r"<loc>\s*(.*?)\s*</loc>", body)
        all_urls: list[str] = []
        for sub_url in nested:
            all_urls.extend(_fetch_sitemap_urls(sub_url))
        return all_urls

    return re.findall(r"<loc>\s*(.*?)\s*</loc>", body)


def _short_url(url: str, domain: str) -> str:
    for prefix in (f"https://{domain}", f"http://{domain}"):
        if url.startswith(prefix):
            path = url[len(prefix):]
            return path if path else "/"
    return url


# ---------------------------------------------------------------------------
# Data collectors -- each returns a dict or None
# ---------------------------------------------------------------------------

def _collect_traffic(config: Config) -> dict[str, Any] | None:
    """Plausible 30-day traffic data."""
    if not config.plausible.api_key or not config.plausible.site_id:
        return None

    try:
        from searchstack.providers.plausible import query

        # Total visitors + pageviews last 30 days
        result = query(config, {
            "metrics": ["visitors", "pageviews", "bounce_rate", "visit_duration"],
            "date_range": "30d",
        })

        if "error" in result:
            return None

        results_list = result.get("results", [])
        if not results_list:
            return None

        row = results_list[0] if isinstance(results_list, list) else results_list
        metrics = row.get("metrics", row) if isinstance(row, dict) else {}

        # Top pages
        pages_result = query(config, {
            "metrics": ["visitors", "pageviews"],
            "dimensions": ["event:page"],
            "date_range": "30d",
            "order_by": [["visitors", "desc"]],
            "limit": 20,
        })

        top_pages: list[dict[str, Any]] = []
        for item in pages_result.get("results", []):
            dims = item.get("dimensions", [])
            m = item.get("metrics", [])
            if dims and m:
                top_pages.append({
                    "page": dims[0],
                    "visitors": m[0] if len(m) > 0 else 0,
                    "pageviews": m[1] if len(m) > 1 else 0,
                })

        # Top sources
        sources_result = query(config, {
            "metrics": ["visitors"],
            "dimensions": ["visit:source"],
            "date_range": "30d",
            "order_by": [["visitors", "desc"]],
            "limit": 15,
        })

        top_sources: list[dict[str, Any]] = []
        for item in sources_result.get("results", []):
            dims = item.get("dimensions", [])
            m = item.get("metrics", [])
            if dims and m:
                top_sources.append({"source": dims[0], "visitors": m[0]})

        return {
            "metrics": metrics if isinstance(metrics, dict) else {},
            "top_pages": top_pages,
            "top_sources": top_sources,
        }
    except Exception:
        return None


def _collect_gsc_queries(config: Config) -> list[dict[str, Any]] | None:
    """GSC top 25 search queries last 28 days."""
    if not config.gsc.site_url:
        return None

    try:
        from searchstack.providers.gsc import gsc_request, get_gsc_site_url_encoded

        site = get_gsc_site_url_encoded(config)
        result = gsc_request(config, f"webmasters/v3/sites/{site}/searchAnalytics/query", method="POST", body={
            "startDate": _offset_date(-28),
            "endDate": _offset_date(-1),
            "dimensions": ["query"],
            "rowLimit": 25,
            "type": "web",
        })

        if result is None or "error" in result:
            return None

        rows = result.get("rows", [])
        queries: list[dict[str, Any]] = []
        for row in rows:
            keys = row.get("keys", [])
            queries.append({
                "query": keys[0] if keys else "",
                "clicks": row.get("clicks", 0),
                "impressions": row.get("impressions", 0),
                "ctr": round(row.get("ctr", 0) * 100, 1),
                "position": round(row.get("position", 0), 1),
            })

        return queries
    except Exception:
        return None


def _collect_geo(config: Config) -> dict[str, Any] | None:
    """Load latest GEO snapshot."""
    return snapshots.load_latest_snapshot("geo")


def _collect_ai(config: Config) -> dict[str, Any] | None:
    """Load latest AI citation snapshot."""
    return snapshots.load_latest_snapshot("ai_citations")


def _collect_positions(config: Config) -> dict[str, Any] | None:
    """Load latest position tracking data from DataForSEO."""
    if not config.dataforseo.login:
        return None

    try:
        from searchstack.providers.dataforseo import api_request, get_location_code, get_language_code

        body = [{
            "target": config.domain,
            "location_code": get_location_code(config),
            "language_code": get_language_code(config),
            "limit": 50,
        }]

        result = api_request(config, "dataforseo_labs/google/ranked_keywords/live", body)

        if "error" in result:
            return None

        tasks = result.get("tasks", [])
        if not tasks or not tasks[0].get("result"):
            return None

        items = tasks[0]["result"][0].get("items", [])
        keywords: list[dict[str, Any]] = []

        for item in items:
            kw_data = item.get("keyword_data", {})
            ranked = item.get("ranked_serp_element", {})
            info = kw_data.get("keyword_info", {})

            keywords.append({
                "keyword": kw_data.get("keyword", ""),
                "position": ranked.get("serp_item", {}).get("rank_absolute", 0),
                "volume": info.get("search_volume", 0),
                "url": ranked.get("serp_item", {}).get("relative_url", ""),
            })

        return {"keywords": keywords, "total": len(keywords)}
    except Exception:
        return None


def _collect_competitors(config: Config) -> list[dict[str, Any]] | None:
    """Bulk traffic estimation for configured competitors."""
    if not config.dataforseo.login or not config.competitors:
        return None

    try:
        from searchstack.providers.dataforseo import api_request, get_location_code, get_language_code

        targets = [config.domain] + config.competitors
        body = [{
            "targets": targets,
            "location_code": get_location_code(config),
            "language_code": get_language_code(config),
        }]

        result = api_request(config, "dataforseo_labs/google/bulk_traffic_estimation/live", body)

        if "error" in result:
            return None

        tasks = result.get("tasks", [])
        if not tasks or not tasks[0].get("result"):
            return None

        items = tasks[0]["result"][0].get("items", [])
        competitors: list[dict[str, Any]] = []

        for item in items:
            competitors.append({
                "domain": item.get("target", ""),
                "etv": item.get("metrics", {}).get("organic", {}).get("etv", 0),
                "count": item.get("metrics", {}).get("organic", {}).get("count", 0),
            })

        return competitors
    except Exception:
        return None


def _collect_indexing(config: Config) -> dict[str, Any] | None:
    """URL inspection results via GSC."""
    if not config.gsc.site_url or not config.sitemap:
        return None

    try:
        from searchstack.providers.gsc import gsc_request

        urls = _fetch_sitemap_urls(config.sitemap)
        if not urls:
            return None

        results: list[dict[str, Any]] = []
        indexed = 0
        not_indexed = 0
        errors = 0

        for url in urls:
            body = {
                "inspectionUrl": url,
                "siteUrl": config.gsc.site_url,
            }
            result = gsc_request(config, "v1/urlInspection/index:inspect", method="POST", body=body)

            if result is None or "error" in result:
                errors += 1
                results.append({"url": url, "verdict": "ERROR", "coverage": "Error"})
                continue

            inspection = result.get("inspectionResult", {})
            idx = inspection.get("indexStatusResult", {})
            verdict = idx.get("verdict", "Unknown")
            coverage = idx.get("coverageState", "Unknown")
            last_crawl = idx.get("lastCrawlTime", "")[:10]

            if verdict.upper() == "PASS":
                indexed += 1
            else:
                not_indexed += 1

            results.append({
                "url": url,
                "verdict": verdict,
                "coverage": coverage,
                "last_crawl": last_crawl,
            })

        return {
            "pages": results,
            "indexed": indexed,
            "not_indexed": not_indexed,
            "errors": errors,
            "total": len(results),
        }
    except Exception:
        return None


def _collect_backlinks(config: Config) -> dict[str, Any] | None:
    """Backlink summary from DataForSEO."""
    if not config.dataforseo.login:
        return None

    try:
        from searchstack.providers.dataforseo import api_request

        body = [{"target": config.domain, "internal_list_limit": 0, "external_list_limit": 0}]
        result = api_request(config, "backlinks/summary/live", body)

        if "error" in result:
            return None

        tasks = result.get("tasks", [])
        if not tasks or not tasks[0].get("result"):
            return None

        summary = tasks[0]["result"][0]
        return {
            "total_backlinks": summary.get("total_backlinks", 0),
            "referring_domains": summary.get("referring_domains", 0),
            "referring_ips": summary.get("referring_ips", 0),
            "broken_backlinks": summary.get("broken_backlinks", 0),
            "referring_domains_nofollow": summary.get("referring_domains_nofollow", 0),
            "rank": summary.get("rank", 0),
        }
    except Exception:
        return None


def _collect_keyword_gaps(config: Config) -> list[dict[str, Any]] | None:
    """High-volume keywords where domain ranks poorly or not at all."""
    if not config.dataforseo.login or not config.competitors:
        return None

    try:
        from searchstack.providers.dataforseo import api_request, get_location_code, get_language_code

        body = [{
            "target1": config.domain,
            "target2": config.competitors[0],
            "location_code": get_location_code(config),
            "language_code": get_language_code(config),
            "limit": 20,
            "order_by": ["keyword_data.keyword_info.search_volume,desc"],
            "filters": [
                ["keyword_data.keyword_info.search_volume", ">", 100],
            ],
        }]

        result = api_request(config, "dataforseo_labs/google/domain_intersection/live", body)

        if "error" in result:
            return None

        tasks = result.get("tasks", [])
        if not tasks or not tasks[0].get("result"):
            return None

        items = tasks[0]["result"][0].get("items", [])
        gaps: list[dict[str, Any]] = []

        for item in items:
            kw_data = item.get("keyword_data", {})
            info = kw_data.get("keyword_info", {})
            first = item.get("first_domain_serp_element")
            second = item.get("second_domain_serp_element")

            my_pos = first.get("serp_item", {}).get("rank_absolute", 0) if first else 0
            comp_pos = second.get("serp_item", {}).get("rank_absolute", 0) if second else 0

            gaps.append({
                "keyword": kw_data.get("keyword", ""),
                "volume": info.get("search_volume", 0),
                "my_position": my_pos,
                "competitor_position": comp_pos,
            })

        return gaps
    except Exception:
        return None


def _collect_position_changes(config: Config) -> dict[str, Any] | None:
    """Compare current positions with latest snapshot."""
    latest = snapshots.load_latest_snapshot("positions")
    if not latest:
        return None
    return latest


def _collect_meta_issues(config: Config) -> dict[str, Any] | None:
    """Run meta audit (reuse meta module logic)."""
    try:
        from searchstack.commands.meta import _fetch_sitemap_urls, _filter_html_urls, _fetch_meta, _check_issues

        if not config.sitemap:
            return None

        all_urls = _fetch_sitemap_urls(config.sitemap)
        html_urls = _filter_html_urls(all_urls)

        results: list[dict[str, Any]] = []
        for url in html_urls:
            meta = _fetch_meta(url)
            issues = _check_issues(meta)
            if issues:
                meta["issues"] = issues
                results.append(meta)

        return {"pages_with_issues": results, "total_issues": sum(len(r.get("issues", [])) for r in results)}
    except Exception:
        return None


def _collect_orphans(config: Config) -> dict[str, Any] | None:
    """Run link analysis for orphan detection."""
    try:
        from searchstack.commands.links import run as links_run
        # links.run prints output; we call it silently by importing internals
        from searchstack.commands.links import (
            _fetch_sitemap_urls, _filter_html_urls,
            _normalize_url, _fetch_internal_links,
        )

        if not config.sitemap:
            return None

        all_urls = _fetch_sitemap_urls(config.sitemap)
        html_urls = _filter_html_urls(all_urls)

        if not html_urls:
            return None

        sitemap_normalized = {_normalize_url(u) for u in html_urls}
        linked_to: dict[str, int] = {u: 0 for u in sitemap_normalized}

        for url in html_urls:
            norm_url = _normalize_url(url)
            internal = _fetch_internal_links(url, config.domain)
            for link in internal:
                if link in linked_to:
                    linked_to[link] += 1

        orphans = [u for u, count in linked_to.items() if count == 0]
        return {
            "orphans": [_short_url(u, config.domain) for u in sorted(orphans)],
            "total_pages": len(sitemap_normalized),
            "total_orphans": len(orphans),
        }
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Date helper
# ---------------------------------------------------------------------------

def _offset_date(days: int) -> str:
    """Return ISO date string offset from today by N days."""
    from datetime import timedelta
    dt = datetime.now(timezone.utc) + timedelta(days=days)
    return dt.strftime("%Y-%m-%d")


# ---------------------------------------------------------------------------
# Report sections
# ---------------------------------------------------------------------------

def _section_traffic(L: list[str], data: dict[str, Any] | None) -> None:
    L.append("## 2. Traffic (Plausible 30d)\n")
    if data is None:
        L.append("*Plausible not configured or unavailable.*\n")
        return

    metrics = data.get("metrics", {})
    visitors = metrics.get("visitors", metrics[0]) if isinstance(metrics, (list, dict)) else 0
    if isinstance(metrics, dict):
        visitors = metrics.get("visitors", 0)
        pageviews = metrics.get("pageviews", 0)
        bounce = metrics.get("bounce_rate", 0)
        duration = metrics.get("visit_duration", 0)
    elif isinstance(metrics, list):
        visitors = metrics[0] if len(metrics) > 0 else 0
        pageviews = metrics[1] if len(metrics) > 1 else 0
        bounce = metrics[2] if len(metrics) > 2 else 0
        duration = metrics[3] if len(metrics) > 3 else 0
    else:
        visitors = pageviews = bounce = duration = 0

    L.append(f"| Metric | Value |")
    L.append(f"|--------|-------|")
    L.append(f"| Visitors | {visitors:,} |")
    L.append(f"| Pageviews | {pageviews:,} |")
    L.append(f"| Bounce Rate | {bounce}% |")
    L.append(f"| Avg Duration | {duration}s |")
    L.append("")

    top_pages = data.get("top_pages", [])
    if top_pages:
        L.append("### Top Pages\n")
        L.append("| Page | Visitors | Pageviews |")
        L.append("|------|----------|-----------|")
        for p in top_pages[:15]:
            L.append(f"| {p['page']} | {p['visitors']:,} | {p['pageviews']:,} |")
        L.append("")

    top_sources = data.get("top_sources", [])
    if top_sources:
        L.append("### Traffic Sources\n")
        L.append("| Source | Visitors |")
        L.append("|--------|----------|")
        for s in top_sources[:10]:
            L.append(f"| {s['source']} | {s['visitors']:,} |")
        L.append("")


def _section_queries(L: list[str], data: list[dict[str, Any]] | None) -> None:
    L.append("## 3. Search Queries (GSC Top 25)\n")
    if data is None:
        L.append("*GSC not configured or unavailable.*\n")
        return

    L.append("| Query | Clicks | Impressions | CTR | Position |")
    L.append("|-------|--------|-------------|-----|----------|")
    for q in data:
        L.append(f"| {q['query']} | {q['clicks']:,} | {q['impressions']:,} | {q['ctr']}% | {q['position']} |")
    L.append("")


def _section_geo(L: list[str], data: dict[str, Any] | None) -> None:
    L.append("## 4. GEO Visibility\n")
    if data is None:
        L.append("*No GEO snapshot available. Run `searchstack geo` first.*\n")
        return

    keywords = data.get("keywords", data.get("results", []))
    if isinstance(keywords, dict):
        for kw, results in keywords.items():
            L.append(f"### {kw}\n")
            if isinstance(results, list):
                for r in results:
                    cited = r.get("cited", False)
                    icon = "\u2705" if cited else "\u274c"
                    L.append(f"- {icon} {r.get('query', r.get('keyword', ''))}")
            elif isinstance(results, dict):
                for subkw, val in results.items():
                    icon = "\u2705" if val else "\u274c"
                    L.append(f"- {icon} {subkw}")
            L.append("")
    elif isinstance(keywords, list):
        for item in keywords:
            kw = item.get("keyword", item.get("query", ""))
            cited = item.get("cited", item.get("visible", False))
            icon = "\u2705" if cited else "\u274c"
            L.append(f"- {icon} {kw}")
        L.append("")
    else:
        L.append(f"Snapshot data: {json.dumps(data, indent=2)[:500]}\n")


def _section_aeo(L: list[str], data: dict[str, Any] | None) -> None:
    L.append("## 5. AEO Status (AI Citations)\n")
    if data is None:
        L.append("*No AI citation snapshot available. Run `searchstack ai` first.*\n")
        return

    providers = data.get("providers", {})
    if not providers:
        L.append("*No provider data in snapshot.*\n")
        return

    for provider_name, pdata in providers.items():
        cited = pdata.get("cited", 0)
        total = pdata.get("total", 0)
        pct = (cited / total * 100) if total else 0
        L.append(f"### {provider_name.title()} ({cited}/{total} = {pct:.0f}%)\n")

        for r in pdata.get("results", []):
            query = r.get("query", "")
            is_cited = r.get("cited", False)
            icon = "\u2705" if is_cited else "\u274c"
            L.append(f"- {icon} \"{query}\"")

        L.append("")


def _section_positions(L: list[str], data: dict[str, Any] | None) -> None:
    L.append("## 6. Google Positions (DataForSEO)\n")
    if data is None:
        L.append("*DataForSEO not configured or no data.*\n")
        return

    keywords = data.get("keywords", [])
    if not keywords:
        L.append("*No ranked keywords found.*\n")
        return

    L.append("| Keyword | Position | Volume | URL |")
    L.append("|---------|----------|--------|-----|")
    for kw in keywords[:30]:
        L.append(f"| {kw['keyword']} | {kw['position']} | {kw.get('volume', 0):,} | {kw.get('url', '')} |")
    L.append(f"\nTotal ranked keywords: {data.get('total', len(keywords))}\n")


def _section_competitors(L: list[str], data: list[dict[str, Any]] | None) -> None:
    L.append("## 7. Competitor Traffic Estimation\n")
    if data is None:
        L.append("*No competitors configured or DataForSEO unavailable.*\n")
        return

    L.append("| Domain | Est. Traffic | Ranked Keywords |")
    L.append("|--------|--------------|-----------------|")
    for c in data:
        L.append(f"| {c['domain']} | {c.get('etv', 0):,.0f} | {c.get('count', 0):,} |")
    L.append("")


def _section_indexing(L: list[str], data: dict[str, Any] | None) -> None:
    L.append("## 8. Indexing Status\n")
    if data is None:
        L.append("*GSC not configured or sitemap unavailable.*\n")
        return

    indexed = data.get("indexed", 0)
    not_indexed = data.get("not_indexed", 0)
    errors = data.get("errors", 0)
    total = data.get("total", 0)

    L.append(f"- **Indexed:** {indexed}")
    L.append(f"- **Not indexed:** {not_indexed}")
    L.append(f"- **Errors:** {errors}")
    L.append(f"- **Total:** {total}")
    L.append("")

    pages = data.get("pages", [])
    not_indexed_pages = [p for p in pages if p.get("verdict", "").upper() != "PASS"]
    if not_indexed_pages:
        L.append("### Not Indexed Pages\n")
        L.append("| URL | Coverage | Last Crawl |")
        L.append("|-----|----------|------------|")
        for p in not_indexed_pages[:20]:
            L.append(f"| {p['url']} | {p.get('coverage', '')} | {p.get('last_crawl', '')} |")
        L.append("")


def _section_backlinks(L: list[str], data: dict[str, Any] | None) -> None:
    L.append("## 9. Backlinks\n")
    if data is None:
        L.append("*DataForSEO not configured.*\n")
        return

    L.append(f"| Metric | Value |")
    L.append(f"|--------|-------|")
    L.append(f"| Total Backlinks | {data.get('total_backlinks', 0):,} |")
    L.append(f"| Referring Domains | {data.get('referring_domains', 0):,} |")
    L.append(f"| Referring IPs | {data.get('referring_ips', 0):,} |")
    L.append(f"| Broken Backlinks | {data.get('broken_backlinks', 0):,} |")
    L.append(f"| Nofollow Domains | {data.get('referring_domains_nofollow', 0):,} |")
    L.append(f"| Domain Rank | {data.get('rank', 0)} |")
    L.append("")


def _section_gaps(L: list[str], data: list[dict[str, Any]] | None) -> None:
    L.append("## 10. Keyword Gaps\n")
    if data is None:
        L.append("*No competitor configured or DataForSEO unavailable.*\n")
        return

    if not data:
        L.append("*No keyword gaps found.*\n")
        return

    L.append("| Keyword | Volume | Your Pos | Competitor Pos |")
    L.append("|---------|--------|----------|----------------|")
    for g in data:
        my_pos = g.get("my_position", 0) or "-"
        comp_pos = g.get("competitor_position", 0) or "-"
        L.append(f"| {g['keyword']} | {g.get('volume', 0):,} | {my_pos} | {comp_pos} |")
    L.append("")


def _section_position_changes(L: list[str], data: dict[str, Any] | None) -> None:
    L.append("## 11. Position Changes\n")
    if data is None:
        L.append("*No position snapshot available. Run `searchstack track` first.*\n")
        return

    keywords = data.get("keywords", [])
    if not keywords:
        L.append("*No tracking data.*\n")
        return

    L.append("| Keyword | Position | Volume |")
    L.append("|---------|----------|--------|")
    for kw in keywords[:20]:
        L.append(f"| {kw.get('keyword', '')} | {kw.get('position', '?')} | {kw.get('volume', 0):,} |")
    L.append("")


def _section_meta_issues(L: list[str], data: dict[str, Any] | None, domain: str) -> None:
    L.append("## 12. Meta Issues\n")
    if data is None:
        L.append("*Could not crawl site for meta issues.*\n")
        return

    pages = data.get("pages_with_issues", [])
    total_issues = data.get("total_issues", 0)

    if not pages:
        L.append("No meta issues found. All pages pass.\n")
        return

    L.append(f"**{total_issues} issues** across {len(pages)} pages:\n")
    L.append("| Page | Issues |")
    L.append("|------|--------|")
    for p in pages:
        path = _short_url(p.get("url", ""), domain)
        issues = ", ".join(p.get("issues", []))
        L.append(f"| {path} | {issues} |")
    L.append("")


def _section_orphans(L: list[str], data: dict[str, Any] | None) -> None:
    L.append("## 13. Orphan Pages\n")
    if data is None:
        L.append("*Could not crawl site for orphan detection.*\n")
        return

    orphans = data.get("orphans", [])
    total = data.get("total_pages", 0)

    if not orphans:
        L.append(f"No orphan pages found across {total} pages.\n")
        return

    L.append(f"**{len(orphans)} orphan pages** (no inbound internal links) out of {total}:\n")
    for o in orphans:
        L.append(f"- {o}")
    L.append("")


def _section_recommendations(
    L: list[str],
    traffic: dict[str, Any] | None,
    positions: dict[str, Any] | None,
    backlinks: dict[str, Any] | None,
    meta_issues: dict[str, Any] | None,
    orphans: dict[str, Any] | None,
    gaps: list[dict[str, Any]] | None,
    ai_data: dict[str, Any] | None,
    indexing: dict[str, Any] | None,
) -> list[str]:
    """Generate auto-recommendations and return them as a list too."""
    L.append("## 14. Recommendations\n")

    recs: list[str] = []

    # Meta issues
    if meta_issues and meta_issues.get("total_issues", 0) > 0:
        count = meta_issues["total_issues"]
        recs.append(f"Fix {count} meta tag issues (title/description length, missing H1)")

    # Orphan pages
    if orphans and orphans.get("total_orphans", 0) > 0:
        count = orphans["total_orphans"]
        recs.append(f"Add internal links to {count} orphan pages")

    # Indexing
    if indexing:
        not_indexed = indexing.get("not_indexed", 0) + indexing.get("errors", 0)
        if not_indexed > 0:
            recs.append(f"Investigate {not_indexed} pages not indexed by Google")

    # Backlinks
    if backlinks:
        broken = backlinks.get("broken_backlinks", 0)
        if broken > 0:
            recs.append(f"Reclaim {broken:,} broken backlinks (301 redirects or outreach)")
        domains = backlinks.get("referring_domains", 0)
        if domains < 50:
            recs.append("Build more referring domains (currently under 50)")

    # Keyword gaps
    if gaps and len(gaps) > 0:
        recs.append(f"Target {len(gaps)} keyword gaps where competitors rank but you don't")

    # AI citations
    if ai_data:
        providers = ai_data.get("providers", {})
        total_cited = sum(p.get("cited", 0) for p in providers.values())
        total_queries = sum(p.get("total", 0) for p in providers.values())
        if total_queries > 0 and total_cited / total_queries < 0.5:
            recs.append("Improve AI citation rate (below 50%) -- optimize llms.txt and structured data")

    # Positions
    if positions:
        keywords = positions.get("keywords", [])
        page2 = [kw for kw in keywords if 11 <= kw.get("position", 0) <= 20]
        if page2:
            top3 = sorted(page2, key=lambda k: k.get("volume", 0), reverse=True)[:3]
            kw_str = ", ".join(k["keyword"] for k in top3)
            recs.append(f"Push page-2 keywords to page 1: {kw_str}")

    if not recs:
        recs.append("No critical issues detected. Continue monitoring.")

    for i, rec in enumerate(recs, 1):
        L.append(f"{i}. {rec}")

    L.append("")
    return recs


def _build_executive_summary(
    domain: str,
    traffic: dict[str, Any] | None,
    ai_data: dict[str, Any] | None,
    backlinks: dict[str, Any] | None,
    gaps: list[dict[str, Any]] | None,
    recs: list[str],
) -> list[str]:
    """Build the executive summary section."""
    lines: list[str] = []
    lines.append("## 1. Executive Summary\n")

    # Visitors
    visitors = 0
    if traffic:
        metrics = traffic.get("metrics", {})
        if isinstance(metrics, dict):
            visitors = metrics.get("visitors", 0)
        elif isinstance(metrics, list) and metrics:
            visitors = metrics[0]
    lines.append(f"- **Visitors (30d):** {visitors:,}")

    # AI citations
    if ai_data:
        providers = ai_data.get("providers", {})
        total_cited = sum(p.get("cited", 0) for p in providers.values())
        total_queries = sum(p.get("total", 0) for p in providers.values())
        lines.append(f"- **AI Citations:** {total_cited}/{total_queries} queries")
    else:
        lines.append("- **AI Citations:** N/A")

    # Backlinks
    if backlinks:
        lines.append(f"- **Backlinks:** {backlinks.get('total_backlinks', 0):,} ({backlinks.get('referring_domains', 0):,} domains)")
    else:
        lines.append("- **Backlinks:** N/A")

    # Gaps
    gap_count = len(gaps) if gaps else 0
    lines.append(f"- **Keyword Gaps:** {gap_count}")

    # Top recommendations
    lines.append(f"- **Action Items:** {len(recs)}")
    if recs:
        lines.append(f"\n**Top priority:** {recs[0]}")

    lines.append("")
    return lines


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def run(config: Config, *args: str) -> None:
    """Generate a full 14-section Markdown SEO/AEO report."""
    if not config.domain:
        print("  No domain configured. Set domain = \"...\" in .searchstack.toml")
        return

    print(f"\n  Generating report for {config.domain}...")
    print(f"  This may take a few minutes.\n")

    # Collect data from all sources
    print("  [1/10] Traffic (Plausible)...")
    traffic = _collect_traffic(config)

    print("  [2/10] Search queries (GSC)...")
    gsc_queries = _collect_gsc_queries(config)

    print("  [3/10] GEO visibility (snapshot)...")
    geo_data = _collect_geo(config)

    print("  [4/10] AI citations (snapshot)...")
    ai_data = _collect_ai(config)

    print("  [5/10] Google positions (DataForSEO)...")
    positions = _collect_positions(config)

    print("  [6/10] Competitor traffic...")
    competitors = _collect_competitors(config)

    print("  [7/10] Indexing status (GSC)...")
    indexing = _collect_indexing(config)

    print("  [8/10] Backlinks (DataForSEO)...")
    backlinks_data = _collect_backlinks(config)

    print("  [9/10] Keyword gaps...")
    gaps = _collect_keyword_gaps(config)

    print("  [10/10] Crawling site (meta + links)...")
    meta_issues = _collect_meta_issues(config)
    orphans = _collect_orphans(config)

    position_changes = _collect_position_changes(config)

    # Build report
    L: list[str] = []
    L.append(f"# SEO/AEO Report: {config.domain}")
    L.append(f"*Generated {_today()} by SearchStack*\n")
    L.append("---\n")

    # Placeholder for executive summary (inserted after recommendations)
    exec_placeholder = len(L)

    _section_traffic(L, traffic)
    _section_queries(L, gsc_queries)
    _section_geo(L, geo_data)
    _section_aeo(L, ai_data)
    _section_positions(L, positions)
    _section_competitors(L, competitors)
    _section_indexing(L, indexing)
    _section_backlinks(L, backlinks_data)
    _section_gaps(L, gaps)
    _section_position_changes(L, position_changes)
    _section_meta_issues(L, meta_issues, config.domain)
    _section_orphans(L, orphans)

    recs = _section_recommendations(
        L, traffic, positions, backlinks_data, meta_issues, orphans, gaps, ai_data, indexing,
    )

    # Insert executive summary at top
    exec_lines = _build_executive_summary(
        config.domain, traffic, ai_data, backlinks_data, gaps, recs,
    )
    for i, line in enumerate(exec_lines):
        L.insert(exec_placeholder + i, line)

    # Final report string
    report = "\n".join(L)

    # Save to snapshot dir
    snapshot_dir = snapshots.get_snapshot_dir()
    filename = f"report_{_today()}.md"
    report_path = snapshot_dir / filename

    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report)

    # Also save as JSON snapshot for programmatic access
    snapshot_data = {
        "domain": config.domain,
        "date": _today(),
        "traffic": traffic,
        "gsc_queries": gsc_queries,
        "geo": geo_data is not None,
        "ai": ai_data is not None,
        "positions": positions,
        "competitors": competitors,
        "indexing": indexing,
        "backlinks": backlinks_data,
        "gaps": gaps,
        "meta_issues": meta_issues,
        "orphans": orphans,
        "recommendations": recs,
    }
    snapshots.save_snapshot("report", snapshot_data)

    # Print the report
    print(report)
    print(f"\n  Saved: {report_path}\n")
