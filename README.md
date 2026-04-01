# Searchstack — AEO/GEO/SEO for AI-native founders

> Open-source AEO / GEO / SEO tech stack for AI-native founders.

[![PyPI](https://img.shields.io/pypi/v/searchstack.svg)](https://pypi.org/project/searchstack/)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

Monitor your visibility across Google, AI Overviews, ChatGPT, Perplexity & Claude — from one CLI.

<p align="center">
  <img src="demo/searchstack-demo.gif" alt="searchstack CLI demo" width="900">
</p>

## Who is this for

- **AI-native founders** — you're building a product and need to be visible in both Google AND AI search, but don't have $400/mo for Semrush
- **Indie hackers & solo devs** — you ship content, want to know if it's working, and prefer CLI over dashboards
- **SEO-aware engineers** — you understand technical SEO but need a tool that also covers the new AEO/GEO landscape
- **Agency operators** — you manage SEO for multiple clients and need automated reports you can schedule and pipe to Slack

If you've ever wondered *"Does ChatGPT know my product exists?"* — this tool answers that question.

---

## searchstack vs The Rest

| Feature | searchstack | Ahrefs ($99+/mo) | Semrush ($130+/mo) | Free tools |
|---------|:-----------:|:-----------------:|:-------------------:|:----------:|
| Google rankings (GSC) | ✅ | ✅ | ✅ | ✅ GSC only |
| Keyword research | ✅ | ✅ | ✅ | ❌ |
| Backlink analysis | ✅ | ✅ | ✅ | ❌ |
| Technical audit | ✅ | ✅ | ✅ | Partial |
| **ChatGPT citation check** | ✅ | ❌ | ❌ | ❌ |
| **Perplexity citation check** | ✅ | ❌ | ❌ | ❌ |
| **Claude citation check** | ✅ | ❌ | ❌ | ❌ |
| **Grok (xAI) citation check** | ✅ | ❌ | ❌ | ❌ |
| **Local LLM check (Ollama)** | ✅ | ❌ | ❌ | ❌ |
| **Google AI Overview monitor** | ✅ | ❌ | ❌ | ❌ |
| **AI referral tracking** | ✅ | ❌ | ❌ | ❌ |
| CLI / scriptable | ✅ | ❌ | ❌ | ❌ |
| Cron / server deploy | ✅ | ❌ | ❌ | ❌ |
| Markdown reports | ✅ | ❌ PDF only | ❌ PDF only | ❌ |
| Open source | ✅ | ❌ | ❌ | Varies |
| Monthly cost | **~$5** | $99-999 | $130-500 | $0 (limited) |

The bottom 5 rows are what no existing tool does. That's why searchstack exists.

---

### What's inside

- **AEO Monitor** — check if ChatGPT, Perplexity, Claude, Grok, and **local models (Ollama/Qwen/Llama)** cite your site when users ask about your niche
- **GEO Monitor** — track Google AI Overview: who gets cited for your target keywords (and whether it's you)
- **Google Search Console** — rankings, clicks, impressions, CTR, indexing status, sitemap health
- **Keyword Research** — suggestions, volumes, competitor overlap, keyword gaps (DataForSEO)
- **Position Tracking** — compare rankings over time, detect improvements and drops
- **Backlink Analysis** — your profile + competitor backlinks, referring domains, domain rank
- **Technical Audit** — meta tags, JSON-LD validation, internal linking, orphan pages, on-page scoring
- **Traffic Analytics** — Plausible integration with AI referral breakdown (chatgpt.com, perplexity.ai, claude.ai)
- **Search Submission** — IndexNow (instant Bing/Yandex), Bing Webmaster, GSC sitemap resubmit
- **llms.txt Generator** — `searchstack llms generate` creates llms.txt + llms-full.txt from your sitemap following the [llmstxt.org](https://llmstxt.org) spec. Validate with `searchstack llms validate`.
- **Content Monitor** — `searchstack monitor` shows per-page performance: rankings, clicks, indexing status, keyword tracking, changes since last check.
- **SEO Audit** — `searchstack audit` combines GSC data with keyword volumes, calculates opportunity scores, finds content gaps.
- **Markdown Reports** — `searchstack report` generates a full 14-section .md file with executive summary and auto-recommendations. Run it monthly, diff the results, track progress over time.
- **Local LLM Support** — run AEO checks against Ollama, LM Studio, vLLM, or any OpenAI-compatible local model. Test how open-source models (Qwen, Llama, Mistral, Gemma) represent your brand — completely free, no API keys, runs offline.
- **Cron-ready** — pure CLI, no GUI, no browser. Deploy on any server, schedule via cron (`0 8 * * 1 searchstack report`), pipe output to Slack/email. Built for automation.

**22 commands. 10 API integrations (5 cloud AI + local LLMs). One config file. Runs anywhere Python runs.**

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

## Try it free (no API keys needed)

These commands work with zero configuration — they just crawl your sitemap:

```bash
pip install searchstack

# Check meta tags on all your pages
searchstack meta

# Validate JSON-LD structured data
searchstack schema

# Find orphan pages (no internal links)
searchstack links

# Full on-page SEO score for any URL
searchstack onpage https://yoursite.com/pricing
```

No API keys. No accounts. No config file. Just install and run.

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

See [Services Setup Guide](docs/SERVICES.md) for connecting all 9 services step by step.

---

## Commands

### AEO / GEO — AI Search Visibility

```bash
searchstack ai                       # citation check: ChatGPT + Perplexity + Claude + Grok
searchstack ai chatgpt               # ChatGPT only
searchstack ai perplexity            # Perplexity only
searchstack ai claude                # Claude only
searchstack ai grok                  # Grok (xAI) only
searchstack ai ollama                # local model (Ollama/LM Studio/vLLM)
searchstack geo                      # Google AI Overview for all target keywords
searchstack geo "your keyword"       # single keyword check
searchstack llms generate            # generate llms.txt + llms-full.txt from your sitemap
searchstack llms validate            # validate existing llms.txt against spec
searchstack llms check               # check if your site has AI-ready files
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

### Dashboards & Reporting

```bash
searchstack monitor                  # site health: traffic + rankings + indexing per page
searchstack audit                    # full SEO audit with keyword volumes + opportunity scores
searchstack report                   # full Markdown report (14 sections)
```

---

## Services

9 integrations. None required — each command gracefully skips unavailable services.

| # | Service | Cost | What it unlocks |
|---|---------|------|----------------|
| 1 | **[Google Search Console](https://search.google.com/search-console)** | Free | Rankings, clicks, indexing status |
| 2 | **[DataForSEO](https://dataforseo.com)** | $50 prepaid | Keywords, SERP, AI Overview, backlinks |
| 3 | **[OpenAI](https://platform.openai.com)** | ~$0.001/query | ChatGPT citation check |
| 4 | **[Perplexity](https://docs.perplexity.ai)** | ~$0.005/query | Perplexity citation check (best — returns source URLs) |
| 5 | **[Anthropic](https://console.anthropic.com)** | ~$0.001/query | Claude citation check |
| 6 | **[xAI](https://console.x.ai)** | ~$0.002/query | Grok citation check |
| 7 | **[Plausible](https://plausible.io)** | $9/mo | Traffic analytics, AI referral tracking |
| 8 | **[Bing Webmaster](https://www.bing.com/webmasters)** | Free | Bing stats, URL submission |
| 9 | **[IndexNow](https://www.indexnow.org)** | Free | Instant Bing/Yandex notification |
| 10 | **[Ollama](https://ollama.com)** / any local LLM | Free | Test local models (Qwen, Llama, Mistral, Gemma) |

**Why Bing matters:** ChatGPT Search, Perplexity, and Microsoft Copilot all use Bing as their search backend. If you're not in Bing, you're invisible to 3 major AI search products.

### Local LLM setup (Ollama, LM Studio, vLLM)

Run AEO checks against local models — free, offline, no API keys:

```bash
# 1. Install Ollama and pull a model
brew install ollama
ollama pull qwen3:8b

# 2. Add to .searchstack.toml
# [ollama]
# base_url = "http://localhost:11434/v1"
# model = "qwen3:8b"

# 3. Run
searchstack ai ollama
```

Works with any OpenAI-compatible server:

| Server | Config `base_url` | Notes |
|--------|------------------|-------|
| **Ollama** | `http://localhost:11434/v1` | Default, easiest setup |
| **LM Studio** | `http://localhost:1234/v1` | GUI for managing models |
| **vLLM** | `http://localhost:8000/v1` | Production-grade serving |
| **llama.cpp** | `http://localhost:8080/v1` | Lightweight C++ server |
| **LocalAI** | `http://localhost:8080/v1` | Drop-in OpenAI replacement |

**Why test local models?** Open-source LLMs (Qwen, Llama, Mistral, Gemma) are increasingly used in products, search tools, and agents. Knowing how they represent your brand helps you optimize content for the entire AI ecosystem — not just the big 4.

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
| 5 | AI chatbot citations | OpenAI, Perplexity, Anthropic, xAI |
| 6 | Google positions | DataForSEO |
| 7 | Competitor traffic | DataForSEO |
| 8 | Indexing status | GSC |
| 9 | Backlinks | DataForSEO |
| 10 | Keyword gaps | DataForSEO |
| 11 | Position changes | DataForSEO (vs snapshot) |
| 12 | Meta issues | Sitemap crawl |
| 13 | Orphan pages | Sitemap crawl |
| 14 | Recommendations | Auto-generated |

### Sample report output

<details>
<summary>Click to expand a report fragment</summary>

```markdown
# SEO/AEO/GEO Report — 01-04-2026

> yoursite.com | Generated 2026-04-01 09:00

## Executive Summary

| Metric | Value |
|--------|-------|
| Visitors (30 days) | **1,247** |
| Google AI cites us | **0** times |
| Backlinks | 89 (from 23 domains) |
| Keyword gaps (not in top-10) | 12 |
| Positions: improved / declined | 5 / 2 |

**Status:** 🟡 Growing

## 3. Google AI Overview visibility (GEO)

- Keywords checked: 23
- AI Overview present: 18/23
- **AI cites us: 0**
- Organic top-10: 7

### Top Cited (instead of us)

| Domain | Times cited |
|--------|------------|
| competitor1.com | 8 |
| competitor2.com | 5 |
| wikipedia.org | 4 |

## 4. AI chatbot citations (AEO)

- ✅ **ChatGPT**: 3/8 queries cite us
- ✅ **Perplexity**: 5/8 queries cite us
- ❌ **Claude**: 0/8 queries cite us

## Recommendations

- 🤖 **Google AI never cites us** — improve citation-ready content
- 🎯 **12 keyword gaps** — update existing articles for these queries
- 🔗 **Low backlinks (23 domains)** — need outreach campaign
```

</details>

---

## Configuration

All keys via `.searchstack.toml` or environment variables (env vars take priority):

```bash
export DATAFORSEO_LOGIN="email"          export DATAFORSEO_PASSWORD="pass"
export OPENAI_API_KEY="sk-..."           export PERPLEXITY_API_KEY="pplx-..."
export ANTHROPIC_API_KEY="sk-ant-..."    export XAI_API_KEY="xai-..."
export PLAUSIBLE_API_KEY="key"           export BING_WEBMASTER_API_KEY="key"
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
│   ├── anthropic.py      # Anthropic (Claude)
│   ├── grok.py           # Grok (xAI)
│   └── google_ads.py     # Google Ads Keyword Planner
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
    ├── report.py         # Markdown report generator
    ├── monitor.py        # Site health monitor
    ├── audit.py          # SEO audit with opportunity scores
    └── llms.py           # llms.txt generation and validation
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
| **[Services Setup Guide](docs/SERVICES.md)** | Step-by-step setup for all 9 services, full config template, verification checklist |
| **[AEO/GEO Explained](docs/AEO-GEO-EXPLAINED.md)** | How AI search works, which models power which search engines, why Bing matters, monitoring strategy |
| **[Detailed Reference](docs/DETAILED-REFERENCE.md)** | Deep dive into every feature, command, and service |
| **[llmstxt.org spec](https://llmstxt.org)** | The llms.txt standard — `searchstack llms` implements generation and validation with built-in docs |

---

## FAQ

<details>
<summary><strong>Do I need all 9 services?</strong></summary>

No. Each command gracefully skips unavailable services. You can start with just the free tools (`meta`, `schema`, `links`, `onpage`) and add API keys as needed. The most impactful paid service is DataForSEO ($50 one-time) — it unlocks GEO monitoring, keyword research, and competitor analysis.

</details>

<details>
<summary><strong>How much does it actually cost per month?</strong></summary>

- **$0/mo** — GSC + technical audit (meta, schema, links, onpage, pages)
- **$1-2/mo** — add weekly AEO + GEO monitoring
- **$5-10/mo** — full daily monitoring including all API calls
- **$50 one-time** — DataForSEO deposit (lasts months, no subscription)

Compare: Ahrefs starts at $99/mo, Semrush at $130/mo, and neither tracks AI visibility.

</details>

<details>
<summary><strong>Does searchstack work without DataForSEO?</strong></summary>

Yes. Without DataForSEO you lose: keyword research, live SERP, GEO monitoring, competitor analysis, backlink checks, and position tracking. You keep: GSC rankings, AEO citation checks (ChatGPT/Perplexity/Claude/Grok), Plausible traffic, technical audit, Bing submission, and IndexNow.

</details>

<details>
<summary><strong>Is this a replacement for Ahrefs/Semrush?</strong></summary>

For technical SEO and AI search monitoring — yes. For features like site explorer, content gap analysis at scale, or rank tracking with 10,000+ keywords — no. searchstack is designed for founders and small teams who need the most impactful SEO data without enterprise pricing.

</details>

<details>
<summary><strong>Can I monitor multiple sites?</strong></summary>

Currently one site per config file. For multiple sites, use separate `.searchstack.toml` files and run with `--config` flag (coming soon) or separate directories.

</details>

<details>
<summary><strong>Why does ChatGPT Search use Bing?</strong></summary>

Microsoft invested $13B in OpenAI. As part of the deal, ChatGPT Search uses Bing as its search backend. Perplexity and Microsoft Copilot also use Bing. This means **3 out of 5 major AI search products** pull from Bing, not Google. Read more in [AEO/GEO Explained](docs/AEO-GEO-EXPLAINED.md#the-critical-role-of-bing).

</details>

---

## Roadmap

- [ ] `searchstack init` — interactive setup wizard
- [ ] `searchstack cron` — scheduled monitoring via system cron
- [ ] `searchstack diff` — visual diff between report snapshots
- [ ] `searchstack dashboard` — local HTML dashboard
- [ ] Reddit, HackerNews, Twitter mention tracking
- [ ] YouTube search visibility
- [x] ~~llms.txt generation and validation~~ (shipped in v0.1.0)
- [ ] GitHub Actions integration for CI/CD monitoring

---

## License

MIT

---

Built by [Alex Pospekhov](https://github.com/alexpospekhov)
