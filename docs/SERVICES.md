# Services Setup Guide

Step-by-step instructions for connecting every external service that searchstack uses.

**Time to complete:** ~30 minutes for all services.

---

## Quick Reference

| # | Service | Required? | Cost | Config key | Env variable | Commands it unlocks |
|---|---------|-----------|------|------------|-------------|-------------------|
| 1 | [Google Search Console](#1-google-search-console) | **Yes** | Free | `[gsc]` | — | `gsc`, `pages`, `report` |
| 2 | [DataForSEO](#2-dataforseo) | **Yes** | $50 prepaid | `[dataforseo]` | `DATAFORSEO_LOGIN`, `DATAFORSEO_PASSWORD` | `geo`, `keywords`, `competitors`, `gaps`, `serp`, `track`, `bulk`, `backlinks` |
| 3 | [OpenAI](#3-openai-chatgpt) | For AEO | ~$0.001/query | `[openai]` | `OPENAI_API_KEY` | `ai`, `ai chatgpt` |
| 4 | [Perplexity](#4-perplexity) | For AEO | ~$0.005/query | `[perplexity]` | `PERPLEXITY_API_KEY` | `ai`, `ai perplexity` |
| 5 | [Anthropic](#5-anthropic-claude) | For AEO | ~$0.001/query | `[anthropic]` | `ANTHROPIC_API_KEY` | `ai`, `ai claude` |
| 6 | [Plausible](#6-plausible-analytics) | Optional | $9/mo or self-hosted | `[plausible]` | `PLAUSIBLE_API_KEY` | `traffic` |
| 7 | [Bing Webmaster](#7-bing-webmaster-tools) | Recommended | Free | `[bing]` | `BING_WEBMASTER_API_KEY` | `bing` |
| 8 | [IndexNow](#8-indexnow) | Recommended | Free | `[indexnow]` | — | `indexnow` |

Every key goes into **one of two places:**

```
Option A: Config file (.searchstack.toml)     Option B: Environment variable
─────────────────────────────────────────     ─────────────────────────────
[openai]                                      export OPENAI_API_KEY="sk-..."
api_key = "sk-..."
```

Environment variables always override the config file.

---

## 1. Google Search Console

**What it gives you:** Your actual Google rankings — queries, clicks, impressions, CTR, average position. URL indexing status. Sitemap health.

**Cost:** Free, unlimited.

### Step 1: Verify your site in Google Search Console

1. Go to **[search.google.com/search-console](https://search.google.com/search-console)**
2. Click **"Add property"**
3. Choose **"Domain"** (recommended) → enter `example.com`
4. Verify via DNS TXT record (Google gives you the exact record to add)
5. Wait for verification (usually instant, sometimes up to 24h)

> **Why "Domain" property?** It covers all subdomains (www, blog, app) and both http/https. The alternative "URL prefix" only covers one specific prefix.

### Step 2: Enable APIs in Google Cloud

1. Go to **[console.cloud.google.com](https://console.cloud.google.com)**
2. Create a project (or use existing) — note the **project ID**
3. Go to **APIs & Services → Library**
4. Search and enable these two APIs:
   - **Google Search Console API** (also called "Search Console API")
   - **Indexing API** (for URL inspection)

### Step 3: Create OAuth credentials

1. Go to **APIs & Services → Credentials**
2. Click **"+ Create Credentials" → "OAuth client ID"**
3. If prompted, configure the OAuth consent screen:
   - User type: **External** (or Internal if using Google Workspace)
   - App name: anything (e.g., "searchstack")
   - Scopes: add `webmasters.readonly`, `webmasters`, `indexing`
4. Back in Credentials, create OAuth client ID:
   - Application type: **Desktop app**
   - Name: anything
5. Click **"Download JSON"**
6. Save the file as `credentials.json`

### Step 4: Configure searchstack

```toml
# .searchstack.toml

[gsc]
credentials_file = "/path/to/credentials.json"
site_url = "sc-domain:example.com"
gcp_project = "your-gcp-project-id"    # optional, for quota attribution
```

### Step 5: First run (OAuth flow)

```bash
searchstack gsc
```

This opens your browser. Sign in with the Google account that has Search Console access. Grant permissions. A `token.pickle` file is saved automatically — future runs won't require browser login.

**OAuth scopes requested:**
- `https://www.googleapis.com/auth/webmasters.readonly` — read rankings
- `https://www.googleapis.com/auth/webmasters` — resubmit sitemaps
- `https://www.googleapis.com/auth/indexing` — URL inspection

### Troubleshooting

| Problem | Fix |
|---------|-----|
| "Access blocked: app not verified" | Add your Google account as a test user in the OAuth consent screen |
| "403 Forbidden" | Make sure the Google account has access to the Search Console property |
| "token.pickle expired" | Delete `token.pickle` and run again — it will re-authenticate |
| "Quota exceeded" | Set `gcp_project` in config so requests are attributed to your project |

---

## 2. DataForSEO

**What it gives you:** Keyword volumes, live SERP results, Google AI Overview data, backlink profiles, competitor traffic estimates. The only API that provides programmatic access to AI Overview content.

**Cost:** Pay-as-you-go, $50 minimum deposit. A typical month of monitoring costs $2-5.

### Step 1: Create account

1. Go to **[app.dataforseo.com/register](https://app.dataforseo.com/register)**
2. Sign up with email
3. Verify email

### Step 2: Add balance

1. Go to **Dashboard → Balance**
2. Add $50 (minimum deposit)
3. This is prepaid — no recurring subscription. $50 lasts months of normal usage.

### Step 3: Get API credentials

1. Go to **Dashboard → API Access**
2. Note your **login** (your email) and **API password** (NOT your account password)

> **Important:** The API password is separate from your login password. It's shown in the Dashboard → API Access section.

### Step 4: Configure searchstack

```toml
# .searchstack.toml

[dataforseo]
login = "your-email@example.com"
password = "your-api-password"
location_code = 2840          # 2840 = United States
language_code = "en"
```

Or via environment variables:

```bash
export DATAFORSEO_LOGIN="your-email@example.com"
export DATAFORSEO_PASSWORD="your-api-password"
```

### Cost per command

| Command | API endpoint | Cost per call |
|---------|-------------|---------------|
| `geo` (per keyword) | SERP Google Organic Live Advanced | ~$0.008 |
| `keywords` | Keyword Suggestions Live | ~$0.05 |
| `competitors` | Ranked Keywords Live | ~$0.02 |
| `gaps` | Ranked Keywords Live | ~$0.02 |
| `serp` | SERP Google Organic Live Advanced | ~$0.008 |
| `track` | Ranked Keywords Live | ~$0.02 |
| `bulk` | Bulk Traffic Estimation Live | ~$0.01 |
| `backlinks` | Backlinks Summary + Referring Domains | ~$0.04 |

### Location codes (common)

| Country | Code |
|---------|------|
| United States | 2840 |
| United Kingdom | 2826 |
| Canada | 2124 |
| Australia | 2036 |
| Germany | 2276 |
| France | 2250 |
| India | 2356 |

Full list: [dataforseo.com/apis/google-locations](https://docs.dataforseo.com/v3/serp/google/locations/)

---

## 3. OpenAI (ChatGPT)

**What it gives you:** Ask ChatGPT your target questions and detect if it mentions your domain in the response. Tests whether ChatGPT "knows" your brand from its training data.

**Cost:** ~$0.001 per query (GPT-4o-mini). Checking 8 queries costs less than $0.01.

### Step 1: Get API key

1. Go to **[platform.openai.com/api-keys](https://platform.openai.com/api-keys)**
2. Sign in (or create account)
3. Click **"+ Create new secret key"**
4. Name it (e.g., "searchstack")
5. Copy the key (starts with `sk-`)

> **Note:** You need to add payment method and have credits. New accounts get $5 free credits.

### Step 2: Configure searchstack

```toml
# .searchstack.toml

[openai]
api_key = "sk-..."
```

Or:

```bash
export OPENAI_API_KEY="sk-..."
```

### What searchstack does with it

- Sends each query from `[ai_queries]` to GPT-4o-mini
- Checks if the response text contains your domain name
- Saves results to snapshot for historical tracking

> **Important:** The API does NOT have web browsing. Responses come from training data only. This tests whether ChatGPT "knows" your brand — not whether ChatGPT Search would show your site (that depends on Bing rankings).

---

## 4. Perplexity

**What it gives you:** The most reliable AI citation data. Perplexity always searches the web before answering and returns explicit source URLs in the API response.

**Cost:** ~$0.005 per query (Sonar model). Checking 8 queries costs ~$0.04.

### Step 1: Get API key

1. Go to **[perplexity.ai/settings/api](https://www.perplexity.ai/settings/api)**
2. Sign in (or create account)
3. Add payment method (Settings → API → Billing)
4. Generate API key (starts with `pplx-`)

### Step 2: Configure searchstack

```toml
# .searchstack.toml

[perplexity]
api_key = "pplx-..."
```

Or:

```bash
export PERPLEXITY_API_KEY="pplx-..."
```

### What searchstack does with it

- Sends each query to Perplexity's Sonar model
- Checks the `citations` array in the response for your domain
- Also checks the response text for domain mentions
- Perplexity is the **most reliable** for citation detection because it returns structured citation URLs

---

## 5. Anthropic (Claude)

**What it gives you:** Tests whether Claude mentions your product when asked relevant questions. Like OpenAI, the API uses training data only (no web browsing).

**Cost:** ~$0.001 per query (Haiku model). Checking 8 queries costs less than $0.01.

### Step 1: Get API key

1. Go to **[console.anthropic.com/settings/keys](https://console.anthropic.com/settings/keys)**
2. Sign in (or create account)
3. Click **"Create Key"**
4. Copy the key (starts with `sk-ant-`)

> **Note:** Add payment method in Settings → Billing. New accounts get $5 free credits.

### Step 2: Configure searchstack

```toml
# .searchstack.toml

[anthropic]
api_key = "sk-ant-..."
```

Or:

```bash
export ANTHROPIC_API_KEY="sk-ant-..."
```

### What searchstack does with it

- Sends each query to Claude Haiku (cheapest model)
- Checks if the response text contains your domain name
- Claude rarely cites specific URLs — it's more useful for testing brand recognition

---

## 6. Plausible Analytics

**What it gives you:** Privacy-first web analytics. The killer feature for searchstack: filter traffic by source to see exactly how many visitors come from `chatgpt.com`, `perplexity.ai`, and `claude.ai`.

**Cost:** $9/mo (cloud) or free (self-hosted).

### Step 1: Add your site

1. Go to **[plausible.io](https://plausible.io)** and sign up (30-day free trial)
2. Add your domain
3. Add the Plausible script to your site:
   ```html
   <script defer data-domain="example.com" src="https://plausible.io/js/script.js"></script>
   ```

### Step 2: Create API key

1. Go to **Settings → API Keys** (in your Plausible dashboard)
2. Click **"+ New API Key"**
3. Name it (e.g., "searchstack")
4. Copy the key

### Step 3: Configure searchstack

```toml
# .searchstack.toml

[plausible]
api_key = "your-plausible-api-key"
site_id = "example.com"
```

Or:

```bash
export PLAUSIBLE_API_KEY="your-plausible-api-key"
```

### Self-hosting alternative

If you self-host Plausible, change the API base URL (coming in a future searchstack release). For now, self-hosted users can modify the `PLAUSIBLE_BASE` constant in the config.

---

## 7. Bing Webmaster Tools

**What it gives you:** Bing-specific query stats, URL submission with daily quotas, sitemap management. **Critical for AI visibility** because ChatGPT Search, Perplexity, and Copilot all use Bing as their search backend.

**Cost:** Free, unlimited.

### Step 1: Verify your site

1. Go to **[bing.com/webmasters](https://www.bing.com/webmasters)**
2. Sign in with Microsoft account
3. Add your site URL
4. Verify ownership:
   - **Option A (fastest):** Import from Google Search Console (if already verified there)
   - **Option B:** DNS CNAME record
   - **Option C:** Meta tag on homepage

### Step 2: Submit sitemap

1. In Bing Webmaster dashboard, go to **Sitemaps**
2. Submit `https://example.com/sitemap.xml`

Or use searchstack:
```bash
searchstack bing sitemap
```

### Step 3: Get API key

1. In Bing Webmaster dashboard, click the **gear icon** (Settings)
2. Go to **API Access**
3. Click **"API Key"** → generate or copy existing key

### Step 4: Configure searchstack

```toml
# .searchstack.toml

[bing]
api_key = "your-bing-webmaster-api-key"
```

Or:

```bash
export BING_WEBMASTER_API_KEY="your-bing-webmaster-api-key"
```

### Why Bing matters for AI search

```
Bing index → ChatGPT Search
Bing index → Perplexity (partially)
Bing index → Microsoft Copilot

If you're not in Bing, you're invisible to 3 major AI search products.
```

---

## 8. IndexNow

**What it gives you:** Instant notification to Bing and Yandex when your pages change. Instead of waiting for crawlers to discover your updates (hours to days), IndexNow tells them immediately.

**Cost:** Free, unlimited.

### Step 1: Generate a key

Pick any string as your key. Example: `searchstack2026`

### Step 2: Host the key file on your site

Create a text file at `https://example.com/searchstack2026.txt` containing just the key:

```
searchstack2026
```

This file proves you own the domain.

### Step 3: Configure searchstack

```toml
# .searchstack.toml

[indexnow]
key = "searchstack2026"
```

### How it works

When you run `searchstack indexnow`:
1. Fetches all URLs from your sitemap
2. Sends them to `api.indexnow.org` (Bing + partners)
3. Sends them to `yandex.com/indexnow` (Yandex)

Both Bing and Yandex process the notification within minutes.

> **Tip:** Run `searchstack indexnow` every time you publish or update content. It's free and speeds up AI search indexing significantly.

---

## Full Config File Template

Copy this to `.searchstack.toml` in your project root and fill in your keys:

```toml
# ╔══════════════════════════════════════════════════════════════╗
# ║  searchstack configuration                                   ║
# ║  Docs: docs/SERVICES.md                                      ║
# ╚══════════════════════════════════════════════════════════════╝

# Your website
domain = "example.com"
sitemap = "https://example.com/sitemap.xml"

# ── 1. Google Search Console (FREE) ───────────────────────────
[gsc]
credentials_file = "credentials.json"     # OAuth JSON from GCP Console
site_url = "sc-domain:example.com"        # "sc-domain:" for Domain property
gcp_project = ""                          # GCP project ID (optional)

# ── 2. DataForSEO ($50 prepaid) ───────────────────────────────
[dataforseo]
login = ""                                # your email
password = ""                             # API password (not account password!)
location_code = 2840                      # 2840 = US, 2826 = UK, 2124 = CA
language_code = "en"

# ── 3. OpenAI — ChatGPT AEO check (~$0.001/query) ────────────
[openai]
api_key = ""                              # sk-...

# ── 4. Perplexity — AEO check (~$0.005/query) ────────────────
[perplexity]
api_key = ""                              # pplx-...

# ── 5. Anthropic — Claude AEO check (~$0.001/query) ──────────
[anthropic]
api_key = ""                              # sk-ant-...

# ── 6. Plausible Analytics ($9/mo or self-hosted) ─────────────
[plausible]
api_key = ""
site_id = "example.com"

# ── 7. Bing Webmaster Tools (FREE) ───────────────────────────
[bing]
api_key = ""

# ── 8. IndexNow (FREE) ───────────────────────────────────────
[indexnow]
key = ""                                  # must match file at domain/{key}.txt

# ── AEO: Questions to ask AI chatbots ────────────────────────
[ai_queries]
queries = [
    "What is the best tool for [your niche]?",
    "How to solve [your customer's problem]?",
    "Top [your category] software in 2026",
    "[Your product category] comparison",
    "How much does [your topic] cost?",
]

# ── GEO: Keywords to monitor in Google AI Overview ───────────
[geo_keywords]
main = [
    "your main keyword 2026",
    "your product category",
]
features = [
    "how to [thing your product does]",
    "[feature] calculator",
]
comparison = [
    "best [category] tool",
    "[competitor] alternative",
]

# ── Competitors for bulk traffic comparison ──────────────────
[competitors]
domains = [
    "competitor1.com",
    "competitor2.com",
    "competitor3.com",
]

# ── Report output ────────────────────────────────────────────
[report]
output_dir = "./reports"                  # where to save MD reports
```

---

## Environment Variables Reference

All keys can be set as environment variables instead of (or in addition to) the config file.

```bash
# DataForSEO
export DATAFORSEO_LOGIN="your-email@example.com"
export DATAFORSEO_PASSWORD="your-api-password"

# AEO providers
export OPENAI_API_KEY="sk-..."
export PERPLEXITY_API_KEY="pplx-..."
export ANTHROPIC_API_KEY="sk-ant-..."

# Analytics & webmaster
export PLAUSIBLE_API_KEY="your-key"
export BING_WEBMASTER_API_KEY="your-key"
```

> **Priority:** Environment variable → config file value. If both are set, the env var wins.

> **Security:** Never commit API keys to git. Add `.searchstack.toml` to your `.gitignore`.

---

## Verification Checklist

After setting up all services, run these commands to verify everything works:

```bash
# Test Google Search Console
searchstack gsc
# Expected: table of your top queries with clicks/impressions

# Test DataForSEO
searchstack serp "your main keyword"
# Expected: live SERP top-10 results

# Test AEO (all three)
searchstack ai
# Expected: citation check results for ChatGPT, Perplexity, Claude

# Test GEO
searchstack geo "your main keyword"
# Expected: AI Overview status + organic position

# Test Plausible
searchstack traffic
# Expected: visitor count, sources, top pages

# Test Bing
searchstack bing
# Expected: daily/monthly quota, query stats

# Test IndexNow
searchstack indexnow
# Expected: submission status for Bing + Yandex

# Full report (tests everything at once)
searchstack report
# Expected: 14-section Markdown report saved to disk
```

If any command shows "No API key" or similar error, check the corresponding section above.
