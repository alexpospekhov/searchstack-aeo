"""Internal linking audit and orphan page detection."""

from __future__ import annotations

import re
import urllib.request
from html.parser import HTMLParser
from typing import Any
from urllib.parse import urljoin, urlparse

from searchstack.config import Config


_UA = "Mozilla/5.0 SearchStack/1.0"


# ---------------------------------------------------------------------------
# Sitemap
# ---------------------------------------------------------------------------

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


def _filter_html_urls(urls: list[str]) -> list[str]:
    skip = (".xml", ".txt", ".md", ".json", ".pdf", ".jpg", ".png", ".svg", ".css", ".js")
    return [u for u in urls if not any(u.lower().endswith(ext) for ext in skip)]


# ---------------------------------------------------------------------------
# Link extraction
# ---------------------------------------------------------------------------

class _LinkParser(HTMLParser):
    """Extract all href values from <a> tags."""

    def __init__(self) -> None:
        super().__init__()
        self.links: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "a":
            for name, value in attrs:
                if name == "href" and value:
                    self.links.append(value)


def _normalize_url(url: str) -> str:
    """Strip trailing slash and fragment for comparison."""
    parsed = urlparse(url)
    path = parsed.path.rstrip("/") or "/"
    return f"{parsed.scheme}://{parsed.netloc}{path}"


def _fetch_internal_links(url: str, domain: str) -> set[str]:
    """Fetch a page and return all internal links (same domain)."""
    req = urllib.request.Request(url, headers={"User-Agent": _UA})
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            html = resp.read().decode("utf-8", errors="replace")
    except Exception:
        return set()

    parser = _LinkParser()
    try:
        parser.feed(html)
    except Exception:
        pass

    internal: set[str] = set()
    for href in parser.links:
        # Skip anchors, mailto, tel, javascript
        if href.startswith(("#", "mailto:", "tel:", "javascript:")):
            continue

        # Resolve relative URLs
        full_url = urljoin(url, href)
        parsed = urlparse(full_url)

        # Only keep same-domain links
        if parsed.netloc and domain in parsed.netloc:
            internal.add(_normalize_url(full_url))

    return internal


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
    """Analyze internal linking structure and find orphan pages.

    Returns results dict (also used by report module).
    """
    if not config.sitemap:
        print("  No sitemap configured. Set sitemap = \"...\" in .searchstack.toml")
        return None

    print(f"\n  Internal Link Analysis")
    print(f"  Sitemap: {config.sitemap}\n")

    all_urls = _fetch_sitemap_urls(config.sitemap)
    html_urls = _filter_html_urls(all_urls)

    if not html_urls:
        print("  No HTML pages found in sitemap.")
        return None

    print(f"  Crawling {len(html_urls)} pages...\n")

    # Normalize sitemap URLs for comparison
    sitemap_normalized = {_normalize_url(u) for u in html_urls}

    # Build link graph
    page_links: dict[str, set[str]] = {}
    linked_to: dict[str, int] = {u: 0 for u in sitemap_normalized}

    for url in html_urls:
        norm_url = _normalize_url(url)
        internal = _fetch_internal_links(url, config.domain)
        page_links[norm_url] = internal

        for link in internal:
            if link in linked_to:
                linked_to[link] += 1

    # Find orphans (in sitemap but no inbound links)
    orphans = [u for u, count in linked_to.items() if count == 0]

    # Print table
    page_w = max(len(_short_url(u, config.domain)) for u in sitemap_normalized)
    page_w = max(page_w, 4)
    page_w = min(page_w, 50)

    print(f"  {'Page':<{page_w}}  {'Out':>4}  {'In':>4}  Notes")
    print(f"  {'─' * page_w}  {'─' * 4}  {'─' * 4}  {'─' * 15}")

    for url in sorted(sitemap_normalized):
        path = _short_url(url, config.domain)
        if len(path) > page_w:
            path = path[:page_w - 2] + ".."

        links_out = len(page_links.get(url, set()))
        links_in = linked_to.get(url, 0)
        note = "\u2190 ORPHAN" if links_in == 0 else ""

        print(f"  {path:<{page_w}}  {links_out:>4}  {links_in:>4}  {note}")

    # Print orphan summary
    print(f"\n  Total: {len(sitemap_normalized)} pages | {len(orphans)} orphans")

    if orphans:
        print(f"\n  Orphan pages (no inbound internal links):")
        for u in sorted(orphans):
            print(f"    - {_short_url(u, config.domain)}")

    print()

    return {
        "pages": [
            {
                "url": u,
                "links_out": len(page_links.get(u, set())),
                "links_in": linked_to.get(u, 0),
                "is_orphan": linked_to.get(u, 0) == 0,
            }
            for u in sorted(sitemap_normalized)
        ],
        "orphans": [_short_url(u, config.domain) for u in sorted(orphans)],
        "total_pages": len(sitemap_normalized),
        "total_orphans": len(orphans),
    }
