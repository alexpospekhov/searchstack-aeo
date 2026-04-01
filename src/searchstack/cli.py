"""searchstack CLI -- SEO/AEO/GEO tech stack."""

from __future__ import annotations

import importlib
import sys

from searchstack import __version__
from searchstack.config import load_config


COMMANDS: dict[str, str] = {
    "ai": "searchstack.commands.ai",
    "geo": "searchstack.commands.geo",
    "gsc": "searchstack.commands.gsc_cmd",
    "traffic": "searchstack.commands.traffic",
    "keywords": "searchstack.commands.keywords",
    "competitors": "searchstack.commands.competitors",
    "gaps": "searchstack.commands.gaps",
    "serp": "searchstack.commands.serp",
    "track": "searchstack.commands.track",
    "bulk": "searchstack.commands.bulk",
    "backlinks": "searchstack.commands.backlinks",
    "meta": "searchstack.commands.meta",
    "schema": "searchstack.commands.schema",
    "links": "searchstack.commands.links",
    "onpage": "searchstack.commands.onpage",
    "pages": "searchstack.commands.pages",
    "indexnow": "searchstack.commands.indexnow",
    "bing": "searchstack.commands.bing_cmd",
    "report": "searchstack.commands.report",
}


def print_help() -> None:
    """Print grouped command listing."""
    print(f"""searchstack {__version__} -- SEO/AEO/GEO tech stack

Usage: searchstack [command] [args...]
       searchstack                Run full report (all sections)

AEO / GEO:
  ai [provider]        AI citation check (chatgpt, perplexity, claude)
  geo [keyword]        Google AI Overview monitor

SEO:
  gsc [sub] [arg]      Google Search Console (pages-perf, trend, inspect, ...)
  keywords "phrase"    Keyword suggestions with volumes
  competitors          Ranked keywords + overlap
  gaps                 High-volume keywords where you rank poorly
  serp "query"         Live SERP top-10 for a query
  track                Position changes since last check
  bulk domain1 ...     Competitor traffic comparison
  backlinks [domain]   Backlink profile (yours or competitor's)

Technical:
  meta                 Title/description length audit
  schema               JSON-LD structured data validation
  links                Internal linking + orphan page detection
  onpage <url>         Full on-page SEO score
  pages                Indexing status of all sitemap URLs

Traffic & Submission:
  traffic              Plausible analytics + AI referral tracking
  indexnow             Submit URLs to Bing + Yandex via IndexNow
  bing [sub]           Bing Webmaster stats (submit, stats)

Reporting:
  report               Full 14-section Markdown report

Options:
  -h, --help           Show this help message
  --version            Show version

Config: .searchstack.toml (CWD) or ~/.config/searchstack/config.toml
Docs:   https://github.com/hyperfocus/searchstack""")


def main() -> None:
    """CLI entry point."""
    config = load_config()
    args = sys.argv[1:]

    if not args:
        from searchstack.commands.report import run
        run(config)
        return

    cmd = args[0]
    rest = args[1:]

    if cmd in ("-h", "--help", "help"):
        print_help()
        return

    if cmd == "--version":
        print(f"searchstack {__version__}")
        return

    if cmd in COMMANDS:
        mod = importlib.import_module(COMMANDS[cmd])
        mod.run(config, *rest)
    else:
        print(f"Unknown command: {cmd}")
        print()
        print_help()
        sys.exit(1)
