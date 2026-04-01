"""Meta tag audit -- title, description, and H1 checks for all sitemap URLs."""

from __future__ import annotations

import re
import urllib.request
import urllib.error
from html.parser import HTMLParser
from typing import Any

from searchstack.config import Config


_UA = "Mozilla/5.0 SearchStack/1.0"


# ---------------------------------------------------------------------------
# Sitemap fetching
# ---------------------------------------------------------------------------

def _fetch_sitemap_urls(sitemap_url: str) -> list[str]:
    """Fetch a sitemap XML and extract all <loc> URLs."""
    req = urllib.request.Request(sitemap_url, headers={"User-Agent": _UA})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            body = resp.read().decode("utf-8", errors="replace")
    except Exception as exc:
        print(f"  Failed to fetch sitemap: {exc}")
        return []

    # Handle sitemap index (nested sitemaps)
    if "<sitemapindex" in body:
        nested = re.findall(r"<loc>\s*(.*?)\s*</loc>", body)
        all_urls: list[str] = []
        for sub_url in nested:
            all_urls.extend(_fetch_sitemap_urls(sub_url))
        return all_urls

    return re.findall(r"<loc>\s*(.*?)\s*</loc>", body)


def _filter_html_urls(urls: list[str]) -> list[str]:
    """Keep only URLs that look like HTML pages (not .xml, .txt, .md, etc.)."""
    skip = (".xml", ".txt", ".md", ".json", ".pdf", ".jpg", ".png", ".svg", ".css", ".js")
    return [u for u in urls if not any(u.lower().endswith(ext) for ext in skip)]


# ---------------------------------------------------------------------------
# HTML meta extraction
# ---------------------------------------------------------------------------

class _MetaParser(HTMLParser):
    """Extract title, meta description, and H1 tags from HTML."""

    def __init__(self) -> None:
        super().__init__()
        self.title = ""
        self.description = ""
        self.h1s: list[str] = []
        self._in_title = False
        self._in_h1 = False
        self._buf = ""

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "title":
            self._in_title = True
            self._buf = ""
        elif tag == "h1":
            self._in_h1 = True
            self._buf = ""
        elif tag == "meta":
            attr_dict = {k.lower(): v for k, v in attrs if v is not None}
            if attr_dict.get("name", "").lower() == "description":
                self.description = attr_dict.get("content", "")

    def handle_endtag(self, tag: str) -> None:
        if tag == "title" and self._in_title:
            self.title = self._buf.strip()
            self._in_title = False
        elif tag == "h1" and self._in_h1:
            self.h1s.append(self._buf.strip())
            self._in_h1 = False

    def handle_data(self, data: str) -> None:
        if self._in_title or self._in_h1:
            self._buf += data


def _fetch_meta(url: str) -> dict[str, Any]:
    """Fetch a page and extract meta information."""
    req = urllib.request.Request(url, headers={"User-Agent": _UA})
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            html = resp.read().decode("utf-8", errors="replace")
    except Exception as exc:
        return {"url": url, "error": str(exc)}

    parser = _MetaParser()
    try:
        parser.feed(html)
    except Exception:
        pass

    return {
        "url": url,
        "title": parser.title,
        "title_len": len(parser.title),
        "description": parser.description,
        "desc_len": len(parser.description),
        "h1s": parser.h1s,
    }


# ---------------------------------------------------------------------------
# Issue detection
# ---------------------------------------------------------------------------

def _check_issues(meta: dict[str, Any]) -> list[str]:
    """Return a list of issue strings for a page's meta data."""
    issues: list[str] = []

    if "error" in meta:
        return [f"FETCH ERROR: {meta['error']}"]

    tlen = meta["title_len"]
    if tlen == 0:
        issues.append("NO TITLE")
    elif tlen < 30:
        issues.append(f"Title too short ({tlen})")
    elif tlen > 65:
        issues.append(f"Title too long ({tlen})")

    dlen = meta["desc_len"]
    if dlen == 0:
        issues.append("NO DESC")
    elif dlen < 100:
        issues.append(f"Desc too short ({dlen})")
    elif dlen > 165:
        issues.append(f"Desc too long ({dlen})")

    h1s = meta.get("h1s", [])
    if not h1s:
        issues.append("NO H1")
    elif len(h1s) > 1:
        issues.append(f"Multiple H1 ({len(h1s)})")

    if h1s and meta["title"] and h1s[0].lower().strip() == meta["title"].lower().strip():
        issues.append("H1 == Title")

    return issues


# ---------------------------------------------------------------------------
# Command entry point
# ---------------------------------------------------------------------------

def _short_url(url: str, domain: str) -> str:
    """Shorten URL for display: strip scheme and domain."""
    for prefix in (f"https://{domain}", f"http://{domain}"):
        if url.startswith(prefix):
            path = url[len(prefix):]
            return path if path else "/"
    return url


def run(config: Config, *args: str) -> dict[str, Any] | None:
    """Audit meta tags (title, description, H1) across all sitemap URLs.

    Returns results dict (also used by report module).
    """
    if not config.sitemap:
        print("  No sitemap configured. Set sitemap = \"...\" in .searchstack.toml")
        return None

    print(f"\n  Meta Tag Audit")
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
        meta = _fetch_meta(url)
        issues = _check_issues(meta)
        total_issues += len(issues)
        meta["issues"] = issues
        results.append(meta)

    # Print table
    page_w = max(len(_short_url(r["url"], config.domain)) for r in results)
    page_w = max(page_w, 4)
    page_w = min(page_w, 50)

    print(f"  {'Page':<{page_w}}  {'Title':>5}  {'Desc':>5}  Issues")
    print(f"  {'─' * page_w}  {'─' * 5}  {'─' * 5}  {'─' * 30}")

    for r in results:
        path = _short_url(r["url"], config.domain)
        if len(path) > page_w:
            path = path[:page_w - 2] + ".."
        tlen = r.get("title_len", "?")
        dlen = r.get("desc_len", "?")
        issues = r.get("issues", [])
        issue_str = ", ".join(issues) if issues else "OK"
        print(f"  {path:<{page_w}}  {tlen:>5}  {dlen:>5}  {issue_str}")

    print(f"\n  Total: {len(results)} pages, {total_issues} issues\n")
    return {"pages": results, "total_issues": total_issues}
