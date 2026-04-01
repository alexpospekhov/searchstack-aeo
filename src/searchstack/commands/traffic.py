"""Traffic analytics via Plausible -- visitors, sources, AI referrals."""

from __future__ import annotations

from searchstack.config import Config

AI_REFERRERS = ["chatgpt.com", "perplexity.ai", "claude.ai"]


def _bar(value: int, max_value: int, width: int = 20) -> str:
    """Render a simple text bar chart segment."""
    if max_value == 0:
        return ""
    filled = round((value / max_value) * width)
    return "\u2588" * filled + "\u2591" * (width - filled)


def _fmt_num(n: int | float) -> str:
    """Format number with comma separators."""
    if isinstance(n, float):
        return f"{n:,.1f}"
    return f"{n:,}"


def run(config: Config, *args: str) -> None:
    """Display Plausible traffic analytics with AI referral tracking.

    Usage:
        searchstack traffic
    """
    if not config.plausible.api_key:
        print("Plausible API key not configured.")
        print("Set plausible.api_key in .searchstack.toml or PLAUSIBLE_API_KEY env var.")
        return
    if not config.plausible.site_id:
        print("Plausible site_id not configured.")
        print("Set plausible.site_id in .searchstack.toml (e.g. 'yoursite.com').")
        return

    from searchstack.providers import plausible

    site_id = config.plausible.site_id
    api_key = config.plausible.api_key
    period = "30d"

    print(f"\n  Traffic for {site_id} (last 30 days)\n")

    # -- Overview metrics --
    try:
        overview = plausible.aggregate(
            site_id=site_id,
            api_key=api_key,
            period=period,
            metrics=["visitors", "visits", "pageviews", "bounce_rate"],
        )
        results = overview.get("results", {})

        visitors = results.get("visitors", {}).get("value", 0)
        visits = results.get("visits", {}).get("value", 0)
        pageviews = results.get("pageviews", {}).get("value", 0)
        bounce_rate = results.get("bounce_rate", {}).get("value", 0)

        print(f"  Overview:")
        print(f"    Visitors:    {_fmt_num(visitors)}")
        print(f"    Visits:      {_fmt_num(visits)}")
        print(f"    Pageviews:   {_fmt_num(pageviews)}")
        print(f"    Bounce rate: {bounce_rate}%")
        print()
    except Exception as e:
        print(f"  Overview: error -- {e}\n")

    # -- Top sources --
    try:
        sources = plausible.breakdown(
            site_id=site_id,
            api_key=api_key,
            period=period,
            property="visit:source",
            metrics=["visitors"],
            limit=15,
        )
        source_results = sources.get("results", [])

        if source_results:
            print(f"  Top Sources:")
            max_v = source_results[0].get("visitors", 1) if source_results else 1
            for row in source_results:
                name = row.get("source", "(direct)")
                v = row.get("visitors", 0)
                bar = _bar(v, max_v, 15)
                print(f"    {bar} {name:30s} {_fmt_num(v)}")
            print()
    except Exception as e:
        print(f"  Sources: error -- {e}\n")

    # -- AI referrals --
    try:
        print(f"  AI Referrals:")
        found_any = False
        for referrer in AI_REFERRERS:
            ai_data = plausible.breakdown(
                site_id=site_id,
                api_key=api_key,
                period=period,
                property="visit:source",
                metrics=["visitors", "visits", "pageviews"],
                filters=[["is", "visit:source", [referrer]]],
                limit=1,
            )
            ai_results = ai_data.get("results", [])
            if ai_results:
                found_any = True
                row = ai_results[0]
                v = row.get("visitors", 0)
                vis = row.get("visits", 0)
                pv = row.get("pageviews", 0)
                print(f"    {referrer:25s} {_fmt_num(v)} visitors, {_fmt_num(vis)} visits, {_fmt_num(pv)} pageviews")
            else:
                print(f"    {referrer:25s} --")
        if not found_any:
            print(f"    No AI referral traffic detected in the last 30 days.")
        print()
    except Exception as e:
        print(f"  AI Referrals: error -- {e}\n")

    # -- Channels --
    try:
        channels = plausible.breakdown(
            site_id=site_id,
            api_key=api_key,
            period=period,
            property="visit:channel",
            metrics=["visitors"],
            limit=10,
        )
        channel_results = channels.get("results", [])
        if channel_results:
            print(f"  Channels:")
            for row in channel_results:
                name = row.get("channel", "unknown")
                v = row.get("visitors", 0)
                print(f"    {name:25s} {_fmt_num(v)}")
            print()
    except Exception as e:
        print(f"  Channels: error -- {e}\n")

    # -- Countries --
    try:
        countries = plausible.breakdown(
            site_id=site_id,
            api_key=api_key,
            period=period,
            property="visit:country",
            metrics=["visitors"],
            limit=10,
        )
        country_results = countries.get("results", [])
        if country_results:
            print(f"  Countries:")
            for row in country_results:
                name = row.get("country", "??")
                v = row.get("visitors", 0)
                print(f"    {name:25s} {_fmt_num(v)}")
            print()
    except Exception as e:
        print(f"  Countries: error -- {e}\n")

    # -- Devices --
    try:
        devices = plausible.breakdown(
            site_id=site_id,
            api_key=api_key,
            period=period,
            property="visit:device",
            metrics=["visitors"],
            limit=5,
        )
        device_results = devices.get("results", [])
        if device_results:
            print(f"  Devices:")
            for row in device_results:
                name = row.get("device", "unknown")
                v = row.get("visitors", 0)
                print(f"    {name:25s} {_fmt_num(v)}")
            print()
    except Exception as e:
        print(f"  Devices: error -- {e}\n")

    # -- Top pages --
    try:
        pages = plausible.breakdown(
            site_id=site_id,
            api_key=api_key,
            period=period,
            property="event:page",
            metrics=["visitors", "pageviews"],
            limit=15,
        )
        page_results = pages.get("results", [])
        if page_results:
            print(f"  Top Pages:")
            print(f"    {'Page':50s} {'Visitors':>10s} {'Views':>10s}")
            print(f"    {'-'*50} {'-'*10} {'-'*10}")
            for row in page_results:
                page = row.get("page", "/")
                v = row.get("visitors", 0)
                pv = row.get("pageviews", 0)
                # Truncate long paths
                display_page = page if len(page) <= 50 else page[:47] + "..."
                print(f"    {display_page:50s} {_fmt_num(v):>10s} {_fmt_num(pv):>10s}")
            print()
    except Exception as e:
        print(f"  Pages: error -- {e}\n")

    # -- Daily trend (last 7 days) --
    try:
        trend = plausible.timeseries(
            site_id=site_id,
            api_key=api_key,
            period="7d",
            metrics=["visitors"],
        )
        trend_results = trend.get("results", [])
        if trend_results:
            print(f"  Daily Trend (7 days):")
            max_v = max((r.get("visitors", 0) for r in trend_results), default=1) or 1
            for row in trend_results:
                date = row.get("date", "")
                v = row.get("visitors", 0)
                bar = _bar(v, max_v, 25)
                # Show just the date portion
                day = date[:10] if len(date) >= 10 else date
                print(f"    {day}  {bar} {_fmt_num(v)}")
            print()
    except Exception as e:
        print(f"  Daily trend: error -- {e}\n")
