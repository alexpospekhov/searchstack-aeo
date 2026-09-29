"""Tests for SERP item parsing (organic, PAA, discussions/forums)."""

import unittest

from searchstack.config import Config


class TestSerp(unittest.TestCase):
    def test_paa_and_discussion_extraction(self):
        sample_items = [
            {
                "type": "organic",
                "domain": "mysaas.com",
                "title": "MySaaS - Automation Platform",
                "url": "https://mysaas.com",
            },
            {
                "type": "people_also_ask",
                "items": [
                    {"title": "How does workflow automation work?", "description": "It connects APIs."},
                    {"title": "Is workflow software expensive?", "description": "Plans start free."}
                ]
            },
            {
                "type": "discussions_and_forums",
                "items": [
                    {"domain": "reddit.com", "title": "Best automation tools for 2026 : r/SaaS", "url": "https://reddit.com/r/SaaS/123"}
                ]
            }
        ]

        organic = [i for i in sample_items if i.get("type") == "organic"]
        paa = [i for i in sample_items if i.get("type") == "people_also_ask"]
        forums = [i for i in sample_items if i.get("type") == "discussions_and_forums"]

        self.assertEqual(len(organic), 1)
        self.assertEqual(organic[0]["domain"], "mysaas.com")

        self.assertEqual(len(paa), 1)
        questions = paa[0].get("items", [])
        self.assertEqual(len(questions), 2)
        self.assertEqual(questions[0]["title"], "How does workflow automation work?")

        self.assertEqual(len(forums), 1)
        discussions = forums[0].get("items", [])
        self.assertEqual(len(discussions), 1)
        self.assertEqual(discussions[0]["domain"], "reddit.com")


if __name__ == "__main__":
    unittest.main()
