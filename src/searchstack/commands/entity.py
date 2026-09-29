"""Google Knowledge Graph Entity Authority check for brand & AEO optimization."""

from __future__ import annotations

import json
import os
import urllib.parse
import urllib.request
from typing import Any

from searchstack.config import Config


def _get_google_api_key(config: Config) -> str:
    """Find a Google API key from config or env."""
    return (
        os.environ.get("GOOGLE_API_KEY", "")
        or config.gemini.api_key
        or os.environ.get("GEMINI_API_KEY", "")
    )


def run(config: Config, *args: str) -> None:
    """Query Google Knowledge Graph Search API for entity recognition and authority."""
    query = " ".join(args) if args else config.domain.split(".")[0]
    if not query:
        print("Usage: searchstack entity \"brand or topic\"")
        return

    api_key = _get_google_api_key(config)
    if not api_key:
        print("Google API key missing.")
        print("Set GEMINI_API_KEY or GOOGLE_API_KEY in your environment, or [gemini] in .searchstack.toml.")
        return

    encoded_query = urllib.parse.quote(query)
    url = f"https://kgsearch.googleapis.com/v1/entities:search?query={encoded_query}&key={api_key}&limit=5&indent=True"

    print(f"\nChecking Google Knowledge Graph for entity: \"{query}\"...\n")

    try:
        req = urllib.request.Request(url, headers={"User-Agent": "searchstack/1.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except Exception as exc:
        print(f"Error querying Knowledge Graph API: {exc}")
        return

    elements = data.get("itemListElement", [])
    if not elements:
        print(f"[-] No entity found in Google Knowledge Graph for \"{query}\".")
        print("    Google has not yet reconciled this brand as an authority entity in its graph.")
        print("    Recommendation: Add Organization schema with sameAs links (Wikidata, Crunchbase, LinkedIn).\n")
        return

    print(f"[+] Found {len(elements)} entity match(es) in Google Knowledge Graph:\n")

    for idx, item in enumerate(elements, 1):
        result = item.get("result", {})
        score = item.get("resultScore", 0.0)
        name = result.get("name", "Unknown")
        types = ", ".join(result.get("@type", []))
        desc = result.get("description", "")
        detailed = result.get("detailedDescription", {}).get("articleBody", "")
        url_ref = result.get("url", "")

        print(f"  {idx}. {name} (Score: {score:.1f})")
        print(f"     Types:       {types}")
        if desc:
            print(f"     Description: {desc}")
        if detailed:
            print(f"     Summary:     {detailed[:120]}...")
        if url_ref:
            print(f"     Entity URL:  {url_ref}")
        print()
