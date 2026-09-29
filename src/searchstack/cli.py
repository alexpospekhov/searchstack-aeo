"""searchstack CLI -- SEO/AEO/GEO tech stack."""

from __future__ import annotations

import importlib
import sys

from searchstack import __version__
from searchstack.config import load_config


COMMANDS: dict[str, str] = {
    "ai": "searchstack.commands.ai",
    "geo": "searchstack.commands.geo",
    "doctor": "searchstack.commands.doctor",
    "gsc": "searchstack.commands.gsc_cmd",
    "traffic": "searchstack.commands.traffic",
    "keywords": "searchstack.commands.keywords",
    "competitors": "searchstack.commands.competitors",
    "competitor": "searchstack.commands.competitor",
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
    "monitor": "searchstack.commands.monitor",
    "audit": "searchstack.commands.audit",
    "llms": "searchstack.commands.llms",
    "diff": "searchstack.commands.diff",
    "questions": "searchstack.commands.questions",
    "entity": "searchstack.commands.entity",
}


def print_help() -> None:
    """Print grouped command listing."""
    print(f"""searchstack {__version__} -- SEO/AEO/GEO tech stack

Usage: searchstack [options] [command] [args...]
       searchstack                Run full report (all sections)

AEO / GEO:
  ai [provider]        AI citation check (chatgpt, perplexity, claude, grok, gemini, ollama)
  geo [keyword]        Google AI Overview monitor
  entity "brand"       Google Knowledge Graph authority & entity check
  doctor               Live provider + entitlement health check

SEO:
  gsc [sub] [arg]      Google Search Console (pages-perf, trend, inspect, ...)
  keywords "phrase"    Keyword suggestions with volumes
  competitors          Ranked keywords + overlap
  competitor study <domain> [--cluster name]
                       Research competitor & propose monitoring candidates
  gaps                 High-volume keywords where you rank poorly
  serp "query"         Live SERP top-10 for a query (with PAA & UGC forums)
  questions "topic"    Extract People Also Ask questions for content ideation
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

Dashboards:
  monitor              Site health dashboard (traffic, rankings, indexing)
  audit                Full SEO audit with keyword volumes + opportunity scores

AEO Content:
  llms [sub]           llms.txt generator + validator (generate, validate, check)

Reporting:
  report               Full 14-section Markdown report
  diff [type]          Compare latest snapshots (ai, doctor, geo)

Options:
  -p, --preset <name>  Use a named preset from presets/ (e.g. saas-starter)
  -c, --config <file>  Use a specific TOML config file
  -h, --help           Show this help message
  --version            Show version

Config: SEARCHSTACK_CONFIG, SEARCHSTACK_PRESET, .searchstack.toml (CWD) or ~/.config/searchstack/config.toml
Docs:   https://github.com/alexpospekhov/searchstack-aeo""")


def main() -> None:
    """CLI entry point."""
    args = sys.argv[1:]
    config_override: str | None = None

    filtered_args: list[str] = []
    i = 0
    while i < len(args):
        arg = args[i]
        if arg in ("--config", "-c") and i + 1 < len(args):
            config_override = args[i + 1]
            i += 2
        elif arg.startswith("--config="):
            config_override = arg.split("=", 1)[1]
            i += 1
        elif arg in ("--preset", "-p") and i + 1 < len(args):
            config_override = args[i + 1]
            i += 2
        elif arg.startswith("--preset="):
            config_override = arg.split("=", 1)[1]
            i += 1
        else:
            filtered_args.append(arg)
            i += 1

    config = load_config(config_override)
    args = filtered_args

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
