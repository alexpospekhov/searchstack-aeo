"""Tests for CLI routing, command registry, and help text."""

import io
import sys
import unittest
from unittest.mock import patch

from searchstack import __version__
from searchstack.cli import COMMANDS, print_help, main


class TestCLI(unittest.TestCase):
    def test_version_string(self):
        self.assertEqual(__version__, "1.0.0")

    def test_commands_registered(self):
        expected_commands = {
            "ai", "geo", "doctor", "gsc", "traffic", "keywords",
            "competitors", "competitor", "gaps", "serp", "track",
            "bulk", "backlinks", "meta", "schema", "links", "onpage",
            "pages", "indexnow", "bing", "report", "monitor", "audit",
            "llms", "diff", "questions", "entity"
        }
        for cmd in expected_commands:
            self.assertIn(cmd, COMMANDS, f"Command '{cmd}' is missing from COMMANDS map")

    def test_help_output(self):
        buf = io.StringIO()
        with patch("sys.stdout", buf):
            print_help()
        out = buf.getvalue()
        self.assertIn("searchstack 1.0.0", out)
        self.assertIn("doctor", out)
        self.assertIn("competitor study", out)
        self.assertIn("questions", out)
        self.assertIn("entity", out)
        self.assertIn("diff", out)

    def test_version_cli_flag(self):
        buf = io.StringIO()
        with patch("sys.stdout", buf), patch("sys.argv", ["searchstack", "--version"]):
            main()
        out = buf.getvalue()
        self.assertIn("searchstack 1.0.0", out)


if __name__ == "__main__":
    unittest.main()
