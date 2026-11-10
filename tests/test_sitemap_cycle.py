"""Tests for sitemap index fetching (cycle safety, nesting)."""

import unittest
import urllib.request
from unittest.mock import patch

from searchstack.commands import bing_cmd, indexnow, meta

MODULES = {
    "meta": meta,
    "indexnow": indexnow,
    "bing_cmd": bing_cmd,
}

SELFREF_INDEX = (
    b'<?xml version="1.0"?>'
    b"<sitemapindex><sitemap>"
    b"<loc>https://example.com/sitemap.xml</loc>"
    b"</sitemap></sitemapindex>"
)

MUTUAL_A = (
    b'<?xml version="1.0"?>'
    b"<sitemapindex><sitemap>"
    b"<loc>https://example.com/b.xml</loc>"
    b"</sitemap></sitemapindex>"
)
MUTUAL_B = (
    b'<?xml version="1.0"?>'
    b"<sitemapindex><sitemap>"
    b"<loc>https://example.com/a.xml</loc>"
    b"</sitemap></sitemapindex>"
)

NESTED_INDEX = (
    b'<?xml version="1.0"?>'
    b"<sitemapindex><sitemap>"
    b"<loc>https://example.com/pages.xml</loc>"
    b"</sitemap><sitemap>"
    b"<loc>https://example.com/pages.xml</loc>"
    b"</sitemap></sitemapindex>"
)
PAGES = (
    b'<?xml version="1.0"?>'
    b"<urlset><url><loc>https://example.com/one</loc></url>"
    b"<url><loc>https://example.com/two</loc></url></urlset>"
)


class FakeResponse:
    def __init__(self, body: bytes):
        self._body = body

    def read(self) -> bytes:
        return self._body

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False


def make_urlopen(bodies: dict):
    def fake_urlopen(req, timeout=30):
        url = req.full_url if isinstance(req, urllib.request.Request) else req
        return FakeResponse(bodies[url])

    return fake_urlopen


class TestSitemapIndexCycle(unittest.TestCase):
    def test_self_referencing_index_terminates(self):
        # A sitemap index that lists itself must not recurse forever.
        bodies = {"https://example.com/sitemap.xml": SELFREF_INDEX}
        for name, mod in MODULES.items():
            with self.subTest(module=name):
                with patch.object(
                    mod.urllib.request, "urlopen", make_urlopen(bodies)
                ):
                    self.assertEqual(
                        mod._fetch_sitemap_urls("https://example.com/sitemap.xml"), []
                    )

    def test_mutual_cycle_terminates(self):
        # a.xml <-> b.xml must terminate too.
        bodies = {
            "https://example.com/a.xml": MUTUAL_A,
            "https://example.com/b.xml": MUTUAL_B,
        }
        for name, mod in MODULES.items():
            with self.subTest(module=name):
                with patch.object(
                    mod.urllib.request, "urlopen", make_urlopen(bodies)
                ):
                    self.assertEqual(
                        mod._fetch_sitemap_urls("https://example.com/a.xml"), []
                    )

    def test_nested_index_still_collected_once(self):
        # Distinct nested sitemaps are still followed; a sitemap listed
        # twice is fetched once (no duplicate URLs).
        bodies = {
            "https://example.com/sitemap.xml": NESTED_INDEX,
            "https://example.com/pages.xml": PAGES,
        }
        for name, mod in MODULES.items():
            with self.subTest(module=name):
                with patch.object(
                    mod.urllib.request, "urlopen", make_urlopen(bodies)
                ):
                    self.assertEqual(
                        mod._fetch_sitemap_urls("https://example.com/sitemap.xml"),
                        ["https://example.com/one", "https://example.com/two"],
                    )


if __name__ == "__main__":
    unittest.main()
