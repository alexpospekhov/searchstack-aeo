"""Tests for the cloro provider. HTTP is stubbed; the payloads follow the
shape of live cloro responses."""

import io
import unittest
from unittest.mock import MagicMock, patch

from searchstack.commands import ai, geo
from searchstack.config import Config
from searchstack.providers import cloro

GOOGLE_RESULT = {
    "success": True,
    "result": {
        "organicResults": [
            {"position": 1, "title": "Best rank trackers", "link": "https://competitor.com/blog/rank-trackers/"},
            {"position": 2, "title": "Redirect only", "link": "https://www.google.com/goto?url=CAESZw"},
            {"position": 3, "title": "Empty link", "link": ""},
            {"position": 4, "title": "MySaaS rank tracker", "link": "https://www.mysaas.com/rank-tracker"},
        ],
        "peopleAlsoAsk": [{"question": "What is the best rank tracker?", "type": "AIOVERVIEW"}],
        "relatedSearches": [],
        "aioverview": {
            "text": "The best rank tracker tools cater to different needs.",
            "sources": [
                {"position": 1, "label": "Best rank trackers", "url": "https://competitor.com/blog/rank-trackers/"},
                {"position": 2, "label": "MySaaS", "url": "https://mysaas.com/features"},
            ],
            "citationPills": [],
        },
    },
}

GOOGLE_NO_AIO = {
    "success": True,
    "result": {
        "organicResults": [
            {"position": 1, "title": "Best rank trackers", "link": "https://competitor.com/blog/rank-trackers/"},
        ],
        "peopleAlsoAsk": [],
        "relatedSearches": [],
    },
}

CHATGPT_RESULT = {
    "success": True,
    "result": {
        "model": None,
        "text": "If you're looking for the best rank tracking tools in 2026, there are several options.",
        "sources": [
            {"position": 1, "label": "Website and pricing", "url": "https://competitor.com/pricing/", "footnote": True},
            {"position": 2, "label": "MySaaS", "url": "https://mysaas.com/pricing", "footnote": False},
        ],
        "citationPills": [],
    },
}

AIMODE_RESULT = {
    "success": True,
    "result": {
        "text": "Evaluating rank tracking tools depends on your needs.",
        "sources": [
            {
                "position": 1,
                "label": "15 Best Rank Tracking Software",
                "url": "https://competitor.com/top-tools/",
                "description": "Each of these tools covers different roles.",
            },
        ],
        "citationPills": [],
    },
}

BING_AIMODE_RESULT = {
    "success": True,
    "result": {
        "text": "The ASICS Gel Pulse 15, Brooks Glycerin 21, and Saucony Guide 19 are good picks.",
        "sources": [
            {
                "position": 1,
                "label": "Best Running Shoes Under $150 in 2026: 8 Picks Worth the Money",
                "url": "https://runninggearlab.com/best-running-shoes-under-150/",
                "description": "The best running shoes under $150 in 2026.",
            },
        ],
        "citationPills": [
            {
                "position": 1,
                "label": "Best Running Shoes Under $150 in 2026: 8 Picks Worth the Money",
                "url": "https://runninggearlab.com/best-running-shoes-under-150/",
                "domain": "runninggearlab.com",
                "citationPillId": 1,
            },
        ],
    },
}

BAD_KEY = {
    "success": False,
    "error": {"code": "INVALID_API_KEY_FORMAT", "message": "Invalid API key format"},
}


def _resp(payload, status=200):
    resp = MagicMock()
    resp.status_code = status
    resp.json.return_value = payload
    return resp


def _config():
    config = Config(domain="mysaas.com")
    config.cloro.api_key = "test-key"
    return config


class TestCloroProvider(unittest.TestCase):
    def test_check_citation_chatgpt(self):
        with patch("requests.post", return_value=_resp(CHATGPT_RESULT)) as post:
            result = cloro.check_citation(_config(), "best rank tracker", "mysaas.com", engine="chatgpt")

        url = post.call_args.args[0]
        kwargs = post.call_args.kwargs
        self.assertEqual(url, "https://api.cloro.dev/v1/monitor/chatgpt")
        self.assertEqual(kwargs["json"], {"prompt": "best rank tracker", "country": "US"})
        self.assertEqual(kwargs["headers"]["Authorization"], "Bearer test-key")
        self.assertTrue(result["cited"])
        self.assertEqual(result["citations"], ["https://competitor.com/pricing/", "https://mysaas.com/pricing"])
        self.assertEqual(result["model"], "cloro/chatgpt")
        self.assertIsNone(result["error"])

    def test_check_citation_not_cited(self):
        with patch("requests.post", return_value=_resp(AIMODE_RESULT)):
            result = cloro.check_citation(_config(), "best rank tracker", "mysaas.com", engine="aimode")
        self.assertFalse(result["cited"])
        self.assertEqual(result["citations"], ["https://competitor.com/top-tools/"])

    def test_check_citation_bing_aimode(self):
        with patch("requests.post", return_value=_resp(BING_AIMODE_RESULT)) as post:
            result = cloro.check_citation(
                _config(), "best running shoes", "runninggearlab.com", engine="bing/aimode"
            )
        self.assertEqual(post.call_args.args[0], "https://api.cloro.dev/v1/monitor/bing/aimode")
        self.assertEqual(post.call_args.kwargs["json"], {"prompt": "best running shoes", "country": "US"})
        self.assertTrue(result["cited"])
        self.assertEqual(result["citations"], ["https://runninggearlab.com/best-running-shoes-under-150/"])
        self.assertEqual(result["model"], "cloro/bing/aimode")

    def test_error_body_is_reported(self):
        with patch("requests.post", return_value=_resp(BAD_KEY, status=401)):
            result = cloro.check_citation(_config(), "q", "mysaas.com", engine="gemini")
        self.assertFalse(result["cited"])
        self.assertIn("INVALID_API_KEY_FORMAT", result["error"])

    def test_google_search_body(self):
        config = _config()
        config.cloro.country = "DE"
        with patch("requests.post", return_value=_resp(GOOGLE_RESULT)) as post:
            cloro.google_search(keyword="rank tracker", config=config)
        self.assertEqual(post.call_args.args[0], "https://api.cloro.dev/v1/monitor/google")
        self.assertEqual(
            post.call_args.kwargs["json"],
            {"query": "rank tracker", "country": "DE", "include": {"aioverview": True}},
        )

    def test_parse_ai_overview(self):
        info = cloro.parse_ai_overview(GOOGLE_RESULT["result"], "mysaas.com")
        self.assertTrue(info["ai_present"])
        self.assertTrue(info["cites_us"])
        self.assertEqual(info["cited_domains"], ["competitor.com", "mysaas.com"])

    def test_parse_ai_overview_absent(self):
        info = cloro.parse_ai_overview(GOOGLE_NO_AIO["result"], "mysaas.com")
        self.assertFalse(info["ai_present"])
        self.assertFalse(info["cites_us"])

    def test_parse_organic_skips_empty_and_redirect_links(self):
        organic = cloro.parse_organic(GOOGLE_RESULT["result"], "mysaas.com")
        self.assertEqual(organic["position"], 4)
        self.assertEqual([r["rank"] for r in organic["top_10"]], [1, 4])
        self.assertEqual(organic["top_10"][1]["domain"], "mysaas.com")


class TestCloroCommands(unittest.TestCase):
    def test_geo_uses_cloro_without_dataforseo(self):
        config = _config()
        with patch("requests.post", return_value=_resp(GOOGLE_RESULT)), \
                patch("searchstack.snapshots.save_snapshot", return_value="snap.json") as save, \
                patch("sys.stdout", io.StringIO()):
            geo.run(config, "rank", "tracker")
        data = save.call_args.args[1]
        self.assertEqual(data["ai_overview_present"], 1)
        self.assertEqual(data["cites_us"], 1)
        self.assertEqual(data["results"][0]["organic_position"], 4)

    def test_ai_cloro_provider_skips_without_key(self):
        with patch("sys.stdout", io.StringIO()):
            result = ai._check_provider("cloro-chatgpt", ["q"], Config(domain="mysaas.com"))
        self.assertEqual(result["total"], 0)

    def test_ai_cloro_provider(self):
        with patch("requests.post", return_value=_resp(CHATGPT_RESULT)) as post, \
                patch("sys.stdout", io.StringIO()):
            result = ai._check_provider("cloro-gemini", ["best rank tracker"], _config())
        self.assertEqual(post.call_args.args[0], "https://api.cloro.dev/v1/monitor/gemini")
        self.assertEqual(result["cited"], 1)
        self.assertEqual(result["total"], 1)

    def test_ai_cloro_bing_aimode_provider(self):
        with patch("requests.post", return_value=_resp(BING_AIMODE_RESULT)) as post, \
                patch("sys.stdout", io.StringIO()):
            result = ai._check_provider("cloro-bing-aimode", ["best running shoes"], _config())
        self.assertEqual(post.call_args.args[0], "https://api.cloro.dev/v1/monitor/bing/aimode")
        self.assertEqual(result["cited"], 0)
        self.assertEqual(result["total"], 1)


if __name__ == "__main__":
    unittest.main()
