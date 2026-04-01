"""JSON-LD structured data validation for all sitemap URLs."""

from __future__ import annotations

import json
import re
import urllib.request
from html.parser import HTMLParser
from typing import Any

from searchstack.config import Config


_UA = "Mozilla/5.0 SearchStack/1.0"


# ---------------------------------------------------------------------------
# Reuse sitemap fetch from meta module
# ---------------------------------------------------------------------------

def _fetch_sitemap_urls(sitemap_url: str) -> list[str]:
    """Fetch sitemap XML and extract all <loc> URLs."""
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


def _filter_html_urls(urls: list[str]) -> list[str]:
    skip = (".xml", ".txt", ".md", ".json", ".pdf", ".jpg", ".png", ".svg", ".css", ".js")
    return [u for u in urls if not any(u.lower().endswith(ext) for ext in skip)]


# ---------------------------------------------------------------------------
# JSON-LD extraction
# ---------------------------------------------------------------------------

class _JsonLdParser(HTMLParser):
    """Extract all <script type="application/ld+json"> blocks."""

    def __init__(self) -> None:
        super().__init__()
        self.blocks: list[str] = []
        self._in_jsonld = False
        self._buf = ""

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "script":
            attr_dict = {k.lower(): (v or "").lower() for k, v in attrs}
            if attr_dict.get("type") == "application/ld+json":
                self._in_jsonld = True
                self._buf = ""

    def handle_endtag(self, tag: str) -> None:
        if tag == "script" and self._in_jsonld:
            self.blocks.append(self._buf)
            self._in_jsonld = False

    def handle_data(self, data: str) -> None:
        if self._in_jsonld:
            self._buf += data


def _extract_schemas(url: str) -> dict[str, Any]:
    """Fetch a URL and extract JSON-LD schemas."""
    req = urllib.request.Request(url, headers={"User-Agent": _UA})
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            html = resp.read().decode("utf-8", errors="replace")
    except Exception as exc:
        return {"url": url, "error": str(exc), "schemas": [], "issues": ["FETCH ERROR"]}

    parser = _JsonLdParser()
    try:
        parser.feed(html)
    except Exception:
        pass

    schemas: list[str] = []
    issues: list[str] = []

    if not parser.blocks:
        issues.append("NO JSON-LD")
        return {"url": url, "schemas": schemas, "issues": issues}

    for block in parser.blocks:
        try:
            data = json.loads(block)
            if isinstance(data, list):
                for item in data:
                    schema_type = item.get("@type", "Unknown") if isinstance(item, dict) else "Unknown"
                    schemas.append(schema_type)
            elif isinstance(data, dict):
                schema_type = data.get("@type", "Unknown")
                if isinstance(schema_type, list):
                    schemas.extend(schema_type)
                else:
                    schemas.append(schema_type)
        except json.JSONDecodeError:
            issues.append("INVALID JSON")

    return {"url": url, "schemas": schemas, "issues": issues}


# ---------------------------------------------------------------------------
# Command entry point
# ---------------------------------------------------------------------------

def _short_url(url: str, domain: str) -> str:
    for prefix in (f"https://{domain}", f"http://{domain}"):
        if url.startswith(prefix):
            path = url[len(prefix):]
            return path if path else "/"
    return url


def run(config: Config, *args: str) -> dict[str, Any] | None:
    """Validate JSON-LD structured data across all sitemap URLs.

    Returns results dict (also used by report module).
    """
    if not config.sitemap:
        print("  No sitemap configured. Set sitemap = \"...\" in .searchstack.toml")
        return None

    print(f"\n  JSON-LD Schema Validation")
    print(f"  Sitemap: {config.sitemap}\n")

    all_urls = _fetch_sitemap_urls(config.sitemap)
    html_urls = _filter_html_urls(all_urls)

    if not html_urls:
        print("  No HTML pages found in sitemap.")
        return None

    print(f"  Checking {len(html_urls)} pages...\n")

    results: list[dict[str, Any]] = []
    total_issues = 0

    for url in html_urls:
        result = _extract_schemas(url)
        total_issues += len(result["issues"])
        results.append(result)

    # Print table
    page_w = max(len(_short_url(r["url"], config.domain)) for r in results)
    page_w = max(page_w, 4)
    page_w = min(page_w, 50)

    print(f"  {'Page':<{page_w}}  Schemas")
    print(f"  {'─' * page_w}  {'─' * 40}")

    for r in results:
        path = _short_url(r["url"], config.domain)
        if len(path) > page_w:
            path = path[:page_w - 2] + ".."

        if r["issues"]:
            schema_str = ", ".join(r["issues"])
        elif r["schemas"]:
            schema_str = ", ".join(r["schemas"])
        else:
            schema_str = "NO JSON-LD"

        print(f"  {path:<{page_w}}  {schema_str}")

    pages_ok = sum(1 for r in results if r["schemas"] and not r["issues"])
    print(f"\n  Total: {len(results)} pages | {pages_ok} with valid schema | {total_issues} issues\n")

    return {"pages": results, "total_issues": total_issues, "pages_with_schema": pages_ok}
