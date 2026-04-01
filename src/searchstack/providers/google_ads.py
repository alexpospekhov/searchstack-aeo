"""Google Ads Keyword Planner provider.

Uses the google-ads Python library to fetch keyword ideas with monthly search
volumes.  The library is NOT in default deps (it's ~50 MB with protobuf),
so import errors are handled gracefully with install instructions.

Required credentials (config section [google_ads] or env vars):
  - developer_token   (GOOGLE_ADS_DEVELOPER_TOKEN)
  - customer_id       (GOOGLE_ADS_CUSTOMER_ID) -- no dashes
  - client_id         (google-ads-oauth-client-id)
  - client_secret     (google-ads-oauth-client-secret)
  - refresh_token     (google-ads-refresh-token)
"""

from __future__ import annotations

from searchstack.config import Config


def _load_client(config: Config):
    """Build a GoogleAdsClient from config credentials.

    Returns the client instance, or None if the library is missing or
    credentials are incomplete.
    """
    try:
        from google.ads.googleads.client import GoogleAdsClient  # type: ignore[import-untyped]
    except ImportError:
        print(
            "google-ads library not installed.\n"
            "Install it with:  pip install google-ads\n"
            "(~50 MB -- not included in searchstack's default dependencies)"
        )
        return None

    ga = config.google_ads
    if not ga.customer_id or not ga.developer_token:
        print(
            "Google Ads not configured.  Set [google_ads] in .searchstack.toml:\n"
            "  customer_id      = \"1234567890\"   # no dashes\n"
            "  developer_token  = \"XXXXXXXX\"\n"
            "  client_id        = \"...apps.googleusercontent.com\"\n"
            "  client_secret    = \"...\"\n"
            "  refresh_token    = \"...\"\n"
            "Or use env vars: GOOGLE_ADS_DEVELOPER_TOKEN, GOOGLE_ADS_CUSTOMER_ID"
        )
        return None

    credentials = {
        "developer_token": ga.developer_token,
        "client_id": ga.client_id,
        "client_secret": ga.client_secret,
        "refresh_token": ga.refresh_token,
        "use_proto_plus": True,
    }

    try:
        client = GoogleAdsClient.load_from_dict(credentials)
    except Exception as exc:
        print(f"Failed to initialise Google Ads client: {exc}")
        return None

    return client


def get_keyword_volumes(
    config: Config,
    seed_keywords: list[str],
) -> list[dict]:
    """Get keyword ideas with monthly volumes from Google Ads Keyword Planner.

    Returns list of dicts:
        {"keyword": str, "volume": int, "competition": str,
         "cpc_low": float, "cpc_high": float}

    Sorted by volume descending.  Returns an empty list on any error.
    """
    client = _load_client(config)
    if client is None:
        return []

    ga = config.google_ads

    keyword_plan_idea_service = client.get_service("KeywordPlanIdeaService")
    keyword_plan_network = client.enums.KeywordPlanNetworkEnum.GOOGLE_SEARCH

    # Location & language resource names
    location_code = ga.location_code or 2840
    location_rn = f"geoTargetConstants/{location_code}"

    # Map language_code string -> resource name ID
    _LANG_MAP = {
        "en": 1000, "es": 1003, "fr": 1002, "de": 1001, "pt": 1014,
        "ja": 1005, "zh": 1017, "ko": 1012, "it": 1004, "ru": 1031,
    }
    lang_id = _LANG_MAP.get(ga.language_code, 1000)
    language_rn = f"languageConstants/{lang_id}"

    request = client.get_type("GenerateKeywordIdeaRequest")
    request.customer_id = str(ga.customer_id).replace("-", "")
    request.language = language_rn
    request.geo_target_constants.append(location_rn)
    request.keyword_plan_network = keyword_plan_network
    request.keyword_seed.keywords.extend(seed_keywords)

    try:
        response = keyword_plan_idea_service.generate_keyword_ideas(request=request)
    except Exception as exc:
        print(f"Google Ads API error: {exc}")
        return []

    results: list[dict] = []
    for idea in response:
        metrics = idea.keyword_idea_metrics

        # Competition enum -> readable string
        comp_enum = metrics.competition
        comp_name = comp_enum.name if hasattr(comp_enum, "name") else str(comp_enum)

        # CPC micros -> dollars
        cpc_low = (metrics.low_top_of_page_bid_micros or 0) / 1_000_000
        cpc_high = (metrics.high_top_of_page_bid_micros or 0) / 1_000_000

        results.append({
            "keyword": idea.text,
            "volume": metrics.avg_monthly_searches or 0,
            "competition": comp_name,
            "cpc_low": round(cpc_low, 2),
            "cpc_high": round(cpc_high, 2),
        })

    results.sort(key=lambda r: r["volume"], reverse=True)
    return results
