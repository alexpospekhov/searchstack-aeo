"""AEO citation check across ChatGPT, Perplexity, Claude, Grok, and local models (Ollama)."""

from __future__ import annotations

from searchstack import snapshots
from searchstack.config import Config

PROVIDERS = ("chatgpt", "perplexity", "claude", "grok", "ollama")


def _check_provider(
    provider: str,
    queries: list[str],
    config: Config,
) -> dict:
    """Run citation check for a single provider. Returns results dict."""
    results: list[dict] = []

    if provider == "chatgpt":
        if not config.openai.api_key:
            print(f"  Skipping ChatGPT -- OPENAI_API_KEY not configured")
            return {"provider": provider, "results": [], "cited": 0, "total": 0}
        from searchstack.providers import openai_client
        check_fn = openai_client.check_citation
    elif provider == "perplexity":
        if not config.perplexity.api_key:
            print(f"  Skipping Perplexity -- PERPLEXITY_API_KEY not configured")
            return {"provider": provider, "results": [], "cited": 0, "total": 0}
        from searchstack.providers import perplexity
        check_fn = perplexity.check_citation
    elif provider == "claude":
        if not config.anthropic.api_key:
            print(f"  Skipping Claude -- ANTHROPIC_API_KEY not configured")
            return {"provider": provider, "results": [], "cited": 0, "total": 0}
        from searchstack.providers import anthropic_client
        check_fn = anthropic_client.check_citation
    elif provider == "grok":
        if not config.grok.api_key:
            print(f"  Skipping Grok -- XAI_API_KEY not configured")
            return {"provider": provider, "results": [], "cited": 0, "total": 0}
        from searchstack.providers import grok
        check_fn = grok.check_citation
    elif provider == "ollama":
        if not config.ollama.model:
            print(f"  Skipping Ollama -- [ollama] model not configured")
            return {"provider": provider, "results": [], "cited": 0, "total": 0}
        from searchstack.providers import ollama
        check_fn = ollama.check_citation
    else:
        print(f"  Unknown provider: {provider}")
        return {"provider": provider, "results": [], "cited": 0, "total": 0}

    cited_count = 0

    for query in queries:
        try:
            # Provider check_citation functions are defined as
            # (config, query_text, domain); passing them as (query, domain,
            # config) means the first positional argument — a plain string —
            # gets used as `config`, and the very first attribute access
            # inside the provider (e.g. `config.openai.api_key`) raises
            # `AttributeError: 'str' object has no attribute 'openai'`. The
            # `ai` command was unable to complete even a single provider call
            # without this fix.
            result = check_fn(config, query, config.domain)
            is_cited = result.get("cited", False)
            url = result.get("url", "")
            # Persist the full provider response alongside the existing
            # fields. Providers return (text, citations, model, error) — the
            # original snapshot kept only (query, cited, url, raw), which
            # dropped the model's answer text and any competitor citations
            # it returned. On a zero-citation baseline this was nearly all of
            # the run's value: knowing that a domain isn't cited matters much
            # less than knowing which domains the model DID cite in its
            # place. Keeping the originals for backward compatibility.
            results.append({
                "query": query,
                "cited": is_cited,
                "url": url,
                "text": result.get("text", ""),
                "citations": result.get("citations", []),
                "model": result.get("model", ""),
                "error": result.get("error"),
                "raw": result.get("raw", ""),
            })

            if is_cited:
                cited_count += 1
                suffix = f"  -> {url}" if url else ""
                print(f'    "{query}"  \u2705 CITED{suffix}')
            else:
                # Surface the top competitor hostnames inline so a 0-citation
                # run still produces actionable positioning data at a glance.
                competitor_hosts: list[str] = []
                for c in result.get("citations") or []:
                    if isinstance(c, str) and "://" in c:
                        try:
                            host = c.split("://", 1)[1].split("/", 1)[0]
                            if host.startswith("www."):
                                host = host[4:]
                            if host and host not in competitor_hosts:
                                competitor_hosts.append(host)
                        except Exception:
                            pass
                if competitor_hosts:
                    hint = ", ".join(competitor_hosts[:3])
                    print(f'    "{query}"  \u274c not cited   [cites: {hint}]')
                else:
                    print(f'    "{query}"  \u274c not cited')
        except Exception as e:
            print(f'    "{query}"  \u26a0\ufe0f  error: {e}')
            results.append({
                "query": query,
                "cited": False,
                "error": str(e),
            })

    return {
        "provider": provider,
        "results": results,
        "cited": cited_count,
        "total": len(queries),
    }


def run(config: Config, *args: str) -> None:
    """Run AEO citation check.

    Usage:
        searchstack ai                # all three providers
        searchstack ai chatgpt        # ChatGPT only
        searchstack ai perplexity     # Perplexity only
        searchstack ai claude         # Claude only
    """
    if not config.ai_queries:
        print("No ai_queries configured in .searchstack.toml")
        print("Add queries like:")
        print('  ai_queries = ["best tool for X", "how to solve Y"]')
        return

    # Determine which providers to check
    if args and args[0] in PROVIDERS:
        providers = [args[0]]
    else:
        providers = list(PROVIDERS)

    print(f"\n  Checking AI citations for {config.domain}...\n")

    all_results: dict[str, dict] = {}
    summary_parts: list[str] = []

    for provider in providers:
        label = {
            "chatgpt": "ChatGPT (gpt-4o-mini)",
            "perplexity": "Perplexity (sonar)",
            "claude": "Claude (haiku)",
            "grok": "Grok (grok-3-mini)",
            "ollama": f"Ollama ({config.ollama.model or 'not configured'})",
        }.get(provider, provider)

        print(f"  {label}:")

        result = _check_provider(provider, config.ai_queries, config)
        all_results[provider] = result

        if result["total"] > 0:
            summary_parts.append(f'{provider.title()} {result["cited"]}/{result["total"]}')

        print()

    # Print summary
    if summary_parts:
        print(f"  Summary: {' | '.join(summary_parts)}")

    # Save snapshot
    snapshot_data = {
        "domain": config.domain,
        "queries": config.ai_queries,
        "providers": all_results,
    }
    path = snapshots.save_snapshot("ai_citations", snapshot_data)
    print(f"  Saved: {path}")
