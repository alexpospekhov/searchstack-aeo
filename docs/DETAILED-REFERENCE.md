# searchstack

**Open-source SEO / AEO / GEO tech stack for AI founders.**

Monitor your visibility across Google, AI Overviews, ChatGPT, Perplexity & Claude — from one CLI.

```bash
pip install searchstack
searchstack report    # full Markdown report with 14 sections
```

**New to AEO/GEO?** Read [The AEO/GEO Stack Explained](docs/AEO-GEO-EXPLAINED.md) — how AI search works, which models power which search engines, and why Bing matters more than you think.

**Ready to set up?** Follow the [Services Setup Guide](docs/SERVICES.md) — step-by-step instructions for connecting all 8 external services.

---

## Why searchstack

SEO changed. Ranking on Google page 1 is no longer enough.

- **Google AI Overviews** answer queries directly — your link may never get clicked
- **ChatGPT, Perplexity, Claude** are becoming search engines — do they mention you?
- Traditional SEO tools (Ahrefs, Semrush) cost $100-400/mo and don't track AI visibility at all

searchstack is a single CLI that covers all three layers:

| Layer | What it means | What searchstack does |
|-------|--------------|----------------------|
| **SEO** | Classic Google rankings | GSC positions, keyword tracking, competitor analysis, technical audit |
| **AEO** | Answer Engine Optimization | Checks if ChatGPT, Perplexity, and Claude cite your site |
| **GEO** | Generative Engine Optimization | Monitors Google AI Overview — who gets cited instead of you |

One command. One config file. All three covered.

---

## Features

### AEO — AI Citation Monitoring
- Query ChatGPT (GPT-4o-mini), Perplexity (Sonar), and Claude (Haiku) with your target questions
- Detect whether each AI mentions or links to your domain
- Track citation rates over time with snapshots
- Configurable query list per domain

### GEO — Google AI Overview Tracking
- Check which domains Google AI Overview cites for your target keywords
- Track your organic position alongside AI Overview presence
- Identify who gets cited instead of you
- Cost: ~$0.008 per keyword via DataForSEO

### SEO — Traditional Search
- **Google Search Console**: queries, clicks, impressions, CTR, position trends, device/country breakdowns
- **Keyword Research**: suggestions, search volumes, competition (DataForSEO)
- **Competitor Analysis**: ranked keywords overlap, bulk traffic estimation
- **Keyword Gaps**: high-volume keywords where you rank outside top-10
- **Position Tracking**: compare with previous snapshots, detect improvements and drops
- **Backlink Profile**: total backlinks, referring domains, top referrers

### Technical SEO Audit
- **Meta Check**: title and description length validation on all sitemap URLs
- **JSON-LD Validation**: verify structured data (Schema.org) on every page
- **Internal Linking**: find orphan pages (no internal links point to them)
- **On-Page Scoring**: H1/H2 structure, image alt tags, word count, canonical tags
- **Indexing Status**: check every sitemap URL via GSC URL Inspection API

### Traffic Analytics
- **Plausible Integration**: visitors, sources, top pages, bounce rate, devices, countries
- **AI Referral Tracking**: traffic from chatgpt.com, perplexity.ai, claude.ai broken down by landing page
- **Daily Trends**: 7-day and 30-day traffic visualization

### Search Engine Submission
- **IndexNow**: submit all sitemap URLs to Bing and Yandex instantly
- **Bing Webmaster**: URL submission, sitemap submission, quota tracking, query stats
- **GSC Sitemap**: resubmit sitemap to Google

### Reporting
- **Full Markdown Report**: 14-section report covering traffic, GSC, GEO, AEO, competitors, backlinks, gaps, meta issues, orphan pages, position changes, and recommendations
- **Auto-recommendations**: actionable suggestions based on collected data
- **Executive Summary**: top-level metrics at a glance

---

## Commands

```bash
searchstack                          # full report (everything)
searchstack report                   # generate Markdown report file

# AEO / GEO
searchstack ai                       # AI citation check (ChatGPT + Perplexity + Claude)
searchstack ai chatgpt               # ChatGPT only
searchstack ai perplexity            # Perplexity only
searchstack ai claude                # Claude only
searchstack geo                      # Google AI Overview for all target keywords
searchstack geo "custom query"       # single keyword AI Overview check

# Google Search Console
searchstack gsc                      # top queries (clicks, impressions, CTR, position)
searchstack gsc pages-perf           # top pages performance
searchstack gsc devices              # device breakdown
searchstack gsc countries            # country breakdown
searchstack gsc trend                # daily impressions/clicks trend
searchstack gsc sitemaps             # sitemap status
searchstack gsc inspect <url>        # check indexing of specific URL
searchstack gsc resubmit             # resubmit sitemap

# Keyword Research (DataForSEO)
searchstack keywords "tiktok shop"   # keyword suggestions with volumes
searchstack competitors              # your ranked keywords + overlap
searchstack gaps                     # keywords with high volume where you rank poorly
searchstack serp "query"             # live SERP top-10 for any query
searchstack track                    # compare positions with previous snapshot
searchstack bulk domain1 domain2     # competitor traffic estimation

# Technical Audit
searchstack meta                     # title/description length check on all pages
searchstack schema                   # JSON-LD validation on all pages
searchstack links                    # internal linking analysis + orphan detection
searchstack onpage <url>             # detailed on-page SEO score for a URL
searchstack pages                    # indexing status of ALL sitemap URLs

# Traffic
searchstack traffic                  # Plausible: sources, pages, AI referrals, trends

# Backlinks
searchstack backlinks                # your backlink profile
searchstack backlinks competitor.com # competitor backlink profile

# Submission
searchstack indexnow                 # submit all URLs to IndexNow (Bing/Yandex)
searchstack bing                     # Bing Webmaster quota + query stats
searchstack bing submit              # submit URLs to Bing
searchstack bing sitemap             # submit sitemap to Bing
```

---

## External Services

searchstack integrates with 8 external services. None are strictly required — each command gracefully skips unavailable providers.

### Required for core functionality

| # | Service | What it provides | Free tier | Signup |
|---|---------|-----------------|-----------|--------|
| 1 | **Google Search Console** | Rankings, clicks, impressions, indexing status | Free (unlimited) | [search.google.com/search-console](https://search.google.com/search-console) |
| 2 | **DataForSEO** | Keywords, SERP, AI Overview, backlinks, competitor traffic | $50 prepaid balance (lasts months) | [dataforseo.com](https://dataforseo.com) |

### Required for AEO (AI citation checks)

| # | Service | What it provides | Cost per check | Signup |
|---|---------|-----------------|----------------|--------|
| 3 | **OpenAI API** | ChatGPT citation check | ~$0.001/query (GPT-4o-mini) | [platform.openai.com](https://platform.openai.com) |
| 4 | **Perplexity API** | Perplexity citation check with source URLs | ~$0.005/query (Sonar) | [docs.perplexity.ai](https://docs.perplexity.ai) |
| 5 | **Anthropic API** | Claude citation check | ~$0.001/query (Haiku) | [console.anthropic.com](https://console.anthropic.com) |

### Optional (recommended)

| # | Service | What it provides | Free tier | Signup |
|---|---------|-----------------|-----------|--------|
| 6 | **Plausible Analytics** | Privacy-first traffic analytics, AI referral tracking | Paid ($9/mo) or self-hosted (free) | [plausible.io](https://plausible.io) |
| 7 | **Bing Webmaster Tools** | Bing rankings, URL submission, query stats | Free (unlimited) | [bing.com/webmasters](https://www.bing.com/webmasters) |
| 8 | **IndexNow** | Instant URL submission to Bing + Yandex | Free (unlimited) | [indexnow.org](https://www.indexnow.org) |

### Cost estimate

| Scenario | Monthly cost |
|----------|-------------|
| Full daily monitoring (all services) | ~$5-10/mo |
| Weekly AEO + GEO check only | ~$1-2/mo |
| GSC + technical audit only | Free |

---

## Setup

### 1. Install

```bash
pip install searchstack
```

Or from source:

```bash
git clone https://github.com/hyperfocus-tech/searchstack.git
cd searchstack
pip install -e .
```

### 2. Configure

Create a `.searchstack.toml` in your project root (or `~/.config/searchstack/config.toml` for global config):

```toml
# Your website
domain = "example.com"
sitemap = "https://example.com/sitemap.xml"

# ── Google Search Console ──────────────────────────────
[gsc]
# OAuth2 credentials from Google Cloud Console
# 1. Go to https://console.cloud.google.com/apis/credentials
# 2. Create Credentials → OAuth client ID → Desktop app
# 3. Download JSON and set the path below
credentials_file = "credentials.json"
# token.pickle is created automatically on first run (opens browser for OAuth)
site_url = "sc-domain:example.com"
# GCP project for quota attribution (optional)
gcp_project = ""

# ── DataForSEO ─────────────────────────────────────────
[dataforseo]
# Signup at https://dataforseo.com → get login/password
# Or set env vars: DATAFORSEO_LOGIN, DATAFORSEO_PASSWORD
login = ""
password = ""
# Default location for keyword/SERP lookups (2840 = United States)
location_code = 2840
language_code = "en"

# ── Plausible ──────────────────────────────────────────
[plausible]
# API key from https://plausible.io/settings → API keys
# Or set env var: PLAUSIBLE_API_KEY
api_key = ""
site_id = "example.com"

# ── Bing Webmaster ─────────────────────────────────────
[bing]
# API key from https://www.bing.com/webmasters → API Access
# Or set env var: BING_WEBMASTER_API_KEY
api_key = ""

# ── IndexNow ───────────────────────────────────────────
[indexnow]
# Your IndexNow key (any string — must match the key file hosted on your site)
# Host a file at https://example.com/{key}.txt containing the key itself
key = ""

# ── AEO: AI Citation Check ────────────────────────────
[openai]
# Or set env var: OPENAI_API_KEY
api_key = ""

[perplexity]
# Or set env var: PERPLEXITY_API_KEY
api_key = ""

[anthropic]
# Or set env var: ANTHROPIC_API_KEY
api_key = ""

# ── Target Queries for AI Citation Check ───────────────
# These are the questions searchstack asks ChatGPT/Perplexity/Claude
# to see if they mention your site.
[ai_queries]
queries = [
    "What is the best tool for [your niche]?",
    "How to solve [problem your product solves]?",
    "What are the top [your category] tools in 2026?",
]

# ── Target Keywords for GEO Monitoring ─────────────────
# Grouped by topic. searchstack checks Google AI Overview for each.
[geo_keywords]
main = [
    "your product category",
    "best tool for X 2026",
]
features = [
    "how to do Y",
    "Z calculator",
]

# ── Competitors for bulk traffic comparison ────────────
[competitors]
domains = [
    "competitor1.com",
    "competitor2.com",
    "competitor3.com",
]
```

### 3. Authenticate Google Search Console

On first run of any `gsc` command, searchstack opens your browser for OAuth consent:

```bash
searchstack gsc
# → Opens browser → sign in with Google → grant Search Console access
# → token.pickle is saved locally (auto-refreshes)
```

Required OAuth scopes:
- `https://www.googleapis.com/auth/webmasters.readonly` — read rankings and analytics
- `https://www.googleapis.com/auth/webmasters` — resubmit sitemaps
- `https://www.googleapis.com/auth/indexing` — URL inspection

### 4. Environment variables

All API keys can be set via environment variables instead of the config file:

```bash
export DATAFORSEO_LOGIN="your-email@example.com"
export DATAFORSEO_PASSWORD="your-api-password"
export PLAUSIBLE_API_KEY="your-plausible-key"
export BING_WEBMASTER_API_KEY="your-bing-key"
export OPENAI_API_KEY="sk-..."
export PERPLEXITY_API_KEY="pplx-..."
export ANTHROPIC_API_KEY="sk-ant-..."
```

Environment variables take priority over config file values.

---

## How Each Service Is Used

### Google Search Console (Free)

**What you get:** Real ranking data directly from Google. Clicks, impressions, CTR, average position for every query and page. URL indexing status. Sitemap health.

**Setup:**
1. Verify your site in [Google Search Console](https://search.google.com/search-console)
2. Create OAuth Desktop credentials in [GCP Console](https://console.cloud.google.com/apis/credentials)
3. Enable "Google Search Console API" and "Web Search Indexing API" in your GCP project
4. Download the credentials JSON and point `credentials_file` to it

**Commands:** `gsc`, `pages`

---

### DataForSEO ($50+ prepaid)

**What you get:** Keyword volumes, live SERP results, Google AI Overview data, backlink profiles, competitor traffic estimates. This is the only paid API that provides AI Overview monitoring.

**Setup:**
1. Sign up at [dataforseo.com](https://dataforseo.com)
2. Add $50 balance (no subscription — pay-as-you-go)
3. Get your login (email) and API password from the dashboard

**Cost breakdown:**
| Endpoint | Cost per request | Used by |
|----------|-----------------|---------|
| Keyword Suggestions | ~$0.05 | `keywords` |
| SERP (live, advanced) | ~$0.008 | `geo`, `serp` |
| Ranked Keywords | ~$0.02 | `competitors`, `gaps`, `track` |
| Bulk Traffic Estimation | ~$0.01 | `bulk` |
| Backlinks Summary | ~$0.02 | `backlinks` |
| Referring Domains | ~$0.02 | `backlinks` |

A typical weekly check of 23 GEO keywords + competitor analysis costs ~$0.25.

**Commands:** `geo`, `keywords`, `competitors`, `gaps`, `serp`, `track`, `bulk`, `backlinks`

---

### OpenAI API (~$0.001/query)

**What you get:** Ask ChatGPT your target questions and detect whether it mentions your domain in the response.

**Setup:**
1. Get API key at [platform.openai.com](https://platform.openai.com)
2. Uses `gpt-4o-mini` model (cheapest, sufficient for citation detection)

**Commands:** `ai`, `ai chatgpt`

---

### Perplexity API (~$0.005/query)

**What you get:** Ask Perplexity and check both the response text AND the citations array. Perplexity returns explicit source URLs, making citation detection reliable.

**Setup:**
1. Get API key at [docs.perplexity.ai](https://docs.perplexity.ai)
2. Uses `sonar` model

**Commands:** `ai`, `ai perplexity`

---

### Anthropic API (~$0.001/query)

**What you get:** Ask Claude and check if it mentions your domain. Claude typically doesn't cite URLs directly, but may mention product names.

**Setup:**
1. Get API key at [console.anthropic.com](https://console.anthropic.com)
2. Uses `claude-haiku-4-5` model (cheapest)

**Commands:** `ai`, `ai claude`

---

### Plausible Analytics ($9/mo or self-hosted)

**What you get:** Privacy-first web analytics. Critically, Plausible can filter traffic by source — letting you see exactly how many visitors come from `chatgpt.com`, `perplexity.ai`, and `claude.ai`.

**Setup:**
1. Add your site to [Plausible](https://plausible.io) (or self-host)
2. Create API key in Settings → API keys

**Commands:** `traffic`

---

### Bing Webmaster Tools (Free)

**What you get:** Bing-specific query stats, URL submission with daily quotas, sitemap management.

**Setup:**
1. Verify your site at [Bing Webmaster Tools](https://www.bing.com/webmasters)
2. Get API key from Settings → API Access

**Commands:** `bing`

---

### IndexNow (Free)

**What you get:** Instant notification to Bing and Yandex when your pages change. No waiting for crawlers.

**Setup:**
1. Generate any key string (e.g., `mysitekey2026`)
2. Host a text file at `https://yoursite.com/mysitekey2026.txt` containing the key
3. Set the key in config

**Commands:** `indexnow`

---

## Snapshots & Tracking

searchstack saves JSON snapshots after each run:

```
~/.searchstack/snapshots/
├── ai_citations_20260401_1200.json      # AEO citation results
├── geo_monitor_20260401_1200.json       # GEO AI Overview results
├── positions_latest.json                # latest keyword positions (for tracking)
├── positions_20260401_1200.json         # timestamped position snapshot
└── report_20260401.md                   # generated report
```

Use `searchstack track` to compare current positions with the previous snapshot and see which keywords improved or declined.

---

## Report Output

`searchstack report` generates a Markdown file with up to 14 sections:

1. **Executive Summary** — top-line metrics (visitors, AI citations, backlinks, gaps)
2. **Traffic** — Plausible 30-day overview (sources, countries, devices, AI referrals)
3. **Search Queries** — GSC top queries with clicks, impressions, CTR, position
4. **GEO Visibility** — Google AI Overview citation status + top cited domains
5. **AEO Status** — ChatGPT/Perplexity/Claude citation rates
6. **Google Positions** — ranked keywords with volume
7. **Competitor Traffic** — bulk traffic estimation comparison
8. **Indexing Status** — how many sitemap URLs are indexed
9. **Backlinks** — total backlinks, referring domains, domain rank
10. **Keyword Gaps** — high-volume keywords outside top-10
11. **Position Changes** — improved vs declined since last report
12. **Meta Issues** — pages with title/description problems
13. **Orphan Pages** — pages with no internal links
14. **Recommendations** — auto-generated action items

---

## Architecture

```
searchstack/
├── src/searchstack/
│   ├── cli.py              # entry point, argument parsing
│   ├── config.py           # .searchstack.toml + env var loading
│   ├── providers/          # API clients (stateless, reusable)
│   │   ├── gsc.py          # Google Search Console
│   │   ├── dataforseo.py   # DataForSEO
│   │   ├── plausible.py    # Plausible Analytics
│   │   ├── bing.py         # Bing Webmaster
│   │   ├── openai.py       # OpenAI (ChatGPT)
│   │   ├── perplexity.py   # Perplexity
│   │   └── anthropic.py    # Anthropic (Claude)
│   ├── commands/           # one file per CLI command
│   │   ├── traffic.py
│   │   ├── ai.py
│   │   ├── geo.py
│   │   ├── gsc.py
│   │   ├── keywords.py
│   │   ├── serp.py
│   │   ├── competitors.py
│   │   ├── gaps.py
│   │   ├── backlinks.py
│   │   ├── meta.py
│   │   ├── schema.py
│   │   ├── links.py
│   │   ├── onpage.py
│   │   ├── pages.py
│   │   ├── track.py
│   │   ├── indexnow.py
│   │   ├── bing.py
│   │   └── report.py
│   └── snapshots.py        # save/load/compare JSON snapshots
├── pyproject.toml
├── README.md
└── LICENSE
```

**Dependencies (minimal):**
```
google-auth
google-auth-oauthlib
google-api-python-client
requests
tomli (Python < 3.11)
```

No heavy frameworks. No click/typer/rich. Pure argparse + stdlib where possible.

---

## Examples

### Quick health check (free, no API keys needed)

```bash
# Check meta tags and JSON-LD on all your pages
searchstack meta
searchstack schema

# Check internal linking and find orphan pages
searchstack links

# Detailed on-page score for a specific URL
searchstack onpage https://example.com/pricing
```

### Weekly AEO/GEO monitoring (~$0.20)

```bash
# Are AI chatbots citing you?
searchstack ai

# Is Google AI Overview citing you?
searchstack geo

# How did positions change since last week?
searchstack track
```

### Monthly full report (~$1-2)

```bash
searchstack report
# → saves report to ~/.searchstack/snapshots/report_20260401.md
```

### Competitor research

```bash
# Compare traffic: you vs competitors
searchstack bulk competitor1.com competitor2.com yoursite.com

# Check who ranks for a specific query
searchstack serp "best project management tool 2026"

# Find keywords you should target but don't rank for
searchstack gaps
```

---

## Roadmap

- [ ] `searchstack init` — interactive setup wizard
- [ ] `searchstack cron` — scheduled checks via system cron
- [ ] `searchstack diff` — visual diff between two report snapshots
- [ ] `searchstack dashboard` — local web dashboard (single HTML file)
- [ ] Reddit / HackerNews / Twitter mention tracking
- [ ] YouTube search visibility
- [ ] Schema.org auto-fix suggestions
- [ ] llms.txt / llms-full.txt generation and validation
- [ ] CI/CD integration (GitHub Actions for scheduled monitoring)

---

## Contributing

PRs welcome. See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

---

## License

MIT. See [LICENSE](LICENSE).

---

Built by [Alex Pospekhov](https://github.com/alexpospekhov)
