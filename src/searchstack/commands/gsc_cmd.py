"""Google Search Console -- queries, pages, trend, inspect, sitemaps.

Named gsc_cmd.py to avoid confusion with providers/gsc.py.
"""

from __future__ import annotations

from datetime import date, timedelta

from searchstack.config import Config

DATE_RANGE_DAYS = 28


def _date_range() -> tuple[str, str]:
    """Return (start, end) date strings for the last 28 days."""
    end = date.today() - timedelta(days=3)  # GSC data has ~3 day lag
    start = end - timedelta(days=DATE_RANGE_DAYS)
    return start.isoformat(), end.isoformat()


def _fmt_ctr(ctr: float) -> str:
    """Format CTR as percentage."""
    return f"{ctr * 100:.1f}%"


def _fmt_pos(pos: float) -> str:
    """Format average position."""
    return f"{pos:.1f}"


def _ensure_gsc(config: Config):
    """Validate GSC config and return provider module, or None on failure."""
    if not config.gsc.site_url:
        print("GSC site_url not configured.")
        print("Set gsc.site_url in .searchstack.toml (e.g. 'https://yoursite.com/').")
        return None

    try:
        from searchstack.providers import gsc
        return gsc
    except Exception as e:
        print(f"Failed to load GSC provider: {e}")
        return None


def _top_queries(config: Config) -> None:
    """Default: top 30 queries by clicks."""
    gsc = _ensure_gsc(config)
    if gsc is None:
        return

    start, end = _date_range()

    print(f"\n  Google Search Console -- Top Queries")
    print(f"  Period: {start} to {end}\n")

    try:
        data = gsc.query(
            site_url=config.gsc.site_url,
            start_date=start,
            end_date=end,
            dimensions=["query"],
            row_limit=30,
            config=config,
        )
    except Exception as e:
        print(f"  Error fetching GSC data: {e}")
        return

    rows = data.get("rows", [])
    if not rows:
        print("  No query data available for this period.")
        return

    print(f"    {'#':>3s}  {'Query':40s} {'Clicks':>8s} {'Impr':>8s} {'CTR':>7s} {'Pos':>6s}")
    print(f"    {'---':>3s}  {'-'*40} {'-'*8} {'-'*8} {'-'*7} {'-'*6}")

    for i, row in enumerate(rows, 1):
        query = row.get("keys", [""])[0]
        clicks = row.get("clicks", 0)
        impressions = row.get("impressions", 0)
        ctr = row.get("ctr", 0.0)
        position = row.get("position", 0.0)

        display_query = query if len(query) <= 40 else query[:37] + "..."
        print(f"    {i:3d}  {display_query:40s} {clicks:8,d} {impressions:8,d} {_fmt_ctr(ctr):>7s} {_fmt_pos(position):>6s}")

    print(f"\n  {len(rows)} queries shown.")


def _pages_perf(config: Config) -> None:
    """Top pages by clicks."""
    gsc = _ensure_gsc(config)
    if gsc is None:
        return

    start, end = _date_range()

    print(f"\n  GSC -- Top Pages by Clicks")
    print(f"  Period: {start} to {end}\n")

    try:
        data = gsc.query(
            site_url=config.gsc.site_url,
            start_date=start,
            end_date=end,
            dimensions=["page"],
            row_limit=30,
            config=config,
        )
    except Exception as e:
        print(f"  Error: {e}")
        return

    rows = data.get("rows", [])
    if not rows:
        print("  No page data available.")
        return

    print(f"    {'#':>3s}  {'Page':55s} {'Clicks':>8s} {'Impr':>8s} {'CTR':>7s} {'Pos':>6s}")
    print(f"    {'---':>3s}  {'-'*55} {'-'*8} {'-'*8} {'-'*7} {'-'*6}")

    for i, row in enumerate(rows, 1):
        page = row.get("keys", [""])[0]
        clicks = row.get("clicks", 0)
        impressions = row.get("impressions", 0)
        ctr = row.get("ctr", 0.0)
        position = row.get("position", 0.0)

        # Strip domain prefix for readability
        display = page
        if config.gsc.site_url and page.startswith(config.gsc.site_url):
            display = page[len(config.gsc.site_url.rstrip("/")):]
        display = display if len(display) <= 55 else display[:52] + "..."

        print(f"    {i:3d}  {display:55s} {clicks:8,d} {impressions:8,d} {_fmt_ctr(ctr):>7s} {_fmt_pos(position):>6s}")


def _devices(config: Config) -> None:
    """Clicks/impressions by device."""
    gsc = _ensure_gsc(config)
    if gsc is None:
        return

    start, end = _date_range()

    print(f"\n  GSC -- Devices")
    print(f"  Period: {start} to {end}\n")

    try:
        data = gsc.query(
            site_url=config.gsc.site_url,
            start_date=start,
            end_date=end,
            dimensions=["device"],
            config=config,
        )
    except Exception as e:
        print(f"  Error: {e}")
        return

    rows = data.get("rows", [])
    if not rows:
        print("  No device data.")
        return

    print(f"    {'Device':15s} {'Clicks':>8s} {'Impr':>8s} {'CTR':>7s} {'Pos':>6s}")
    print(f"    {'-'*15} {'-'*8} {'-'*8} {'-'*7} {'-'*6}")

    for row in rows:
        device = row.get("keys", [""])[0]
        clicks = row.get("clicks", 0)
        impressions = row.get("impressions", 0)
        ctr = row.get("ctr", 0.0)
        position = row.get("position", 0.0)
        print(f"    {device:15s} {clicks:8,d} {impressions:8,d} {_fmt_ctr(ctr):>7s} {_fmt_pos(position):>6s}")


def _countries(config: Config) -> None:
    """Top countries by clicks."""
    gsc = _ensure_gsc(config)
    if gsc is None:
        return

    start, end = _date_range()

    print(f"\n  GSC -- Top Countries")
    print(f"  Period: {start} to {end}\n")

    try:
        data = gsc.query(
            site_url=config.gsc.site_url,
            start_date=start,
            end_date=end,
            dimensions=["country"],
            row_limit=20,
            config=config,
        )
    except Exception as e:
        print(f"  Error: {e}")
        return

    rows = data.get("rows", [])
    if not rows:
        print("  No country data.")
        return

    print(f"    {'Country':10s} {'Clicks':>8s} {'Impr':>8s} {'CTR':>7s} {'Pos':>6s}")
    print(f"    {'-'*10} {'-'*8} {'-'*8} {'-'*7} {'-'*6}")

    for row in rows:
        country = row.get("keys", [""])[0]
        clicks = row.get("clicks", 0)
        impressions = row.get("impressions", 0)
        ctr = row.get("ctr", 0.0)
        position = row.get("position", 0.0)
        print(f"    {country:10s} {clicks:8,d} {impressions:8,d} {_fmt_ctr(ctr):>7s} {_fmt_pos(position):>6s}")


def _trend(config: Config) -> None:
    """Daily click/impression trend."""
    gsc = _ensure_gsc(config)
    if gsc is None:
        return

    start, end = _date_range()

    print(f"\n  GSC -- Daily Trend")
    print(f"  Period: {start} to {end}\n")

    try:
        data = gsc.query(
            site_url=config.gsc.site_url,
            start_date=start,
            end_date=end,
            dimensions=["date"],
            config=config,
        )
    except Exception as e:
        print(f"  Error: {e}")
        return

    rows = data.get("rows", [])
    if not rows:
        print("  No trend data.")
        return

    max_clicks = max((r.get("clicks", 0) for r in rows), default=1) or 1

    print(f"    {'Date':12s} {'Clicks':>8s} {'Impr':>8s}")
    print(f"    {'-'*12} {'-'*8} {'-'*8}")

    for row in rows:
        day = row.get("keys", [""])[0]
        clicks = row.get("clicks", 0)
        impressions = row.get("impressions", 0)
        bar_len = round((clicks / max_clicks) * 20)
        bar = "\u2588" * bar_len
        print(f"    {day:12s} {clicks:8,d} {impressions:8,d}  {bar}")


def _sitemaps(config: Config) -> None:
    """List submitted sitemaps."""
    gsc = _ensure_gsc(config)
    if gsc is None:
        return

    print(f"\n  GSC -- Sitemaps\n")

    try:
        data = gsc.list_sitemaps(
            site_url=config.gsc.site_url,
            config=config,
        )
    except Exception as e:
        print(f"  Error: {e}")
        return

    sitemaps = data.get("sitemap", [])
    if not sitemaps:
        print("  No sitemaps found.")
        return

    for sm in sitemaps:
        path = sm.get("path", "")
        last_submitted = sm.get("lastSubmitted", "")
        is_pending = sm.get("isPending", False)
        warnings = sm.get("warnings", 0)
        errors = sm.get("errors", 0)

        status = "pending" if is_pending else "ok"
        print(f"    {path}")
        print(f"      Last submitted: {last_submitted}  Status: {status}  Warnings: {warnings}  Errors: {errors}")


def _inspect(config: Config, url: str) -> None:
    """Inspect a single URL for indexing status."""
    gsc = _ensure_gsc(config)
    if gsc is None:
        return

    print(f"\n  GSC -- URL Inspection")
    print(f"  URL: {url}\n")

    try:
        data = gsc.inspect_url(
            site_url=config.gsc.site_url,
            url=url,
            config=config,
        )
    except Exception as e:
        print(f"  Error: {e}")
        return

    result = data.get("inspectionResult", {})
    index_status = result.get("indexStatusResult", {})

    verdict = index_status.get("verdict", "UNKNOWN")
    coverage = index_status.get("coverageState", "")
    crawled = index_status.get("lastCrawlTime", "never")
    crawl_status = index_status.get("pageFetchState", "")
    robots = index_status.get("robotsTxtState", "")
    indexing = index_status.get("indexingState", "")

    icon = "\u2705" if verdict == "PASS" else "\u274c"
    print(f"    Verdict:     {icon} {verdict}")
    print(f"    Coverage:    {coverage}")
    print(f"    Last crawl:  {crawled}")
    print(f"    Fetch:       {crawl_status}")
    print(f"    Robots.txt:  {robots}")
    print(f"    Indexing:    {indexing}")


def _resubmit(config: Config) -> None:
    """Resubmit sitemap to Google."""
    gsc = _ensure_gsc(config)
    if gsc is None:
        return

    sitemap_url = config.sitemap
    if not sitemap_url:
        print("No sitemap URL configured. Set 'sitemap' in .searchstack.toml.")
        return

    print(f"\n  Resubmitting sitemap: {sitemap_url}\n")

    try:
        gsc.submit_sitemap(
            site_url=config.gsc.site_url,
            sitemap_url=sitemap_url,
            config=config,
        )
        print(f"  \u2705 Sitemap submitted successfully.")
    except Exception as e:
        print(f"  \u274c Error: {e}")


SUBCOMMANDS = {
    "pages-perf": _pages_perf,
    "devices": _devices,
    "countries": _countries,
    "trend": _trend,
    "sitemaps": _sitemaps,
    "resubmit": _resubmit,
}


def run(config: Config, *args: str) -> None:
    """Google Search Console commands.

    Usage:
        searchstack gsc                    # top queries
        searchstack gsc pages-perf         # top pages
        searchstack gsc devices            # device breakdown
        searchstack gsc countries          # country breakdown
        searchstack gsc trend              # daily trend
        searchstack gsc sitemaps           # list sitemaps
        searchstack gsc inspect <url>      # check URL indexing
        searchstack gsc resubmit           # resubmit sitemap
    """
    if not args:
        _top_queries(config)
        return

    subcmd = args[0]

    if subcmd == "inspect":
        if len(args) < 2:
            print("Usage: searchstack gsc inspect <url>")
            return
        _inspect(config, args[1])
        return

    handler = SUBCOMMANDS.get(subcmd)
    if handler is not None:
        handler(config)
    else:
        print(f"Unknown GSC subcommand: {subcmd}")
        print("Available: pages-perf, devices, countries, trend, sitemaps, inspect, resubmit")
