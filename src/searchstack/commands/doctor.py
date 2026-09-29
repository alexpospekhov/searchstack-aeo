"""Live capability doctor for the unified SEO runtime."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from searchstack import snapshots
from searchstack.config import Config


def _result(
    name: str,
    status: str,
    detail: str,
    *,
    endpoint: str = "",
    model: str = "",
) -> dict[str, Any]:
    return {
        "name": name,
        "status": status,
        "detail": detail,
        "endpoint": endpoint,
        "model": model,
    }


def _check_gsc(config: Config) -> dict[str, Any]:
    from searchstack.providers.gsc import get_gsc_token, list_sitemaps

    credentials_path = Path(config.gsc.credentials_file)
    token_path = credentials_path.parent / "token.pickle"

    if not credentials_path.is_file():
        return _result("Google Search Console", "error", f"credentials file missing: {credentials_path}")
    if not token_path.is_file():
        return _result("Google Search Console", "error", f"token.pickle missing next to {credentials_path.name}")

    token = get_gsc_token(config)
    if not token:
        return _result("Google Search Console", "error", "OAuth token unavailable or refresh failed")

    data = list_sitemaps(site_url=config.gsc.site_url, config=config)
    if "error" in data:
        return _result("Google Search Console", "error", data["error"], endpoint="webmasters/v3 + urlInspection")

    return _result(
        "Google Search Console",
        "ok",
        f"OAuth + sitemap access OK ({len(data.get('sitemap', []))} sitemaps)",
        endpoint="webmasters/v3 + urlInspection",
    )


def _check_dataforseo_core(config: Config) -> dict[str, Any]:
    from searchstack.providers.dataforseo import api_request, get_language_code, get_location_code

    if not config.dataforseo.login or not config.dataforseo.password:
        return _result("DataForSEO Core", "error", "credentials not configured")

    body = [{
        "target": config.domain,
        "location_code": get_location_code(config),
        "language_code": get_language_code(config),
        "limit": 1,
    }]
    data = api_request(config, "dataforseo_labs/google/ranked_keywords/live", body)
    if "error" in data:
        return _result("DataForSEO Core", "error", data["error"], endpoint="dataforseo_labs/google/*")

    tasks = data.get("tasks", [])
    if not tasks:
        return _result("DataForSEO Core", "error", "no tasks returned", endpoint="dataforseo_labs/google/*")

    task = tasks[0]
    if task.get("status_code") != 20000:
        return _result(
            "DataForSEO Core",
            "error",
            task.get("status_message", "unexpected task status"),
            endpoint="dataforseo_labs/google/*",
        )

    return _result("DataForSEO Core", "ok", "Labs/SERP auth and live request OK", endpoint="dataforseo_labs/google/*")


def _check_dataforseo_backlinks(config: Config) -> dict[str, Any]:
    from searchstack.providers.dataforseo import api_request

    if not config.dataforseo.login or not config.dataforseo.password:
        return _result("DataForSEO Backlinks", "error", "core credentials not configured")

    data = api_request(config, "backlinks/summary/live", [{"target": config.domain}])
    if "error" in data:
        return _result("DataForSEO Backlinks", "error", data["error"], endpoint="backlinks/*")

    tasks = data.get("tasks", [])
    if not tasks:
        return _result("DataForSEO Backlinks", "error", "no tasks returned", endpoint="backlinks/*")

    task = tasks[0]
    code = task.get("status_code")
    if code == 40204:
        return _result(
            "DataForSEO Backlinks",
            "warn",
            "configured but plan-gated (40204 access denied)",
            endpoint="backlinks/*",
        )
    if code != 20000:
        return _result(
            "DataForSEO Backlinks",
            "error",
            task.get("status_message", "unexpected task status"),
            endpoint="backlinks/*",
        )

    return _result("DataForSEO Backlinks", "ok", "subscription active and endpoint reachable", endpoint="backlinks/*")


def _check_plausible(config: Config) -> dict[str, Any]:
    from searchstack.providers.plausible import query

    if not config.plausible.api_key or not config.plausible.site_id:
        return _result("Plausible", "error", "api key or site_id missing")

    data = query(config, {"metrics": ["visitors"], "date_range": "1d"})
    if "error" in data:
        return _result("Plausible", "error", data["error"], endpoint="POST /api/v2/query")

    visitors = 0
    results = data.get("results", [])
    if results:
        metrics = results[0].get("metrics", [])
        if metrics:
            visitors = metrics[0]

    return _result("Plausible", "ok", f"query OK ({visitors} visitors in last 1d)", endpoint="POST /api/v2/query")


def _check_google_ads(config: Config) -> dict[str, Any]:
    from searchstack.providers import google_ads

    client = google_ads._load_client(config)
    if client is None:
        return _result("Google Ads", "error", "client init failed or credentials missing")

    test_kw = [config.domain] if config.domain else ["search engine optimization"]
    ideas = google_ads.get_keyword_volumes(config, test_kw)
    if not ideas:
        return _result(
            "Google Ads",
            "warn",
            "client loaded but no keyword ideas returned",
            endpoint="KeywordPlanIdeaService.GenerateKeywordIdeas",
        )

    return _result(
        "Google Ads",
        "ok",
        f"keyword planner OK ({len(ideas)} ideas returned)",
        endpoint="KeywordPlanIdeaService.GenerateKeywordIdeas",
    )


def _check_openai(config: Config) -> dict[str, Any]:
    from searchstack.providers import openai_client

    if not config.openai.api_key:
        return _result("OpenAI", "error", "api key missing", model=openai_client.MODEL)

    data = openai_client.check_citation(config, f"What is {config.domain}?", config.domain)
    if data.get("error"):
        return _result("OpenAI", "error", str(data["error"]), endpoint="/v1/chat/completions", model=openai_client.MODEL)

    return _result(
        "OpenAI",
        "warn",
        "runtime works via chat/completions; Responses migration still pending",
        endpoint="/v1/chat/completions",
        model=openai_client.MODEL,
    )


def _check_perplexity(config: Config) -> dict[str, Any]:
    from searchstack.providers import perplexity

    if not config.perplexity.api_key:
        return _result("Perplexity", "error", "api key missing", model=perplexity.MODEL)

    data = perplexity.check_citation(config, f"What is {config.domain}?", config.domain)
    if data.get("error"):
        return _result("Perplexity", "error", str(data["error"]), endpoint="/chat/completions", model=perplexity.MODEL)

    return _result("Perplexity", "ok", "Sonar chat-completions check OK", endpoint="/chat/completions", model=perplexity.MODEL)


def _check_anthropic(config: Config) -> dict[str, Any]:
    from searchstack.providers import anthropic_client

    if not config.anthropic.api_key:
        return _result("Anthropic", "error", "api key missing", model=anthropic_client.MODEL)

    data = anthropic_client.check_citation(config, f"What is {config.domain}?", config.domain)
    if data.get("error"):
        return _result("Anthropic", "error", str(data["error"]), endpoint="/v1/messages", model=anthropic_client.MODEL)

    return _result("Anthropic", "ok", "Messages API check OK", endpoint="/v1/messages", model=anthropic_client.MODEL)


def _check_grok(config: Config) -> dict[str, Any]:
    from searchstack.providers import grok

    if not config.grok.api_key:
        return _result("xAI", "error", "api key missing", model="grok-3-mini")

    data = grok.check_citation(config, f"What is {config.domain}?", config.domain)
    if data.get("error"):
        return _result("xAI", "error", str(data["error"]), endpoint="/v1/chat/completions", model="grok-3-mini")

    return _result(
        "xAI",
        "warn",
        "runtime works via legacy chat-completions; Responses migration pending",
        endpoint="/v1/chat/completions",
        model="grok-3-mini",
    )


def _check_gemini(config: Config) -> dict[str, Any]:
    from searchstack.providers import gemini

    if not config.gemini.api_key:
        return _result("Gemini", "error", "api key missing", model=gemini.MODEL)

    data = gemini.check_citation(config, f"What is {config.domain}?", config.domain)
    if data.get("error"):
        return _result("Gemini", "error", str(data["error"]), endpoint="generateContent", model=gemini.MODEL)

    n = len(data.get("citations") or [])
    return _result("Gemini", "ok", f"generateContent + Search grounding OK ({n} sources)",
                   endpoint="generateContent", model=gemini.MODEL)


def _check_bing(config: Config) -> dict[str, Any]:
    from searchstack.providers.bing import bing_request, get_site_url

    if not config.bing.api_key:
        return _result("Bing Webmaster", "error", "api key missing")

    site_url = get_site_url(config)
    data = bing_request(config, f"GetUrlSubmissionQuota?siteUrl={site_url}")
    if "error" in data:
        return _result("Bing Webmaster", "error", data["error"], endpoint="GetUrlSubmissionQuota")

    quota = data.get("d", {})
    daily = quota.get("DailyQuota", "?") if isinstance(quota, dict) else "?"
    return _result("Bing Webmaster", "ok", f"quota API OK (daily={daily})", endpoint="GetUrlSubmissionQuota")


def _check_indexnow(config: Config) -> dict[str, Any]:
    if not config.indexnow.key:
        return _result("IndexNow", "error", "key missing")

    key = config.indexnow.key.strip()
    candidates = [Path(f"{key}.txt"), Path("public") / f"{key}.txt"]
    for cand in candidates:
        if cand.is_file():
            file_key = cand.read_text(encoding="utf-8").strip()
            if file_key == key:
                return _result("IndexNow", "ok", f"key and hosted key file ({cand}) verified", endpoint="api.indexnow.org/indexnow")
            return _result("IndexNow", "warn", f"key in {cand} differs from config", endpoint="api.indexnow.org/indexnow")

    return _result("IndexNow", "ok", f"key configured ({key})", endpoint="api.indexnow.org/indexnow")


def _check_ollama(config: Config) -> dict[str, Any]:
    if not config.ollama.model:
        return _result("Ollama", "warn", "optional local provider not configured", endpoint=config.ollama.base_url)
    return _result("Ollama", "ok", "local provider configured", endpoint=config.ollama.base_url, model=config.ollama.model)


def _print_result(result: dict[str, Any]) -> None:
    icon = {
        "ok": "OK",
        "warn": "WARN",
        "error": "ERR",
    }.get(result["status"], "INFO")
    line = f"[{icon}] {result['name']}: {result['detail']}"
    extras = [value for value in (result.get("model"), result.get("endpoint")) if value]
    if extras:
        line = f"{line} ({' | '.join(extras)})"
    print(line)


def run(config: Config, *args: str) -> None:
    """Run a live capability check across the SEO service stack."""
    del args

    print(f"\nsearchstack doctor -- {config.domain}\n")
    print("This command performs live provider checks and may consume small API credits.\n")

    checks = [
        _check_gsc(config),
        _check_dataforseo_core(config),
        _check_dataforseo_backlinks(config),
        _check_plausible(config),
        _check_google_ads(config),
        _check_openai(config),
        _check_perplexity(config),
        _check_anthropic(config),
        _check_grok(config),
        _check_gemini(config),
        _check_bing(config),
        _check_indexnow(config),
    ]

    counts = {"ok": 0, "warn": 0, "error": 0}
    for item in checks:
        counts[item["status"]] += 1
        _print_result(item)

    snapshot_path = snapshots.save_snapshot("doctor", {
        "domain": config.domain,
        "results": checks,
        "summary": counts,
    })

    print("\nSummary:")
    print(f"- ok: {counts['ok']}")
    print(f"- warn: {counts['warn']}")
    print(f"- error: {counts['error']}")
    print(f"- docs: https://github.com/alexpospekhov/searchstack-aeo/blob/main/docs/SERVICES.md")
    print(f"- snapshot: {snapshot_path}\n")
