# Searchstack — AEO/GEO/SEO for AI-native founders

> Open-source AEO / GEO / SEO tech stack for AI-native founders.

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

Monitor your visibility across Google, AI Overviews, ChatGPT, Perplexity & Claude — from one CLI.

### What's inside

- **AEO Monitor** — check if ChatGPT, Perplexity, and Claude cite your site when users ask about your niche
- **GEO Monitor** — track Google AI Overview: who gets cited for your target keywords (and whether it's you)
- **Google Search Console** — rankings, clicks, impressions, CTR, indexing status, sitemap health
- **Keyword Research** — suggestions, volumes, competitor overlap, keyword gaps (DataForSEO)
- **Position Tracking** — compare rankings over time, detect improvements and drops
- **Backlink Analysis** — your profile + competitor backlinks, referring domains, domain rank
- **Technical Audit** — meta tags, JSON-LD validation, internal linking, orphan pages, on-page scoring
- **Traffic Analytics** — Plausible integration with AI referral breakdown (chatgpt.com, perplexity.ai, claude.ai)
- **Search Submission** — IndexNow (instant Bing/Yandex), Bing Webmaster, GSC sitemap resubmit
- **Markdown Reports** — `searchstack report` generates a full 14-section .md file with executive summary and auto-recommendations. Run it monthly, diff the results, track progress over time.
- **Cron-ready** — pure CLI, no GUI, no browser. Deploy on any server, schedule via cron (`0 8 * * 1 searchstack report`), pipe output to Slack/email. Built for automation.

**19 commands. 8 API integrations. One config file. Runs anywhere Python runs.**

```
$ searchstack ai

  Checking AI citations for example.com...

  ChatGPT (gpt-4o-mini):
    "What is the best tool for X?"      ✅ CITED
    "How to solve Y?"                    ❌ not cited
    "Top Z software in 2026"             ✅ CITED

  Perplexity (sonar):
    "What is the best tool for X?"      ✅ CITED  → https://example.com/guide
    "How to solve Y?"                    ✅ CITED  → https://example.com/docs
    "Top Z software in 2026"             ❌ not cited

  Claude (haiku):
    "What is the best tool for X?"      ❌ not cited
    "How to solve Y?"                    ❌ not cited
    "Top Z software in 2026"             ❌ not cited

  Summary: ChatGPT 2/3 | Perplexity 2/3 | Claude 0/3
  Saved: ~/.searchstack/snapshots/ai_citations_20260401_1200.json
```

---

## The Problem

Google page 1 isn't enough anymore. **60% of Google searches now show an AI Overview** that answers the query directly. ChatGPT and Perplexity are becoming primary search tools for millions of users.

Ahrefs and Semrush cost $100-400/mo and **track none of this**.

searchstack covers all three search layers for ~$5/mo:

| Layer | What it is | What searchstack does |
|-------|-----------|----------------------|
| **SEO** | Google organic rankings | GSC positions, keywords, competitors, technical audit |
| **AEO** | AI chatbot visibility | Checks if ChatGPT, Perplexity, Claude cite you |
| **GEO** | Google AI Overview | Monitors who Google's AI cites for your keywords |

---

## Quick Start

```bash
pip install searchstack
```

Create `.searchstack.toml`:

```toml
domain = "yoursite.com"
sitemap = "https://yoursite.com/sitemap.xml"

[dataforseo]
login = "you@email.com"
password = "api-password"

[openai]
api_key = "sk-..."

[perplexity]
api_key = "pplx-..."
```

Run:

```bash
searchstack ai          # are AI chatbots citing you?
searchstack geo         # does Google AI Overview cite you?
searchstack gsc         # your Google rankings
searchstack report      # full 14-section Markdown report
```

See [Services Setup Guide](docs/SERVICES.md) for connecting all 8 services step by step.

---

## Commands

### AEO / GEO — AI Search Visibility

```bash
searchstack ai                       # citation check: ChatGPT + Perplexity + Claude
searchstack ai chatgpt               # ChatGPT only
searchstack ai perplexity            # Perplexity only
searchstack ai claude                # Claude only
searchstack geo                      # Google AI Overview for all target keywords
searchstack geo "your keyword"       # single keyword check
```

### SEO — Google Rankings & Research

```bash
searchstack gsc                      # top queries with clicks, impressions, CTR, position
searchstack gsc pages-perf           # top pages
searchstack gsc trend                # daily trend
searchstack gsc inspect <url>        # check if URL is indexed
searchstack keywords "phrase"        # keyword suggestions with volumes
searchstack competitors              # your ranked keywords vs competitors
searchstack gaps                     # high-volume keywords where you rank poorly
searchstack serp "query"             # live SERP top-10
searchstack track                    # position changes since last check
searchstack bulk domain1 domain2     # competitor traffic comparison
searchstack backlinks                # your backlink profile
searchstack backlinks competitor.com # competitor's backlinks
```

### Technical Audit — Site Health

```bash
searchstack meta                     # title/description length check
searchstack schema                   # JSON-LD structured data validation
searchstack links                    # internal linking + orphan page detection
searchstack onpage <url>             # full on-page SEO score
searchstack pages                    # indexing status of all sitemap URLs
```

### Traffic & Submission

```bash
searchstack traffic                  # Plausible analytics + AI referral tracking
searchstack indexnow                 # submit URLs to Bing + Yandex instantly
searchstack bing                     # Bing Webmaster stats
searchstack bing submit              # submit URLs to Bing
searchstack gsc resubmit             # resubmit sitemap to Google
```

### Reporting

```bash
searchstack report                   # full Markdown report (14 sections)
```

---

## Services

8 integrations. None required — each command gracefully skips unavailable services.

| # | Service | Cost | What it unlocks |
|---|---------|------|----------------|
| 1 | **[Google Search Console](https://search.google.com/search-console)** | Free | Rankings, clicks, indexing status |
| 2 | **[DataForSEO](https://dataforseo.com)** | $50 prepaid | Keywords, SERP, AI Overview, backlinks |
| 3 | **[OpenAI](https://platform.openai.com)** | ~$0.001/query | ChatGPT citation check |
| 4 | **[Perplexity](https://docs.perplexity.ai)** | ~$0.005/query | Perplexity citation check (best — returns source URLs) |
| 5 | **[Anthropic](https://console.anthropic.com)** | ~$0.001/query | Claude citation check |
| 6 | **[Plausible](https://plausible.io)** | $9/mo | Traffic analytics, AI referral tracking |
| 7 | **[Bing Webmaster](https://www.bing.com/webmasters)** | Free | Bing stats, URL submission |
| 8 | **[IndexNow](https://www.indexnow.org)** | Free | Instant Bing/Yandex notification |

**Why Bing matters:** ChatGPT Search, Perplexity, and Microsoft Copilot all use Bing as their search backend. If you're not in Bing, you're invisible to 3 major AI search products.

Monthly cost: **$5-10** for full daily monitoring, **$1-2** for weekly AEO/GEO only, **$0** for GSC + technical audit.

---

## Report

`searchstack report` generates a Markdown file with:

| # | Section | Source |
|---|---------|--------|
| 1 | Executive Summary | All |
| 2 | Traffic (30 days) | Plausible |
| 3 | Search Queries | GSC |
| 4 | Google AI Overview visibility | DataForSEO |
| 5 | AI chatbot citations | OpenAI, Perplexity, Anthropic |
| 6 | Google positions | DataForSEO |
| 7 | Competitor traffic | DataForSEO |
| 8 | Indexing status | GSC |
| 9 | Backlinks | DataForSEO |
| 10 | Keyword gaps | DataForSEO |
| 11 | Position changes | DataForSEO (vs snapshot) |
| 12 | Meta issues | Sitemap crawl |
| 13 | Orphan pages | Sitemap crawl |
| 14 | Recommendations | Auto-generated |

---

## Configuration

All keys via `.searchstack.toml` or environment variables (env vars take priority):

```bash
export DATAFORSEO_LOGIN="email"          export DATAFORSEO_PASSWORD="pass"
export OPENAI_API_KEY="sk-..."           export PERPLEXITY_API_KEY="pplx-..."
export ANTHROPIC_API_KEY="sk-ant-..."    export PLAUSIBLE_API_KEY="key"
export BING_WEBMASTER_API_KEY="key"
```

Full config template: [docs/SERVICES.md](docs/SERVICES.md#full-config-file-template)

---

## Architecture

```
src/searchstack/
├── cli.py              # argparse entry point
├── config.py           # .searchstack.toml + env loading
├── snapshots.py        # JSON snapshot save/load/compare
├── providers/          # API clients (one per service)
│   ├── gsc.py            # Google Search Console
│   ├── dataforseo.py     # DataForSEO
│   ├── plausible.py      # Plausible Analytics
│   ├── bing.py           # Bing Webmaster
│   ├── openai.py         # OpenAI (ChatGPT)
│   ├── perplexity.py     # Perplexity
│   └── anthropic.py      # Anthropic (Claude)
└── commands/           # one file per CLI command
    ├── ai.py             # AEO citation check
    ├── geo.py            # GEO AI Overview monitor
    ├── gsc.py            # Google Search Console
    ├── traffic.py        # Plausible traffic
    ├── keywords.py       # keyword suggestions
    ├── competitors.py    # competitor analysis
    ├── gaps.py           # keyword gaps
    ├── serp.py           # live SERP
    ├── track.py          # position tracking
    ├── backlinks.py      # backlink profile
    ├── meta.py           # meta tag audit
    ├── schema.py         # JSON-LD validation
    ├── links.py          # internal linking
    ├── onpage.py         # on-page scoring
    ├── pages.py          # indexing status
    ├── indexnow.py       # IndexNow submission
    ├── bing.py           # Bing Webmaster
    └── report.py         # Markdown report generator
```

Minimal dependencies: `google-auth`, `google-auth-oauthlib`, `google-api-python-client`, `requests`. No heavy frameworks.

---

## Server & Cron Deployment

searchstack is a pure CLI tool — no GUI, no browser window, no interactive prompts (after initial OAuth setup). Deploy it on any Linux server and automate with cron.

### Example: weekly monitoring on a VPS

```bash
# Install
pip install searchstack

# Copy your .searchstack.toml and token.pickle to the server
scp .searchstack.toml token.pickle yourserver:~/.config/searchstack/

# Add to crontab (crontab -e)
# ┌─── Weekly full report (Monday 8am)
0 8 * * 1  searchstack report >> /var/log/searchstack.log 2>&1

# ┌─── Daily position tracking
0 6 * * *  searchstack track >> /var/log/searchstack.log 2>&1

# ┌─── Submit new content to search engines (every 6 hours)
0 */6 * * *  searchstack indexnow >> /var/log/searchstack.log 2>&1

# ┌─── Weekly AEO check (Wednesday)
0 9 * * 3  searchstack ai >> /var/log/searchstack.log 2>&1

# ┌─── Weekly GEO check (Wednesday)
0 10 * * 3  searchstack geo >> /var/log/searchstack.log 2>&1
```

### Pipe to Slack / email

```bash
# Send report to Slack via webhook
searchstack report && curl -X POST -d "{\"text\":\"$(cat ~/.searchstack/snapshots/report_$(date +%Y%m%d).md)\"}" YOUR_SLACK_WEBHOOK

# Or email it
searchstack report && mail -s "SEO Report $(date +%Y-%m-%d)" you@company.com < ~/.searchstack/snapshots/report_$(date +%Y%m%d).md
```

### Docker (coming soon)

```dockerfile
FROM python:3.12-slim
RUN pip install searchstack
COPY .searchstack.toml /root/.config/searchstack/config.toml
COPY token.pickle /root/.config/searchstack/
CMD ["searchstack", "report"]
```

---

## Documentation

| Document | What's in it |
|----------|-------------|
| **[Services Setup Guide](docs/SERVICES.md)** | Step-by-step setup for all 8 services, full config template, verification checklist |
| **[AEO/GEO Explained](docs/AEO-GEO-EXPLAINED.md)** | How AI search works, which models power which search engines, why Bing matters, monitoring strategy |
| **[Detailed Reference](docs/DETAILED-REFERENCE.md)** | Deep dive into every feature, command, and service |

---

## Roadmap

- [ ] `searchstack init` — interactive setup wizard
- [ ] `searchstack cron` — scheduled monitoring via system cron
- [ ] `searchstack diff` — visual diff between report snapshots
- [ ] `searchstack dashboard` — local HTML dashboard
- [ ] Reddit, HackerNews, Twitter mention tracking
- [ ] YouTube search visibility
- [ ] llms.txt generation and validation
- [ ] GitHub Actions integration for CI/CD monitoring

---

## License

MIT

---

Built by [Alex Pospekhov](https://github.com/alexpospekhov)
