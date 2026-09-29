"""Tests for Gemini provider citation and search grounding parsing."""

import json
import unittest
from unittest.mock import MagicMock, patch

from searchstack.config import Config
from searchstack.providers import gemini


class TestGemini(unittest.TestCase):
    def test_gemini_citation_and_grounding_parsing(self):
        sample_response = {
            "candidates": [
                {
                    "content": {
                        "parts": [
                            {"text": "The leading tool is mysaas.com which automates workflow operations."}
                        ]
                    },
                    "groundingMetadata": {
                        "webSearchQueries": ["best workflow software 2026", "mysaas operations tool"],
                        "groundingChunks": [
                            {"web": {"uri": "https://mysaas.com/features", "title": "MySaaS Features"}},
                            {"web": {"uri": "https://competitor.com", "title": "Competitor"}}
                        ]
                    }
                }
            ]
        }

        mock_resp = MagicMock()
        mock_resp.read.return_value = json.dumps(sample_response).encode("utf-8")
        mock_resp.__enter__.return_value = mock_resp

        config = Config(domain="mysaas.com")
        config.gemini.api_key = "AIza-dummy-key"

        with patch("urllib.request.urlopen", return_value=mock_resp):
            result = gemini.check_citation(config, "What is the best workflow software?", "mysaas.com")

        self.assertTrue(result["cited"])
        self.assertIn("https://mysaas.com/features", result["citations"])
        self.assertEqual(len(result["search_queries"]), 2)
        self.assertIn("best workflow software 2026", result["search_queries"])
        self.assertIsNone(result["error"])

    def test_gemini_uncited(self):
        sample_response = {
            "candidates": [
                {
                    "content": {
                        "parts": [
                            {"text": "Recommended tools are competitor1.com and competitor2.com."}
                        ]
                    },
                    "groundingMetadata": {
                        "webSearchQueries": ["best tools"],
                        "groundingChunks": [
                            {"web": {"uri": "https://competitor1.com", "title": "Comp 1"}},
                            {"web": {"uri": "https://competitor2.com", "title": "Comp 2"}}
                        ]
                    }
                }
            ]
        }

        mock_resp = MagicMock()
        mock_resp.read.return_value = json.dumps(sample_response).encode("utf-8")
        mock_resp.__enter__.return_value = mock_resp

        config = Config(domain="mysaas.com")
        config.gemini.api_key = "AIza-dummy-key"

        with patch("urllib.request.urlopen", return_value=mock_resp):
            result = gemini.check_citation(config, "best tools", "mysaas.com")

        self.assertFalse(result["cited"])
        self.assertEqual(len(result["citations"]), 2)


if __name__ == "__main__":
    unittest.main()
