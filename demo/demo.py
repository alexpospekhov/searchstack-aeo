#!/usr/bin/env python3
"""Searchstack CLI demo — simulates realistic output for recording."""
import sys
import time

# Colors
G = "\033[32m"  # green
R = "\033[31m"  # red
B = "\033[1m"   # bold
Y = "\033[33m"  # yellow
C = "\033[36m"  # cyan
D = "\033[2m"   # dim
N = "\033[0m"   # reset

def p(text="", delay=0.02):
    print(text)
    time.sleep(delay)

def section(title):
    p()
    p(f"{B}{title}{N}")
    p("=" * 60)

def demo_ai():
    section("$ searchstack ai")
    p()
    p(f"  Checking AI citations for {B}acme.io{N}...")
    p()
    p(f"  {B}ChatGPT{N} (gpt-4o-mini):")
    time.sleep(0.3)
    p(f'    "Best project management tool 2026?"    {G}✅ CITED{N}')
    p(f'    "How to track team productivity?"        {R}❌ not cited{N}')
    p(f'    "Top SaaS tools for startups"            {G}✅ CITED{N}')
    p(f'    "Project management software comparison" {G}✅ CITED{N}')
    p(f'    "How to run agile sprints?"              {R}❌ not cited{N}')
    p()
    p(f"  {B}Perplexity{N} (sonar):")
    time.sleep(0.3)
    p(f'    "Best project management tool 2026?"    {G}✅ CITED{N}  → https://acme.io/features')
    p(f'    "How to track team productivity?"        {G}✅ CITED{N}  → https://acme.io/blog/productivity')
    p(f'    "Top SaaS tools for startups"            {G}✅ CITED{N}  → https://acme.io/')
    p(f'    "Project management software comparison" {R}❌ not cited{N}')
    p(f'    "How to run agile sprints?"              {G}✅ CITED{N}  → https://acme.io/blog/agile')
    p()
    p(f"  {B}Claude{N} (haiku):")
    time.sleep(0.3)
    p(f'    "Best project management tool 2026?"    {R}❌ not cited{N}')
    p(f'    "How to track team productivity?"        {R}❌ not cited{N}')
    p(f'    "Top SaaS tools for startups"            {R}❌ not cited{N}')
    p(f'    "Project management software comparison" {R}❌ not cited{N}')
    p(f'    "How to run agile sprints?"              {R}❌ not cited{N}')
    p()
    p(f"  {B}Summary:{N} ChatGPT {G}3/5{N} | Perplexity {G}4/5{N} | Claude {R}0/5{N}")
    p(f"  {D}Saved: ~/.searchstack/snapshots/ai_citations_20260401_0900.json{N}")

def demo_geo():
    section("$ searchstack geo")
    p()
    p(f"  Checking Google AI Overview for {B}12 keywords{N}...")
    p()
    p(f"  {B}GROUP: main{N}")
    time.sleep(0.2)
    p(f'  [1/12] "best project management tool 2026"')
    p(f'    🤖 AI Overview | {R}❌ not cited{N} | Organic: pos 7')
    p(f'      → monday.com')
    p(f'      → asana.com')
    p(f'      → notion.so')
    time.sleep(0.2)
    p(f'  [2/12] "project management software for startups"')
    p(f'    🤖 AI Overview | {G}✅ CITED!{N} | Organic: pos 4')
    p(f'      → acme.io {G}← YOU{N}')
    p(f'      → clickup.com')
    time.sleep(0.2)
    p(f'  [3/12] "team productivity tracker"')
    p(f'    🤖 AI Overview | {R}❌ not cited{N} | Organic: not in top 10')
    p(f'      → toggl.com')
    p(f'      → clockify.com')
    time.sleep(0.2)
    p(f"  {D}... (9 more keywords){N}")
    p()
    p(f"  {B}SUMMARY{N}")
    p(f"  Keywords checked:     12")
    p(f"  AI Overview present:  9/12")
    p(f"  AI cites us:          {G}1{N}/9")
    p(f"  Organic top-10:       5/12")
    p()
    p(f"  ⚠️  Top cited domains (instead of us):")
    p(f"    4x monday.com")
    p(f"    3x asana.com")
    p(f"    2x notion.so")
    p(f"  {D}Saved: ~/.searchstack/snapshots/geo_monitor_20260401_0900.json{N}")

def demo_gsc():
    section("$ searchstack gsc")
    p()
    p(f"  {B}{'Query':<45} {'Clicks':>6} {'Impr':>6} {'CTR':>7} {'Pos':>5}{N}")
    p(f"  {'='*75}")
    time.sleep(0.2)
    data = [
        ("project management tool", 142, 3840, 3.7, 6.2),
        ("acme project management", 89, 420, 21.2, 1.3),
        ("best pm software 2026", 67, 2150, 3.1, 8.4),
        ("team productivity tracker", 34, 1890, 1.8, 14.2),
        ("startup project management", 28, 960, 2.9, 7.1),
        ("agile sprint tool", 21, 780, 2.7, 9.8),
        ("free project management", 18, 4200, 0.4, 22.3),
        ("kanban board software", 15, 1100, 1.4, 11.5),
        ("project management comparison", 12, 650, 1.8, 8.9),
        ("acme vs monday", 9, 180, 5.0, 3.2),
    ]
    for q, clicks, impr, ctr, pos in data:
        p(f"  {q:<45} {clicks:>6} {impr:>6} {ctr:>6.1f}% {pos:>5.1f}")
        time.sleep(0.05)

def demo_track():
    section("$ searchstack track")
    p()
    p(f"  {B}{'Keyword':<40} {'Prev':>5} {'Now':>5} {'Δ':>5} {'Vol':>6}{N}")
    p(f"  {'='*65}")
    time.sleep(0.2)
    changes = [
        ("project management tool", 8, 6, "+2", 12100),
        ("best pm software 2026", 11, 8, "+3", 4400),
        ("acme project management", 1, 1, "  =", 480),
        ("startup project management", 9, 7, "+2", 1900),
        ("team productivity tracker", 14, 14, "  =", 3200),
        ("free project management", 24, 22, "+2", 8100),
        ("kanban board software", 10, 12, " -2", 2600),
        ("agile sprint tool", 12, 10, "+2", 1400),
    ]
    for kw, prev, now, delta, vol in changes:
        color = G if delta.strip().startswith("+") else R if delta.strip().startswith("-") else ""
        end = N if color else ""
        p(f"  {kw:<40} {prev:>5} {now:>5} {color}{delta:>5}{end} {vol:>6}")
        time.sleep(0.05)
    p()
    p(f"  ↑{G}5 improved{N} | ↓{R}1 declined{N} | ={D}2 unchanged{N} | Total: 8")
    p(f"  {D}Saved: snapshots/positions_20260401.json{N}")

def demo_meta():
    section("$ searchstack meta")
    p()
    p(f"  Checking 14 pages...\n")
    p(f"  {B}{'Page':<35} {'Title':>5} {'Desc':>5} {'Issues'}{N}")
    p(f"  {'='*70}")
    time.sleep(0.2)
    pages = [
        ("/", 52, 148, f"{G}✅{N}"),
        ("/features", 44, 155, f"{G}✅{N}"),
        ("/pricing", 28, 89, f"{Y}title too short | desc too short{N}"),
        ("/blog/productivity", 71, 162, f"{Y}title long (71){N}"),
        ("/blog/agile", 48, 142, f"{G}✅{N}"),
        ("/about", 38, 0, f"{R}no description{N}"),
        ("/docs", 55, 134, f"{G}✅{N}"),
        ("/changelog", 42, 95, f"{Y}desc too short{N}"),
    ]
    for page, tl, dl, issues in pages:
        p(f"  {page:<35} {tl:>5} {dl:>5} {issues}")
        time.sleep(0.05)
    p()
    p(f"  Total issues: {Y}4{N}")

def demo_report():
    section("$ searchstack report")
    p()
    p(f"  Collecting data...")
    time.sleep(0.3)
    p(f"  {D}├─ Plausible traffic...{N}        {G}✅{N}")
    time.sleep(0.2)
    p(f"  {D}├─ Google Search Console...{N}     {G}✅{N}")
    time.sleep(0.2)
    p(f"  {D}├─ GEO snapshot (latest)...{N}     {G}✅{N}")
    time.sleep(0.2)
    p(f"  {D}├─ AEO snapshot (latest)...{N}     {G}✅{N}")
    time.sleep(0.2)
    p(f"  {D}├─ DataForSEO positions...{N}      {G}✅{N}")
    time.sleep(0.2)
    p(f"  {D}├─ Backlinks...{N}                 {G}✅{N}")
    time.sleep(0.2)
    p(f"  {D}├─ Meta audit...{N}                {G}✅{N}")
    time.sleep(0.2)
    p(f"  {D}└─ Internal links...{N}            {G}✅{N}")
    p()
    p(f"  {B}Report generated: 14 sections{N}")
    p()
    p(f"  📄 {B}~/.searchstack/snapshots/report_20260401.md{N}")
    p(f"  {D}   5.2 KB | 287 lines | 14 sections{N}")
    p()
    p(f"  {B}Executive Summary:{N}")
    p(f"  ┌─────────────────────────────────────┐")
    p(f"  │ Visitors (30d)      {B}1,247{N}           │")
    p(f"  │ Google AI cites us  {R}0 times{N}         │")
    p(f"  │ AI chatbot cites    {G}ChatGPT 3/5{N}     │")
    p(f"  │ Backlinks           89 (23 domains)  │")
    p(f"  │ Keyword gaps        {Y}12 not in top-10{N} │")
    p(f"  │ Positions ↑5 / ↓1                    │")
    p(f"  │ Status: {Y}🟡 Growing{N}                  │")
    p(f"  └─────────────────────────────────────┘")

if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "all"

    if cmd == "ai":
        demo_ai()
    elif cmd == "geo":
        demo_geo()
    elif cmd == "gsc":
        demo_gsc()
    elif cmd == "track":
        demo_track()
    elif cmd == "meta":
        demo_meta()
    elif cmd == "report":
        demo_report()
    elif cmd == "all":
        demo_ai()
        time.sleep(0.5)
        demo_geo()
        time.sleep(0.5)
        demo_gsc()
        time.sleep(0.5)
        demo_track()
        time.sleep(0.5)
        demo_meta()
        time.sleep(0.5)
        demo_report()
    p()
