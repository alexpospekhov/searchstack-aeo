# The AEO/GEO Stack: How AI Search Actually Works (and How to Monitor It)

> This document explains the full landscape of AI-powered search, what AEO and GEO mean in practice, which models power which search engines, and the complete infrastructure you need to monitor your visibility across all of them.

---

## The Three Layers of Search in 2025-2026

Search is no longer one thing. There are now three distinct channels where users find information — and your site needs to be visible in all of them.

```
┌─────────────────────────────────────────────────────────────────┐
│                        USER QUERY                               │
│                  "best tool for X in 2026"                      │
└──────────┬──────────────────┬──────────────────┬────────────────┘
           │                  │                  │
           ▼                  ▼                  ▼
    ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐
    │     SEO      │  │     GEO      │  │       AEO        │
    │  Google SERP │  │  AI Overview │  │  AI Chat Search  │
    │  10 blue     │  │  (inside     │  │  (standalone     │
    │  links       │  │   Google)    │  │   AI products)   │
    └──────────────┘  └──────────────┘  └──────────────────┘
    │                 │                  │
    │ Traditional     │ Google's own     │ ChatGPT, Perplexity,
    │ organic         │ AI-generated     │ Claude, Gemini,
    │ rankings        │ answer box       │ Copilot, Grok —
    │                 │ with citations   │ each with its own
    │                 │                  │ model and retrieval
    └─────────────────┴──────────────────┘
```

### SEO (Search Engine Optimization)

The classic: optimize to rank in Google's organic results (the "10 blue links"). Still accounts for the majority of search traffic. Well understood, well tooled.

**You rank here by:** content quality, backlinks, technical health, domain authority.

### GEO (Generative Engine Optimization)

Google now shows an **AI Overview** box at the top of many search results. This is a Gemini-generated summary that answers the query directly — with citations to specific websites. If you're not cited in the AI Overview, the user may never scroll down to the organic results.

**You get cited here by:** having concise, factual, well-structured content that Google's Gemini model considers authoritative for the query. Citation-ready formatting (short paragraphs, specific numbers, clear definitions) matters more than traditional SEO signals.

### AEO (Answer Engine Optimization)

Users increasingly search by asking AI chatbots directly — ChatGPT, Perplexity, Claude, Gemini, Copilot. Each uses different models and retrieval mechanisms. Some cite sources, some don't. Some have web access, some rely on training data.

**You get mentioned here by:** being in the training data (long-term content strategy), being in web search results that the AI retrieves in real time, and having content that is structured for easy extraction (FAQ format, tables, clear definitions).

---

## Which Models Power Which Search Engines

This is the map of which AI models power which user-facing search products, and how each retrieves information.

### Google Search (AI Overviews)

| Component | Details |
|-----------|---------|
| **Model** | Gemini (Google's proprietary LLM family) |
| **Where it appears** | Top of Google search results page, labeled "AI Overview" |
| **Retrieval method** | Google's own search index. The AI Overview pulls from pages that Google has already crawled and indexed. No separate retrieval — it uses the same index as organic results. |
| **Citations** | Yes — shows clickable source links inline in the AI Overview box |
| **How to get cited** | Rank in Google's top results for the query AND have content that Gemini considers citation-worthy (specific facts, numbers, definitions) |
| **Market share** | ~90% of search globally |
| **API access** | No public API for AI Overview specifically. Must use DataForSEO SERP API with `load_async_ai_overview: true` to retrieve AI Overview content programmatically. |

### ChatGPT (OpenAI)

| Component | Details |
|-----------|---------|
| **Model** | GPT-4o, GPT-4o-mini (for searchstack we use mini — cheapest, sufficient for citation detection) |
| **Where it appears** | chat.openai.com, ChatGPT app, ChatGPT search |
| **Retrieval method** | **Dual:** (1) Training data — knowledge baked into the model from pre-training. (2) Web browsing — ChatGPT can search Bing in real time when the user query requires fresh information. ChatGPT Search uses Bing as its search backend. |
| **Citations** | Partial — ChatGPT Search shows source links. In regular chat mode, it may mention product names without URLs. |
| **How to get cited** | Be in the training data (publish authoritative content early) AND rank well in Bing (ChatGPT Search uses Bing, not Google). |
| **Search backend** | **Bing** (Microsoft partnership) |
| **Market share** | ~200M+ weekly active users (as of 2025) |
| **API access** | OpenAI Chat Completions API. No web browsing in API — responses are purely from training data. This is actually useful for AEO monitoring: it tells you if the model "knows" about your product from training. |

### Perplexity

| Component | Details |
|-----------|---------|
| **Model** | Multiple — uses its own "Sonar" models (fine-tuned for search), plus optionally GPT-4o, Claude for Pro users |
| **Where it appears** | perplexity.ai, Perplexity app |
| **Retrieval method** | **Always retrieves from the web.** Every query triggers real-time web search (their own index + Bing). Perplexity never answers from training data alone — it always grounds responses in retrieved sources. |
| **Citations** | **Yes — always.** Returns explicit citation URLs in the API response (`citations` array). Most reliable citation source among all AI search products. |
| **How to get cited** | Rank well in Bing AND Perplexity's own web index. Have content that clearly answers the query. |
| **Search backend** | **Bing + own index** |
| **Market share** | ~15M+ monthly active users, growing fast |
| **API access** | Perplexity Chat Completions API. Returns `citations` array with source URLs — the best structured data for citation monitoring. |

### Claude (Anthropic)

| Component | Details |
|-----------|---------|
| **Model** | Claude Opus, Sonnet, Haiku (for searchstack we use Haiku — cheapest) |
| **Where it appears** | claude.ai, Claude app |
| **Retrieval method** | **Training data only** (via API). Claude does not have web browsing in the API. On claude.ai, web search is available but not via the API. |
| **Citations** | Rarely — Claude typically mentions concepts and product categories but rarely provides specific URLs. |
| **How to get cited** | Be prominent enough in the training data. Publish authoritative content on high-traffic sites. Brand recognition matters more than SEO here. |
| **Search backend** | None (API), Web search on claude.ai |
| **Market share** | Growing, especially among developers and professionals |
| **API access** | Anthropic Messages API. Pure training data response — good for testing if Claude "knows" your brand. |

### Microsoft Copilot

| Component | Details |
|-----------|---------|
| **Model** | GPT-4o (Microsoft's OpenAI partnership) |
| **Where it appears** | Bing search, Windows Copilot, Edge sidebar, Microsoft 365 |
| **Retrieval method** | **Bing search results.** Copilot always retrieves from Bing before generating answers. |
| **Citations** | Yes — shows source links inline |
| **How to get cited** | Rank well in **Bing** specifically. Copilot pulls from Bing, not Google. |
| **Search backend** | **Bing** |
| **Market share** | Bundled with Windows, Edge, Office — large install base but lower active search usage |
| **API access** | No direct API for Copilot search. Monitor indirectly via Bing Webmaster Tools. |

### Google Gemini (standalone)

| Component | Details |
|-----------|---------|
| **Model** | Gemini Pro, Gemini Ultra |
| **Where it appears** | gemini.google.com, Gemini app, Google Workspace |
| **Retrieval method** | **Google Search.** When Gemini needs current information, it searches Google. |
| **Citations** | Yes — shows "Sources" with links |
| **How to get cited** | Rank in Google organic results. Same strategy as SEO + GEO. |
| **Search backend** | **Google** |
| **API access** | Vertex AI API (no search grounding in free tier). Monitor indirectly via Google Search Console. |

### Grok (xAI)

| Component | Details |
|-----------|---------|
| **Model** | Grok-3, Grok-3-mini (for searchstack we use grok-3-mini) |
| **Where it appears** | grok.com, X.com integration, xAI apps |
| **Retrieval method** | **Web search (real-time).** Grok always searches the web before answering. |
| **Citations** | Yes — shows source links |
| **How to get cited** | Rank in web search results. Grok uses its own web search. |
| **Search backend** | **Own web search** (not Bing, not Google) |
| **Market share** | Growing, integrated into X (Twitter) with 500M+ users |
| **API access** | xAI API (https://api.x.ai). Compatible with OpenAI format. |

---

## The Critical Role of Bing

Here is the fact most SEO practitioners miss:

> **Three out of six major AI search products use Bing as their search backend. One (Grok) uses its own.**

```
                    ┌──────────────┐
                    │     BING     │
                    │  Search Index│
                    └──────┬───────┘
                           │
              ┌────────────┼────────────────┐
              │            │                │
              ▼            ▼                ▼
        ┌──────────┐ ┌──────────┐   ┌────────────┐
        │ ChatGPT  │ │Perplexity│   │  Copilot   │
        │ Search   │ │          │   │ (Bing AI)  │
        └──────────┘ └──────────┘   └────────────┘

                    ┌──────────────┐
                    │    GOOGLE    │
                    │  Search Index│
                    └──────┬───────┘
                           │
              ┌────────────┼────────────────┐
              │            │                │
              ▼            ▼                ▼
        ┌──────────┐ ┌──────────┐   ┌────────────┐
        │  Google  │ │  Google  │   │   Gemini   │
        │  SERP    │ │AI Overview│  │(standalone)│
        └──────────┘ └──────────┘   └────────────┘

              ┌──────────────────┐
              │    xAI / GROK    │
              │  Own Search Index│
              └────────┬─────────┘
                       │
                       ▼
                 ┌──────────┐
                 │   Grok   │
                 │ (grok.com│
                 │  + X.com)│
                 └──────────┘
```

**This means:**
- If you only optimize for Google, you're invisible to ChatGPT, Perplexity, Copilot, and Grok
- Bing Webmaster Tools is not optional — it's how you monitor visibility for 3 AI search products
- Grok uses its own web search — you need to rank in general web results, not just Google or Bing
- IndexNow (instant Bing/Yandex notification) directly impacts how fast your content appears in AI search results
- Bing SEO signals (submit sitemap, submit URLs, verify site) are as important as Google signals for AI visibility

### What to do about Bing

1. **Verify your site** in Bing Webmaster Tools
2. **Submit your sitemap** to Bing
3. **Use IndexNow** to notify Bing immediately when you publish or update content
4. **Submit individual URLs** to Bing when you publish high-priority pages
5. **Monitor Bing query stats** — these are a proxy for ChatGPT/Perplexity/Copilot visibility

searchstack automates all of this:
```bash
searchstack bing sitemap    # submit sitemap to Bing
searchstack bing submit     # submit all URLs individually
searchstack bing            # check quota + query stats
searchstack indexnow        # notify Bing + Yandex instantly
```

---

## How AI Models Decide What to Cite

Each AI search product uses a different strategy for selecting which sources to cite. Understanding this is key to getting your site mentioned.

### 1. Training Data Citations (Claude, ChatGPT without browsing)

The model mentions your product because it appeared enough times in the training corpus (web crawl, Wikipedia, forums, documentation).

**What matters:**
- Domain authority and brand recognition
- Presence on high-traffic third-party sites (Reddit, HackerNews, industry blogs)
- Wikipedia mentions
- Documentation quality (LLMs love well-structured docs)
- Published before the training data cutoff

**What doesn't matter:** Your current Google ranking, your recent content updates.

**How to improve:** Create authoritative content that gets linked from many sources. Get mentioned in listicles, comparisons, reviews. Build genuine brand awareness.

### 2. Retrieved Citations (Perplexity, ChatGPT Search, Copilot, Gemini, Grok, Google AI Overview)

The model searches the web in real time, retrieves relevant pages, then generates an answer citing those pages.

**What matters:**
- Your ranking in the search index being used (Google or Bing)
- Content relevance to the exact query
- **Citation-ready formatting:**
  - Short, factual paragraphs (2-3 sentences)
  - Specific numbers and data points
  - Clear definitions (the model can easily extract a quote)
  - Tables and structured data
  - FAQ sections with concise answers
- Page freshness (recently updated content ranks better)
- JSON-LD structured data (helps models understand page content)

**What doesn't matter:** Pure domain authority without relevant content. Long-form "SEO content" that buries the answer in 3000 words.

### 3. The "Citation-Ready" Content Format

The content format that maximizes AI citations across all platforms:

```markdown
## What is [concept]?

[Concept] is [one-sentence definition with specific numbers].
[One sentence of context]. [One sentence with a specific fact or statistic].

### How [concept] works

1. **Step one** — [concise explanation]
2. **Step two** — [concise explanation]
3. **Step three** — [concise explanation]

### [Concept] costs and pricing

| Item | Cost | Notes |
|------|------|-------|
| ... | $X.XX | ... |

### FAQ

**Q: [Exact question users ask]?**
A: [Direct 1-2 sentence answer]. [Supporting detail].
```

This format works because:
- The definition paragraph is easy for models to extract as a citation
- Numbered steps match how AI models structure responses
- Tables provide specific data points that models love to cite
- FAQ format directly matches conversational AI queries

---

## llms.txt — Telling AI Models About Your Site

`llms.txt` is a proposed standard file — like `robots.txt`, but for AI models. Instead of telling crawlers what NOT to index, it tells AI models what your site IS about and how to understand it.

### The two files

- **`llms.txt`** — short version: site name, one-line description, and a list of your important pages with brief labels. Think of it as a table of contents for AI.
- **`llms-full.txt`** — detailed version: full page summaries, key facts, product descriptions. Everything an AI model needs to understand your site without crawling every page.

### Why it matters

AI models that search the web (Grok, Perplexity, ChatGPT Search) look for easy-to-parse information. `llms.txt` gives them a structured summary of your entire site in one file. This increases the chance they cite your pages accurately — with correct names, descriptions, and URLs.

### How searchstack helps

```bash
searchstack llms generate   # creates llms.txt and llms-full.txt from your sitemap
searchstack llms validate   # checks generated files against the llms.txt spec
```

The `generate` command crawls your sitemap, extracts titles, descriptions, and key content from each page, and produces both files. The `validate` command checks that the files conform to the [llms.txt specification](https://llmstxt.org/).

---

## The Complete Monitoring Stack

Here is every service and why it exists in the searchstack:

```
┌─────────────────────────────────────────────────────────────────────┐
│                        searchstack                                   │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  SEO LAYER (Traditional Google Rankings)                             │
│  ├── Google Search Console API ──── positions, clicks, indexing      │
│  ├── DataForSEO Labs API ────────── keywords, competitors, gaps      │
│  └── DataForSEO Backlinks API ───── backlink profile, referring      │
│                                     domains                          │
│                                                                      │
│  GEO LAYER (Google AI Overview)                                      │
│  └── DataForSEO SERP API ───────── AI Overview content + citations   │
│      (load_async_ai_overview)       for target keywords              │
│                                                                      │
│  AEO LAYER (AI Chat Search)                                          │
│  ├── OpenAI API ─────────────────── ChatGPT citation check           │
│  │   (gpt-4o-mini)                  (training data awareness)        │
│  ├── Perplexity API ─────────────── Perplexity citation check        │
│  │   (sonar)                        (real-time web + citations[])    │
│  ├── Anthropic API ──────────────── Claude citation check            │
│  │   (claude-haiku-4-5)             (training data awareness)        │
│  └── xAI API ────────────────────── Grok citation check             │
│      (grok-3-mini)                  (real-time web search)           │
│                                                                      │
│  BING LAYER (Powers ChatGPT Search + Perplexity + Copilot)          │
│  ├── Bing Webmaster API ─────────── query stats, URL submission      │
│  └── IndexNow API ───────────────── instant Bing + Yandex notify     │
│                                                                      │
│  TRAFFIC LAYER (Measure Real Impact)                                 │
│  └── Plausible API ──────────────── visitors, sources, AI referrals  │
│      (filter: chatgpt.com,          (chatgpt.com, perplexity.ai,     │
│       perplexity.ai, claude.ai)      claude.ai traffic breakdown)    │
│                                                                      │
│  TECHNICAL LAYER (Site Health)                                        │
│  ├── Sitemap crawler ────────────── meta tags, JSON-LD, links        │
│  └── GSC URL Inspection API ─────── per-URL indexing status          │
│                                                                      │
├─────────────────────────────────────────────────────────────────────┤
│  OUTPUT                                                              │
│  ├── Terminal (real-time results)                                     │
│  ├── JSON snapshots (historical tracking)                            │
│  └── Markdown reports (14-section monthly report)                    │
└─────────────────────────────────────────────────────────────────────┘
```

### Service dependency map

```
Command          Google  DataFor  OpenAI  Perplex  Anthropic  xAI    Plausible  Bing  IndexNow
                  GSC     SEO                                  Grok
───────────────────────────────────────────────────────────────────────────────────────────────
ai                                  ●        ●        ●        ●
ai chatgpt                          ●
ai perplexity                                ●
ai claude                                             ●
ai grok                                                        ●
geo                        ●
gsc               ●
keywords                   ●
competitors                ●
gaps                       ●
serp                       ●
track                      ●
bulk                       ●
backlinks                  ●
traffic                                                                  ●
bing                                                                            ●
indexnow                                                                                ●
pages             ●
meta              (sitemap fetch only)
schema            (sitemap fetch only)
links             (sitemap fetch only)
onpage            (single URL fetch only)
monitor           ●        ●
audit             ●        ●
llms              (no API needed — generates files from sitemap)
report            ●        ●        ●        ●        ●        ●       ●        ●
```

● = required for that command. Commands without marks use only sitemap/URL fetching (no API key needed).

---

## Monitoring Strategy: What to Run and When

### Daily (automated via cron)

| Check | Command | Cost | Why |
|-------|---------|------|-----|
| Position tracking | `searchstack track` | ~$0.02 | Catch ranking drops within 24h |

### Weekly

| Check | Command | Cost | Why |
|-------|---------|------|-----|
| AI citation check | `searchstack ai` | ~$0.05 | See if ChatGPT/Perplexity/Claude started (or stopped) mentioning you |
| GEO monitoring | `searchstack geo` | ~$0.18 | Track Google AI Overview citations for your keywords |
| Bing stats | `searchstack bing` | Free | Proxy for ChatGPT/Perplexity/Copilot visibility |

### Monthly

| Check | Command | Cost | Why |
|-------|---------|------|-----|
| Full report | `searchstack report` | ~$1-2 | Comprehensive snapshot — traffic, rankings, AI visibility, technical health |
| Competitor analysis | `searchstack bulk` | ~$0.01 | Track competitor traffic trends |
| Backlink check | `searchstack backlinks` | ~$0.04 | Monitor link building progress |
| Technical audit | `searchstack meta && searchstack schema && searchstack links` | Free | Catch broken meta, missing JSON-LD, orphan pages |

### After publishing new content

```bash
searchstack indexnow                          # notify Bing + Yandex immediately
searchstack bing submit                       # submit to Bing directly
searchstack gsc resubmit                      # resubmit sitemap to Google
searchstack gsc inspect https://site.com/new  # verify Google knows about it
```

### After updating llms.txt

```bash
searchstack llms validate  # check files against the llms.txt spec
searchstack llms generate  # regenerate if you added/removed pages
```

### After a Google algorithm update

```bash
searchstack track          # did positions change?
searchstack geo            # did AI Overview citations change?
searchstack monitor        # quick site health dashboard
searchstack gaps           # any new opportunities?
searchstack report         # full snapshot for comparison
```

### Periodic site health

```bash
searchstack monitor        # quick dashboard: GSC stats, indexing, top queries
searchstack audit          # full SEO analysis with keyword volumes and gaps
```

---

## Glossary

| Term | Definition |
|------|-----------|
| **SEO** | Search Engine Optimization — optimizing for traditional Google/Bing organic results |
| **AEO** | Answer Engine Optimization — optimizing for visibility in AI chatbots (ChatGPT, Perplexity, Claude, Grok) that answer user questions directly |
| **GEO** | Generative Engine Optimization — optimizing for Google's AI Overview box that appears above organic results |
| **AI Overview** | Google's AI-generated summary box at the top of search results (powered by Gemini) |
| **SERP** | Search Engine Results Page — what you see when you Google something |
| **GSC** | Google Search Console — Google's free tool for monitoring your site's search performance |
| **CTR** | Click-Through Rate — percentage of impressions that resulted in clicks |
| **IndexNow** | Protocol for instantly notifying search engines about content changes (supported by Bing, Yandex) |
| **DataForSEO** | Third-party API providing keyword data, SERP results, AI Overview content, and backlink data |
| **Plausible** | Privacy-first web analytics alternative to Google Analytics |
| **Citation** | When an AI model references or links to your website in its response |
| **AI Referral** | Web traffic from AI products — visitors who click through from ChatGPT, Perplexity, or Claude |
| **Sonar** | Perplexity's search-optimized model that always retrieves web sources before answering |
| **Training Data** | The corpus of web content that an AI model learned from during pre-training. Your site is in the training data if it was crawled before the cutoff date. |
| **Retrieval** | Real-time web search performed by an AI model to get current information before answering |
| **Citation-Ready Content** | Content formatted for easy extraction by AI — short paragraphs, specific facts, tables, FAQ format |
| **Orphan Page** | A page in your sitemap that no other page on your site links to — invisible to crawlers that follow links |
| **JSON-LD** | JavaScript Object Notation for Linked Data — structured data format used by Google to understand page content (Schema.org) |
| **Domain Rank** | DataForSEO's metric (0-1000) measuring a domain's authority based on backlink quality |
| **Grok** | xAI's AI model, integrated into X (Twitter). Uses its own web search (not Bing, not Google) to retrieve and cite sources |
| **llms.txt** | Proposed standard file (like robots.txt) that tells AI models what your site is about — short version (llms.txt) for page links, detailed version (llms-full.txt) for full summaries |
| **Monitor** | Site health dashboard command — quick overview of GSC stats, indexing status, and top queries |
| **Audit** | Full SEO analysis command — keyword volumes, ranking gaps, competitor comparison, and technical health check |

---

## Further Reading

- [Google AI Overview documentation](https://blog.google/products/search/generative-ai-google-search-may-2024/)
- [Perplexity publisher program](https://www.perplexity.ai/hub/blog/perplexity-publisher-program)
- [IndexNow protocol specification](https://www.indexnow.org/documentation)
- [DataForSEO API documentation](https://docs.dataforseo.com/)
- [llms.txt specification](https://llmstxt.org/)
- [Google Search Console API reference](https://developers.google.com/webmaster-tools/v1/api_reference_index)
- [xAI Grok API documentation](https://docs.x.ai/)
- [Bing Webmaster API reference](https://learn.microsoft.com/en-us/dotnet/api/microsoft.bing.webmaster.api)
