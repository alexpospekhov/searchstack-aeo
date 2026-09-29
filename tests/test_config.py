"""Tests for searchstack configuration loading and presets."""

import os
import unittest
from pathlib import Path

from searchstack.config import Config, load_config, _build_config, _apply_defaults


class TestConfig(unittest.TestCase):
    def test_default_config(self):
        cfg = Config()
        self.assertEqual(cfg.domain, "")
        self.assertEqual(cfg.gsc.credentials_file, "credentials.json")
        self.assertEqual(cfg.dataforseo.location_code, 2840)
        self.assertEqual(cfg.dataforseo.language_code, "en")
        self.assertEqual(cfg.openrouter.chatgpt_model, "openai/gpt-4o-mini")

    def test_apply_defaults_with_domain(self):
        cfg = Config(domain="testdomain.com")
        _apply_defaults(cfg)
        self.assertEqual(cfg.sitemap, "https://testdomain.com/sitemap.xml")
        self.assertEqual(cfg.gsc.site_url, "sc-domain:testdomain.com")
        self.assertEqual(cfg.plausible.site_id, "testdomain.com")

    def test_preset_loading(self):
        repo_root = Path(__file__).resolve().parents[1]
        preset_path = repo_root / "presets" / "saas-starter.toml"
        self.assertTrue(preset_path.is_file(), f"Preset not found: {preset_path}")

        cfg = load_config(preset_path)
        self.assertEqual(cfg.domain, "mysaas.com")
        self.assertEqual(cfg.sitemap, "https://mysaas.com/sitemap.xml")
        self.assertIn("zapier.com", cfg.competitors)
        self.assertTrue(len(cfg.ai_queries) > 0)
        self.assertIn("product", cfg.geo_keywords)

    def test_env_overlay(self):
        os.environ["OPENAI_API_KEY"] = "sk-test-key-12345"
        os.environ["GEMINI_API_KEY"] = "AIza-test-gemini-key"
        try:
            cfg = load_config()
            self.assertEqual(cfg.openai.api_key, "sk-test-key-12345")
            self.assertEqual(cfg.gemini.api_key, "AIza-test-gemini-key")
        finally:
            os.environ.pop("OPENAI_API_KEY", None)
            os.environ.pop("GEMINI_API_KEY", None)


if __name__ == "__main__":
    unittest.main()
