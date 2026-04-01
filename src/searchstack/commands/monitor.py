"""Site health dashboard -- article performance monitor.

Pulls GSC performance + indexing data for every page in the sitemap,
tracks target keyword positions, compares with previous snapshots.
"""

from __future__ import annotations

import re
import urllib.request
from datetime import date, timedelta
from typing import Any

from searchstack.config import Config
from searchstack.providers.gsc import gsc_request, get_gsc_token, get_gsc_site_url_encoded
from searchstack.snapshots import save_snapshot, load_latest_snapshot


_UA = "Mozilla/5.0 SearchStack/1.0"
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
# 1. Overall traffic
# ---------------------------------------------------------------------------

def _overall_traffic(config: Config) -> dict[str, Any] | None:
    start, end = _date_range()
    site_url_enc = get_gsc_site_url_encoded(config)

    body = {
        "startDate": start,
        "endDate": end,
        "dimensions": [],
        "rowLimit": 1,
    }

    data = gsc_request(
        config,
        f"webmasters/v3/sites/{site_url_enc}/searchAnalytics/query",
        method="POST",
        body=body,
    )

    if data is None or "error" in data:
        print(f"  Error fetching overall traffic: {data}")
        return None

    rows = data.get("rows", [])
    if not rows:
        print("  No traffic data for this period.")
        return None

    row = rows[0]
    result = {
        "clicks": row.get("clicks", 0),
        "impressions": row.get("impressions", 0),
        "ctr": row.get("ctr", 0.0),
        "position": row.get("position", 0.0),
    }

    print(f"\n  Overall Traffic ({start} to {end})")
    print(f"  {'─' * 50}")
    print(f"    Clicks:      {result['clicks']:>10,}")
    print(f"    Impressions: {result['impressions']:>10,}")
    print(f"    Avg CTR:     {_fmt_ctr(result['ctr']):>10s}")
    print(f"    Avg Pos:     {_fmt_pos(result['position']):>10s}")

    return result


# ---------------------------------------------------------------------------
# 2. Article rankings (per-page GSC data + indexing)
# ---------------------------------------------------------------------------

def _article_rankings(config: Config, sitemap_urls: list[str]) -> list[dict]:
    start, end = _date_range()
    site_url_enc = get_gsc_site_url_encoded(config)

    # Fetch per-page performance
    body = {
        "startDate": start,
        "endDate": end,
        "dimensions": ["page"],
        "rowLimit": 500,
    }

    perf_data = gsc_request(
        config,
        f"webmasters/v3/sites/{site_url_enc}/searchAnalytics/query",
        method="POST",
        body=body,
    )

    perf_by_url: dict[str, dict] = {}
    if perf_data and "rows" in perf_data:
        for row in perf_data["rows"]:
            url = row.get("keys", [""])[0]
            perf_by_url[url] = {
                "clicks": row.get("clicks", 0),
                "impressions": row.get("impressions", 0),
                "ctr": row.get("ctr", 0.0),
                "position": row.get("position", 0.0),
            }

    # Inspect indexing status for each sitemap URL
    articles: list[dict] = []
    for url in sitemap_urls:
        perf = perf_by_url.get(url, {
            "clicks": 0, "impressions": 0, "ctr": 0.0, "position": 0.0,
        })

        # URL Inspection
        inspect_body = {
            "inspectionUrl": url,
            "siteUrl": config.gsc.site_url,
        }
        inspect_data = gsc_request(
            config,
            "v1/urlInspection/index:inspect",
            method="POST",
            body=inspect_body,
        )

        index_status = "unknown"
        if inspect_data and "error" not in inspect_data:
            result = inspect_data.get("inspectionResult", {})
            idx = result.get("indexStatusResult", {})
            verdict = idx.get("verdict", "UNKNOWN").upper()
            index_status = "indexed" if verdict == "PASS" else verdict.lower()

        articles.append({
            "url": url,
            "clicks": perf["clicks"],
            "impressions": perf["impressions"],
            "ctr": perf["ctr"],
            "position": perf["position"],
            "index_status": index_status,
        })

    # Sort by clicks descending
    articles.sort(key=lambda a: a["clicks"], reverse=True)

    # Print table
    print(f"\n  Article Rankings")
    print(f"  {'─' * 95}")

    page_w = 50
    print(f"    {'#':>3}  {'Page':<{page_w}}  {'Clicks':>7} {'Impr':>7} {'CTR':>6} {'Pos':>5}  {'Index':<10}")
    print(f"    {'───':>3}  {'─' * page_w}  {'─' * 7} {'─' * 7} {'─' * 6} {'─' * 5}  {'─' * 10}")

    for i, art in enumerate(articles, 1):
        path = _short_url(art["url"], config.domain)
        if len(path) > page_w:
            path = path[:page_w - 3] + "..."

        icon = "\u2705" if art["index_status"] == "indexed" else "\u274c"
        print(
            f"    {i:3d}  {path:<{page_w}}  "
            f"{art['clicks']:7,d} {art['impressions']:7,d} "
            f"{_fmt_ctr(art['ctr']):>6s} {_fmt_pos(art['position']):>5s}  "
            f"{icon} {art['index_status']}"
        )

    return articles


# ---------------------------------------------------------------------------
# 3. Target keyword tracking
# ---------------------------------------------------------------------------

def _keyword_tracking(config: Config) -> list[dict]:
    geo_keywords = config.geo_keywords
    if not geo_keywords:
        print("\n  Target Keyword Tracking: no geo_keywords configured.")
        return []

    start, end = _date_range()
    site_url_enc = get_gsc_site_url_encoded(config)

    # Collect all target keywords
    all_keywords: list[str] = []
    for keywords in geo_keywords.values():
        all_keywords.extend(keywords)
    all_keywords = list(set(all_keywords))

    if not all_keywords:
        return []

    # Fetch query+page data from GSC
    body = {
        "startDate": start,
        "endDate": end,
        "dimensions": ["query", "page"],
        "rowLimit": 500,
    }

    data = gsc_request(
        config,
        f"webmasters/v3/sites/{site_url_enc}/searchAnalytics/query",
        method="POST",
        body=body,
    )

    rows = data.get("rows", []) if data and "error" not in data else []

    # Build lookup: keyword -> best page performance
    kw_perf: dict[str, dict] = {}
    for row in rows:
        keys = row.get("keys", [])
        if len(keys) < 2:
            continue
        query, page = keys[0], keys[1]
        if query not in kw_perf or row.get("clicks", 0) > kw_perf[query].get("clicks", 0):
            kw_perf[query] = {
                "page": page,
                "clicks": row.get("clicks", 0),
                "impressions": row.get("impressions", 0),
                "position": row.get("position", 0.0),
            }

    # Report
    results: list[dict] = []
    ranking: list[dict] = []
    not_ranking: list[str] = []

    for kw in sorted(all_keywords):
        kw_lower = kw.lower()
        if kw_lower in kw_perf:
            perf = kw_perf[kw_lower]
            entry = {"keyword": kw, **perf}
            results.append(entry)
            ranking.append(entry)
        else:
            results.append({"keyword": kw, "page": "", "clicks": 0, "impressions": 0, "position": 0})
            not_ranking.append(kw)

    print(f"\n  Target Keyword Tracking ({len(all_keywords)} keywords)")
    print(f"  {'─' * 95}")

    if ranking:
        kw_w = max(len(r["keyword"]) for r in ranking)
        kw_w = max(kw_w, 7)
        kw_w = min(kw_w, 35)

        print(f"    {'Keyword':<{kw_w}}  {'Pos':>5} {'Impr':>7} {'Clicks':>7}  {'Best Page'}")
        print(f"    {'─' * kw_w}  {'─' * 5} {'─' * 7} {'─' * 7}  {'─' * 40}")

        for r in sorted(ranking, key=lambda x: x["position"]):
            kw_display = r["keyword"] if len(r["keyword"]) <= kw_w else r["keyword"][:kw_w - 3] + "..."
            page_display = _short_url(r["page"], config.domain) if r["page"] else ""
            if len(page_display) > 40:
                page_display = page_display[:37] + "..."
            print(
                f"    {kw_display:<{kw_w}}  "
                f"{_fmt_pos(r['position']):>5s} {r['impressions']:7,d} {r['clicks']:7,d}  "
                f"{page_display}"
            )

    if not_ranking:
        print(f"\n    Not ranking ({len(not_ranking)}):")
        for kw in not_ranking:
            print(f"      \u274c {kw}")

    return results


# ---------------------------------------------------------------------------
# 4. Sitemap health
# ---------------------------------------------------------------------------

def _sitemap_health(config: Config) -> list[dict]:
    site_url_enc = get_gsc_site_url_encoded(config)

    data = gsc_request(
        config,
        f"webmasters/v3/sites/{site_url_enc}/sitemaps",
        method="GET",
    )

    if data is None or "error" in data:
        print(f"\n  Sitemap Health: Error fetching sitemaps -- {data}")
        return []

    sitemaps = data.get("sitemap", [])
    if not sitemaps:
        print("\n  Sitemap Health: no sitemaps found in GSC.")
        return []

    print(f"\n  Sitemap Health")
    print(f"  {'─' * 80}")

    results: list[dict] = []
    for sm in sitemaps:
        path = sm.get("path", "")
        last_submitted = sm.get("lastSubmitted", "")
        last_downloaded = sm.get("lastDownloaded", "")
        is_pending = sm.get("isPending", False)
        warnings_count = sm.get("warnings", 0)
        errors_count = sm.get("errors", 0)

        # Content details
        contents = sm.get("contents", [])
        total_submitted = sum(c.get("submitted", 0) for c in contents)
        total_indexed = sum(c.get("indexed", 0) for c in contents)

        status = "pending" if is_pending else "ok"
        icon = "\u26a0\ufe0f" if is_pending or errors_count or warnings_count else "\u2705"

        print(f"    {icon} {path}")
        print(f"      Submitted: {last_submitted[:10] if last_submitted else 'never'}")
        print(f"      Downloaded: {last_downloaded[:10] if last_downloaded else 'never'}")
        print(f"      URLs: {total_submitted} submitted, {total_indexed} indexed")
        if warnings_count or errors_count:
            print(f"      Warnings: {warnings_count}  Errors: {errors_count}")

        results.append({
            "path": path,
            "status": status,
            "last_submitted": last_submitted,
            "last_downloaded": last_downloaded,
            "urls_submitted": total_submitted,
            "urls_indexed": total_indexed,
            "warnings": warnings_count,
            "errors": errors_count,
        })

    return results


# ---------------------------------------------------------------------------
# 6. Compare with previous snapshot
# ---------------------------------------------------------------------------

def _compare_with_previous(
    current: dict[str, Any],
    previous: dict[str, Any] | None,
) -> None:
    if previous is None:
        print("\n  Comparison: no previous monitor snapshot found (first run).")
        return

    print(f"\n  Changes Since Last Snapshot")
    print(f"  {'─' * 60}")

    # Overall traffic delta
    prev_traffic = previous.get("overall_traffic", {})
    curr_traffic = current.get("overall_traffic", {})

    if prev_traffic and curr_traffic:
        for metric in ("clicks", "impressions"):
            prev_val = prev_traffic.get(metric, 0)
            curr_val = curr_traffic.get(metric, 0)
            delta = curr_val - prev_val
            pct = (delta / prev_val * 100) if prev_val else 0
            arrow = "\u2191" if delta > 0 else "\u2193" if delta < 0 else "="
            print(f"    {metric.capitalize():15s}  {prev_val:>8,} -> {curr_val:>8,}  {arrow} {delta:+,} ({pct:+.1f}%)")

        # Position (lower is better)
        prev_pos = prev_traffic.get("position", 0)
        curr_pos = curr_traffic.get("position", 0)
        pos_delta = prev_pos - curr_pos  # positive = improved
        arrow = "\u2191" if pos_delta > 0 else "\u2193" if pos_delta < 0 else "="
        print(f"    {'Avg Position':15s}  {_fmt_pos(prev_pos):>8s} -> {_fmt_pos(curr_pos):>8s}  {arrow} {pos_delta:+.1f}")

    # Per-page delta
    prev_articles = {a["url"]: a for a in previous.get("articles", [])}
    curr_articles = {a["url"]: a for a in current.get("articles", [])}

    improved: list[tuple[str, float, float]] = []
    declined: list[tuple[str, float, float]] = []

    for url, curr in curr_articles.items():
        if url in prev_articles:
            prev_pos = prev_articles[url].get("position", 0)
            curr_pos = curr.get("position", 0)
            delta = prev_pos - curr_pos
            if delta > 0.5:
                improved.append((url, prev_pos, curr_pos))
            elif delta < -0.5:
                declined.append((url, prev_pos, curr_pos))

    if improved:
        print(f"\n    Position improvements:")
        for url, prev_p, curr_p in sorted(improved, key=lambda x: x[1] - x[2], reverse=True)[:10]:
            path = _short_url(url, "")
            if len(path) > 45:
                path = path[:42] + "..."
            print(f"      \u2191 {path:<45s}  {_fmt_pos(prev_p)} -> {_fmt_pos(curr_p)}")

    if declined:
        print(f"\n    Position declines:")
        for url, prev_p, curr_p in sorted(declined, key=lambda x: x[2] - x[1], reverse=True)[:10]:
            path = _short_url(url, "")
            if len(path) > 45:
                path = path[:42] + "..."
            print(f"      \u2193 {path:<45s}  {_fmt_pos(prev_p)} -> {_fmt_pos(curr_p)}")

    if not improved and not declined:
        print("\n    No significant position changes.")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def run(config: Config, *args: str) -> None:
    """Site health dashboard -- article performance monitor.

    Usage:
        searchstack monitor
    """
    if not _ensure_gsc(config):
        return

    # 1. Overall traffic
    overall = _overall_traffic(config)

    # 2. Article rankings
    sitemap_urls: list[str] = []
    if config.sitemap:
        print(f"\n  Fetching sitemap: {config.sitemap}")
        sitemap_urls = _fetch_sitemap_urls(config.sitemap)
        print(f"  Found {len(sitemap_urls)} URLs in sitemap.")

    articles: list[dict] = []
    if sitemap_urls:
        articles = _article_rankings(config, sitemap_urls)
    else:
        print("\n  No sitemap configured -- skipping article rankings.")

    # 3. Target keyword tracking
    keywords = _keyword_tracking(config)

    # 4. Sitemap health
    sitemaps = _sitemap_health(config)

    # 5. Save snapshot
    snapshot = {
        "date": date.today().isoformat(),
        "overall_traffic": overall or {},
        "articles": articles,
        "keywords": keywords,
        "sitemaps": sitemaps,
    }

    path = save_snapshot("monitor", snapshot)
    print(f"\n  Snapshot saved: {path}")

    # 6. Compare with previous
    previous = load_latest_snapshot("monitor")
    # load_latest_snapshot returns the CURRENT one we just saved if it's the only one,
    # so check if dates differ
    if previous and previous.get("date") != snapshot["date"]:
        _compare_with_previous(snapshot, previous)
    elif previous and previous.get("date") == snapshot["date"]:
        # Same date -- try to find a truly older one by looking at files
        import json
        from pathlib import Path
        from searchstack.snapshots import get_snapshot_dir

        snap_dir = get_snapshot_dir()
        matches = sorted(snap_dir.glob("monitor_*.json"))
        if len(matches) >= 2:
            second_latest = matches[-2]
            try:
                with open(second_latest, "r", encoding="utf-8") as f:
                    prev_data = json.load(f)
                _compare_with_previous(snapshot, prev_data)
            except (json.JSONDecodeError, OSError):
                print("\n  Comparison: could not load previous snapshot.")
        else:
            print("\n  Comparison: first run -- no previous data to compare.")
    else:
        print("\n  Comparison: first run -- no previous data to compare.")

    # Summary
    indexed_count = sum(1 for a in articles if a.get("index_status") == "indexed")
    total_clicks = sum(a.get("clicks", 0) for a in articles)
    print(f"\n  Summary: {len(articles)} pages, {indexed_count} indexed, {total_clicks:,} total clicks")
