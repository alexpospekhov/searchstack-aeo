"""On-page SEO scoring for a single URL."""

from __future__ import annotations

import json
import re
import urllib.request
from html.parser import HTMLParser
from typing import Any

from searchstack.config import Config


_UA = "Mozilla/5.0 SearchStack/1.0"


# ---------------------------------------------------------------------------
# HTML parsing
# ---------------------------------------------------------------------------

class _PageParser(HTMLParser):
    """Extract SEO-relevant elements from HTML."""

    def __init__(self) -> None:
        super().__init__()
        self.title = ""
        self.description = ""
        self.canonical = ""
        self.h1s: list[str] = []
        self.h2s: list[str] = []
        self.images: list[dict[str, str]] = []
        self.jsonld_blocks: list[str] = []
        self.internal_links: list[str] = []
        self.word_count = 0

        self._in_title = False
        self._in_h1 = False
        self._in_h2 = False
        self._in_jsonld = False
        self._in_body = False
        self._buf = ""
        self._body_text = ""

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attr_dict = {k.lower(): v for k, v in attrs}

        if tag == "title":
            self._in_title = True
            self._buf = ""
        elif tag == "h1":
            self._in_h1 = True
            self._buf = ""
        elif tag == "h2":
            self._in_h2 = True
            self._buf = ""
        elif tag == "body":
            self._in_body = True
        elif tag == "meta":
            name = (attr_dict.get("name") or "").lower()
            if name == "description":
                self.description = attr_dict.get("content", "") or ""
        elif tag == "link":
            rel = (attr_dict.get("rel") or "").lower()
            if rel == "canonical":
                self.canonical = attr_dict.get("href", "") or ""
        elif tag == "img":
            self.images.append({
                "src": attr_dict.get("src", "") or "",
                "alt": attr_dict.get("alt", "") or "",
            })
        elif tag == "a":
            href = attr_dict.get("href", "") or ""
            if href.startswith("/") and not href.startswith("//"):
                self.internal_links.append(href)
        elif tag == "script":
            stype = (attr_dict.get("type") or "").lower()
            if stype == "application/ld+json":
                self._in_jsonld = True
                self._buf = ""

    def handle_endtag(self, tag: str) -> None:
        if tag == "title" and self._in_title:
            self.title = self._buf.strip()
            self._in_title = False
        elif tag == "h1" and self._in_h1:
            self.h1s.append(self._buf.strip())
            self._in_h1 = False
        elif tag == "h2" and self._in_h2:
            self.h2s.append(self._buf.strip())
            self._in_h2 = False
        elif tag == "script" and self._in_jsonld:
            self.jsonld_blocks.append(self._buf)
            self._in_jsonld = False
        elif tag == "body":
            self._in_body = False
            self.word_count = len(self._body_text.split())

    def handle_data(self, data: str) -> None:
        if self._in_title or self._in_h1 or self._in_h2 or self._in_jsonld:
            self._buf += data
        if self._in_body:
            self._body_text += data + " "


# ---------------------------------------------------------------------------
# Scoring
# ---------------------------------------------------------------------------

def _score_page(parser: _PageParser) -> list[dict[str, Any]]:
    """Score the page and return a list of check results."""
    checks: list[dict[str, Any]] = []

    # Title (10 pts)
    tlen = len(parser.title)
    if tlen == 0:
        checks.append({"name": "Title tag", "max": 10, "score": 0, "detail": "Missing", "icon": "\u274c"})
    elif 30 <= tlen <= 65:
        checks.append({"name": "Title tag", "max": 10, "score": 10, "detail": f"{tlen} chars (optimal)", "icon": "\u2705"})
    else:
        label = "too short" if tlen < 30 else "too long"
        checks.append({"name": "Title tag", "max": 10, "score": 5, "detail": f"{tlen} chars ({label})", "icon": "\u26a0\ufe0f"})

    # Description (10 pts)
    dlen = len(parser.description)
    if dlen == 0:
        checks.append({"name": "Meta description", "max": 10, "score": 0, "detail": "Missing", "icon": "\u274c"})
    elif 120 <= dlen <= 160:
        checks.append({"name": "Meta description", "max": 10, "score": 10, "detail": f"{dlen} chars (optimal)", "icon": "\u2705"})
    else:
        label = "too short" if dlen < 120 else "too long"
        checks.append({"name": "Meta description", "max": 10, "score": 5, "detail": f"{dlen} chars ({label})", "icon": "\u26a0\ufe0f"})

    # H1 (10 pts)
    h1_count = len(parser.h1s)
    if h1_count == 0:
        checks.append({"name": "H1 heading", "max": 10, "score": 0, "detail": "Missing", "icon": "\u274c"})
    elif h1_count == 1:
        checks.append({"name": "H1 heading", "max": 10, "score": 10, "detail": f"1 H1 found", "icon": "\u2705"})
    else:
        checks.append({"name": "H1 heading", "max": 10, "score": 5, "detail": f"{h1_count} H1s (should be 1)", "icon": "\u26a0\ufe0f"})

    # H2s (5 pts)
    if parser.h2s:
        checks.append({"name": "H2 subheadings", "max": 5, "score": 5, "detail": f"{len(parser.h2s)} found", "icon": "\u2705"})
    else:
        checks.append({"name": "H2 subheadings", "max": 5, "score": 0, "detail": "None found", "icon": "\u274c"})

    # Images with alt (10 pts)
    total_imgs = len(parser.images)
    if total_imgs == 0:
        checks.append({"name": "Image alt text", "max": 10, "score": 5, "detail": "No images", "icon": "\u26a0\ufe0f"})
    else:
        with_alt = sum(1 for img in parser.images if img["alt"].strip())
        pct = (with_alt / total_imgs) * 100
        if pct >= 80:
            checks.append({"name": "Image alt text", "max": 10, "score": 10, "detail": f"{with_alt}/{total_imgs} ({pct:.0f}%)", "icon": "\u2705"})
        else:
            checks.append({"name": "Image alt text", "max": 10, "score": 5, "detail": f"{with_alt}/{total_imgs} ({pct:.0f}%)", "icon": "\u26a0\ufe0f"})

    # Word count (5 pts)
    wc = parser.word_count
    if wc > 300:
        checks.append({"name": "Word count", "max": 5, "score": 5, "detail": f"{wc} words", "icon": "\u2705"})
    else:
        checks.append({"name": "Word count", "max": 5, "score": 0, "detail": f"{wc} words (< 300)", "icon": "\u274c"})

    # JSON-LD (10 pts)
    valid_jsonld = 0
    for block in parser.jsonld_blocks:
        try:
            json.loads(block)
            valid_jsonld += 1
        except json.JSONDecodeError:
            pass

    if valid_jsonld > 0:
        checks.append({"name": "JSON-LD schema", "max": 10, "score": 10, "detail": f"{valid_jsonld} block(s)", "icon": "\u2705"})
    else:
        checks.append({"name": "JSON-LD schema", "max": 10, "score": 0, "detail": "None found", "icon": "\u274c"})

    # Canonical (5 pts)
    if parser.canonical:
        checks.append({"name": "Canonical URL", "max": 5, "score": 5, "detail": "Present", "icon": "\u2705"})
    else:
        checks.append({"name": "Canonical URL", "max": 5, "score": 0, "detail": "Missing", "icon": "\u274c"})

    # Internal links (5 pts)
    link_count = len(parser.internal_links)
    if link_count >= 3:
        checks.append({"name": "Internal links", "max": 5, "score": 5, "detail": f"{link_count} links", "icon": "\u2705"})
    else:
        checks.append({"name": "Internal links", "max": 5, "score": 0, "detail": f"{link_count} links (< 3)", "icon": "\u274c"})

    return checks


# ---------------------------------------------------------------------------
# Command entry point
# ---------------------------------------------------------------------------

def run(config: Config, *args: str) -> dict[str, Any] | None:
    """Run on-page SEO score for a single URL.

    Usage:
        searchstack onpage                    # scores https://{domain}/
        searchstack onpage https://example.com/page
    """
    if args:
        url = args[0]
    elif config.domain:
        url = f"https://{config.domain}/"
    else:
        print("  Usage: searchstack onpage <url>")
        return None

    print(f"\n  On-Page SEO Score")
    print(f"  URL: {url}\n")

    req = urllib.request.Request(url, headers={"User-Agent": _UA})
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            html = resp.read().decode("utf-8", errors="replace")
    except Exception as exc:
        print(f"  Failed to fetch page: {exc}")
        return None

    parser = _PageParser()
    try:
        parser.feed(html)
    except Exception:
        pass

    checks = _score_page(parser)

    # Print results
    name_w = max(len(c["name"]) for c in checks)

    for c in checks:
        print(f"  {c['icon']}  {c['name']:<{name_w}}  {c['score']:>2}/{c['max']:<2}  {c['detail']}")

    total_score = sum(c["score"] for c in checks)
    max_score = sum(c["max"] for c in checks)
    pct = (total_score / max_score * 100) if max_score else 0

    print(f"\n  SCORE: {total_score}/{max_score} ({pct:.0f}%)\n")

    return {
        "url": url,
        "checks": checks,
        "score": total_score,
        "max_score": max_score,
        "percentage": round(pct, 1),
    }
