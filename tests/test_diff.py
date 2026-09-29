"""Tests for snapshot diffing logic."""

import io
from pathlib import Path
import unittest
from unittest.mock import patch

from searchstack.commands import diff


class TestDiff(unittest.TestCase):
    def test_diff_ai_citations(self):
        prev_snapshot = {
            "results": [
                {
                    "provider": "chatgpt",
                    "results": [
                        {"query": "best saas tool", "cited": False},
                        {"query": "workflow automation", "cited": True},
                    ]
                }
            ]
        }
        curr_snapshot = {
            "results": [
                {
                    "provider": "chatgpt",
                    "results": [
                        {"query": "best saas tool", "cited": True},  # GAINED!
                        {"query": "workflow automation", "cited": False},  # LOST!
                    ]
                }
            ]
        }

        buf = io.StringIO()
        with patch("sys.stdout", buf):
            diff._diff_ai(prev_snapshot, curr_snapshot, Path("prev.json"), Path("curr.json"))
        out = buf.getvalue()

        self.assertIn("GAINED AI CITATIONS", out)
        self.assertIn("best saas tool", out)
        self.assertIn("LOST AI CITATIONS", out)
        self.assertIn("workflow automation", out)
        self.assertIn("+1 gained", out)
        self.assertIn("-1 lost", out)


if __name__ == "__main__":
    unittest.main()
