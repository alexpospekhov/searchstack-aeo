"""Competitor research workflow.

Creates a local research run with proposed monitoring keywords/prompts.
This command never changes presets, .searchstack.toml, or server runtime.
"""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from searchstack.config import Config
from searchstack.providers.dataforseo import (
    api_request,
    get_language_code,
    get_location_code,
)


HOME_SEARCHSTACK = Path.home() / ".searchstack"
RESEARCH_RUNS_DIR = HOME_SEARCHSTACK / "research" / "runs"
LOCAL_DB_PATH = HOME_SEARCHSTACK / "research" / "searchstack-local-db.json"
COMPETITORS_FULL = Path("competitors.json")
PRESETS_DIR = Path("presets")

COMMERCIAL_TERMS = {
    "software",
    "tool",
    "tools",
    "platform",
    "calculator",
    "alternative",
    "alternatives",
    "management",
    "automation",
    "fees",
    "profit",
    "analytics",
    "agency",
    "agencies",
}


def _check_configured(config: Config) -> bool:
    if not config.dataforseo.login or not config.dataforseo.password:
        print("DataForSEO not configured. Set [dataforseo] in .searchstack.toml")
        return False
    return True


def _normalize_domain(value: str) -> str:
    value = value.strip()
    if not value:
        return ""
    if "://" not in value:
        value = f"https://{value}"
    parsed = urlparse(value)
    host = parsed.netloc or parsed.path
    host = host.lower().strip().removeprefix("www.")
    return host.split("/")[0]


def _slug(value: str) -> str:
    value = _normalize_domain(value) or value.lower()
    return re.sub(r"[^a-z0-9]+", "-", value).strip("-") or "competitor"


def _load_json(path: Path) -> Any:
    if not path.is_file():
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _load_local_db() -> dict[str, Any]:
    data = _load_json(LOCAL_DB_PATH)
    if isinstance(data, dict):
        data.setdefault("schema_version", 1)
        data.setdefault("runs", [])
        data.setdefault("competitors", {})
        data.setdefault("candidates", {"keywords": [], "ai_prompts": []})
        return data
    return {
        "schema_version": 1,
        "updated_at": "",
        "runs": [],
        "competitors": {},
        "candidates": {"keywords": [], "ai_prompts": []},
    }


def _save_local_db(db: dict[str, Any]) -> None:
    LOCAL_DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    db["updated_at"] = datetime.now(timezone.utc).isoformat()
    with open(LOCAL_DB_PATH, "w", encoding="utf-8") as f:
        json.dump(db, f, indent=2, ensure_ascii=False)


def _find_competitor_profile(domain: str) -> dict[str, Any]:
    data = _load_json(COMPETITORS_FULL) or {}
    profile: dict[str, Any] = {
        "domain": domain,
        "known": False,
        "product_category": "",
        "seo_type": "",
        "notes": "",
        "appears_for": [],
    }

    product = data.get("product_competitors", {}).get("categories", {})
    for category, competitors in product.items():
        for item in competitors:
            item_url = str(item.get("url", "")).lower().removeprefix("www.")
            if item_url == domain:
                profile.update(
                    {
                        "known": True,
                        "product_category": category,
                        "name": item.get("name", domain),
                        "focus": item.get("focus", ""),
                        "pricing": item.get("pricing", ""),
                        "blog": item.get("blog"),
                    }
                )

    seo_domains = data.get("seo_competitors", {}).get("domains", [])
    for item in seo_domains:
        item_domain = str(item.get("domain", "")).lower().removeprefix("www.")
        if item_domain == domain:
            profile.update(
                {
                    "known": True,
                    "seo_type": item.get("type", ""),
                    "authority": item.get("authority", ""),
                    "notes": item.get("notes", ""),
                    "appears_for": item.get("appears_for", []),
                }
            )

    return profile


def _fetch_ranked_keywords(config: Config, domain: str, limit: int = 100) -> list[dict[str, Any]]:
    body = [
        {
            "target": domain,
            "location_code": get_location_code(config),
            "language_code": get_language_code(config),
            "limit": limit,
        }
    ]
    data = api_request(config, "dataforseo_labs/google/ranked_keywords/live", body)
    if "error" in data:
        return [{"error": data["error"]}]

    tasks = data.get("tasks", [])
    if not tasks or not tasks[0].get("result"):
        return []

    items = tasks[0]["result"][0].get("items", []) or []
    rows: list[dict[str, Any]] = []
    for item in items:
        kw_data = item.get("keyword_data", {}) or {}
        info = kw_data.get("keyword_info", {}) or {}
        ranked = item.get("ranked_serp_element", {}) or {}
        serp_item = ranked.get("serp_item", {}) or {}
        keyword = kw_data.get("keyword", "")
        if not keyword:
            continue
        rows.append(
            {
                "keyword": keyword,
                "volume": info.get("search_volume") or 0,
                "competition": info.get("competition"),
                "cpc": info.get("cpc") or 0,
                "position": serp_item.get("rank_absolute") or item.get("rank_absolute"),
                "url": serp_item.get("url", serp_item.get("relative_url", "")),
            }
        )
    rows.sort(key=lambda r: (-(r["volume"] or 0), r["position"] or 999))
    return rows


def _seed_keywords(config: Config, cluster: str) -> list[str]:
    seeds: list[str] = []
    cluster = cluster.strip().lower()
    if cluster and cluster != "all":
        for name, keywords in config.geo_keywords.items():
            normalized = name.replace("_", "-").lower()
            if cluster in {normalized, name.lower()}:
                seeds.extend(keywords)
        if not seeds:
            seeds.append(cluster)
    else:
        for keywords in config.geo_keywords.values():
            seeds.extend(keywords)
    return list(dict.fromkeys(seeds))[:12]


def _fetch_serp_overlap(config: Config, seeds: list[str], domain: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for keyword in seeds[:8]:
        body = [
            {
                "keyword": keyword,
                "location_code": get_location_code(config),
                "language_code": get_language_code(config),
                "depth": 10,
                "device": "desktop",
            }
        ]
        data = api_request(config, "serp/google/organic/live/advanced", body)
        if "error" in data:
            rows.append({"keyword": keyword, "error": data["error"]})
            continue
        tasks = data.get("tasks", [])
        result = tasks[0].get("result", [{}])[0] if tasks and tasks[0].get("result") else {}
        items = result.get("items", []) or []
        organic = [item for item in items if item.get("type") == "organic"][:10]
        domains = [str(item.get("domain", "")).lower().removeprefix("www.") for item in organic]
        rows.append(
            {
                "keyword": keyword,
                "competitor_in_top10": domain in domains,
                "competitor_position": (domains.index(domain) + 1) if domain in domains else None,
                "top_domains": domains,
            }
        )
    return rows


def _current_keywords(config: Config) -> set[str]:
    current: set[str] = set()
    for keywords in config.geo_keywords.values():
        current.update(k.lower() for k in keywords)
    return current


def _score_keyword(row: dict[str, Any], current: set[str], profile: dict[str, Any]) -> tuple[int, list[str], str]:
    keyword = str(row.get("keyword", "")).lower()
    volume = int(row.get("volume") or 0)
    position = int(row.get("position") or 999)

    score = 0
    reasons: list[str] = []

    if keyword in current:
        score -= 40
        reasons.append("already monitored")
    if volume >= 1000:
        score += 25
        reasons.append("high volume")
    elif volume >= 100:
        score += 18
        reasons.append("meaningful volume")
    elif volume >= 10:
        score += 8
        reasons.append("some volume")

    if position <= 3:
        score += 20
        reasons.append("competitor ranks top 3")
    elif position <= 10:
        score += 14
        reasons.append("competitor ranks top 10")
    elif position <= 20:
        score += 7
        reasons.append("competitor ranks top 20")

    if any(term in keyword for term in COMMERCIAL_TERMS):
        score += 18
        reasons.append("commercial/product intent")

    appears_for = " ".join(str(v).lower() for v in profile.get("appears_for", []))
    if keyword and any(part in appears_for for part in keyword.split()[:3]):
        score += 8
        reasons.append("matches known competitor SERP notes")

    if score >= 55:
        cadence = "daily_candidate"
    elif score >= 30:
        cadence = "weekly_candidate"
    elif score >= 15:
        cadence = "research_only"
    else:
        cadence = "reject"

    return score, reasons, cadence


def _candidate_keywords(
    ranked: list[dict[str, Any]],
    current: set[str],
    profile: dict[str, Any],
) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    for row in ranked:
        if "error" in row:
            continue
        score, reasons, cadence = _score_keyword(row, current, profile)
        if cadence == "reject":
            continue
        candidates.append(
            {
                "id": f"kw-{len(candidates) + 1:03d}",
                "keyword": row["keyword"],
                "score": score,
                "recommended_cadence": cadence,
                "status": "proposed",
                "reason": "; ".join(reasons),
                "volume": row.get("volume", 0),
                "competitor_position": row.get("position"),
                "competitor_url": row.get("url", ""),
            }
        )
    candidates.sort(key=lambda r: r["score"], reverse=True)
    return candidates[:25]


def _candidate_prompts(domain: str, profile: dict[str, Any], keywords: list[dict[str, Any]]) -> list[dict[str, Any]]:
    prompts: list[dict[str, Any]] = []
    display = profile.get("name") or domain

    def add(prompt: str, reason: str, score: int, cadence: str) -> None:
        prompts.append(
            {
                "id": f"prompt-{len(prompts) + 1:03d}",
                "prompt": prompt,
                "score": score,
                "recommended_cadence": cadence,
                "status": "proposed",
                "reason": reason,
            }
        )

    if profile.get("known"):
        add(
            f"What is the best {display} alternative?",
            "competitor-capture AEO test",
            72,
            "weekly_candidate",
        )

    top_keywords = [str(k["keyword"]).lower() for k in keywords[:8]]
    if any("calculator" in kw or "fee" in kw or "pricing" in kw for kw in top_keywords):
        add(
            f"What is the pricing and fee structure for {display}?",
            "pricing/calculator intent in competitor keywords",
            68,
            "weekly_candidate",
        )
    if any("analytics" in kw or "tool" in kw or "software" in kw for kw in top_keywords):
        add(
            f"What are the best software alternatives to {display}?",
            "tool/category intent in competitor keywords",
            64,
            "weekly_candidate",
        )

    return prompts


def _write_run(
    *,
    domain: str,
    cluster: str,
    profile: dict[str, Any],
    seeds: list[str],
    ranked: list[dict[str, Any]],
    serp_overlap: list[dict[str, Any]],
    keywords: list[dict[str, Any]],
    prompts: list[dict[str, Any]],
) -> Path:
    RESEARCH_RUNS_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    run_id = f"{ts}_{_slug(domain)}"
    run_dir = RESEARCH_RUNS_DIR / run_id
    run_dir.mkdir(parents=True, exist_ok=False)

    run = {
        "run_id": run_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "target": domain,
        "cluster": cluster or "all",
        "status": "proposed",
        "guard": "study only; no preset, .searchstack.toml, daily, or server runtime changes applied",
        "profile": profile,
        "seed_keywords": seeds,
        "ranked_keywords": ranked,
        "serp_overlap": serp_overlap,
        "keyword_candidates": keywords,
        "aeo_prompt_candidates": prompts,
        "next_operator_actions": [
            "review candidates",
            "accept subset into weekly/cluster preset",
            "promote to daily only with explicit approval",
        ],
    }

    with open(run_dir / "run.json", "w", encoding="utf-8") as f:
        json.dump(run, f, indent=2, ensure_ascii=False)
    with open(run_dir / "candidates.json", "w", encoding="utf-8") as f:
        json.dump({"keywords": keywords, "ai_prompts": prompts}, f, indent=2, ensure_ascii=False)

    summary = [
        f"# Competitor Research Run: {domain}",
        "",
        f"- Run ID: `{run_id}`",
        f"- Cluster: `{cluster or 'all'}`",
        "- Status: `proposed`",
        "- Guard: no runtime/server changes applied.",
        "",
        "## Profile",
        "",
        f"- Known competitor: {profile.get('known')}",
        f"- Product category: {profile.get('product_category') or '-'}",
        f"- SEO type: {profile.get('seo_type') or '-'}",
        f"- Focus: {profile.get('focus') or '-'}",
        f"- Notes: {profile.get('notes') or '-'}",
        "",
        "## Top Keyword Candidates",
        "",
    ]
    for item in keywords[:10]:
        summary.append(
            f"- `{item['keyword']}` score={item['score']} cadence={item['recommended_cadence']} "
            f"vol={item.get('volume', 0)} pos={item.get('competitor_position')} - {item['reason']}"
        )
    summary.extend(["", "## AEO Prompt Candidates", ""])
    for item in prompts:
        summary.append(
            f"- `{item['prompt']}` score={item['score']} cadence={item['recommended_cadence']} - {item['reason']}"
        )
    summary.extend(
        [
            "",
            "## Apply Rule",
            "",
            "This run is evidence and proposals only. Apply to weekly/cluster/daily presets only after operator approval.",
            "",
        ]
    )
    with open(run_dir / "summary.md", "w", encoding="utf-8") as f:
        f.write("\n".join(summary))

    _record_run_in_local_db(
        run_id=run_id,
        run_dir=run_dir,
        domain=domain,
        cluster=cluster,
        profile=profile,
        keywords=keywords,
        prompts=prompts,
    )

    return run_dir


def _record_run_in_local_db(
    *,
    run_id: str,
    run_dir: Path,
    domain: str,
    cluster: str,
    profile: dict[str, Any],
    keywords: list[dict[str, Any]],
    prompts: list[dict[str, Any]],
) -> None:
    db = _load_local_db()
    now = datetime.now(timezone.utc).isoformat()

    run_record = {
        "run_id": run_id,
        "target": domain,
        "cluster": cluster or "all",
        "status": "proposed",
        "created_at": now,
        "path": str(run_dir),
        "keyword_candidates": len(keywords),
        "ai_prompt_candidates": len(prompts),
    }
    db["runs"] = [r for r in db.get("runs", []) if r.get("run_id") != run_id]
    db["runs"].append(run_record)

    competitors = db.setdefault("competitors", {})
    competitor_record = competitors.setdefault(
        domain,
        {
            "domain": domain,
            "first_seen_at": now,
            "runs": [],
            "profile": {},
            "latest_run_id": "",
        },
    )
    competitor_record["latest_run_id"] = run_id
    competitor_record["last_seen_at"] = now
    competitor_record["profile"] = profile
    if run_id not in competitor_record["runs"]:
        competitor_record["runs"].append(run_id)

    candidate_db = db.setdefault("candidates", {"keywords": [], "ai_prompts": []})
    candidate_db["keywords"] = [
        item for item in candidate_db.get("keywords", [])
        if not (item.get("run_id") == run_id and item.get("target") == domain)
    ]
    candidate_db["ai_prompts"] = [
        item for item in candidate_db.get("ai_prompts", [])
        if not (item.get("run_id") == run_id and item.get("target") == domain)
    ]

    for item in keywords:
        record = dict(item)
        record.update({"run_id": run_id, "target": domain, "created_at": now})
        candidate_db["keywords"].append(record)
    for item in prompts:
        record = dict(item)
        record.update({"run_id": run_id, "target": domain, "created_at": now})
        candidate_db["ai_prompts"].append(record)

    _save_local_db(db)


def _find_run(run_id: str) -> Path | None:
    if not RESEARCH_RUNS_DIR.is_dir():
        return None
    runs = sorted([p for p in RESEARCH_RUNS_DIR.iterdir() if p.is_dir()])
    if not runs:
        return None
    if run_id == "latest":
        return runs[-1]
    exact = RESEARCH_RUNS_DIR / run_id
    if exact.is_dir():
        return exact
    matches = [p for p in runs if p.name.endswith(run_id) or run_id in p.name]
    return matches[-1] if matches else None


def _list_runs() -> None:
    db = _load_local_db()
    runs = db.get("runs", [])
    if not runs:
        print("No competitor research runs yet.")
        return

    print("\nCompetitor research runs")
    for item in runs[-20:]:
        print(
            f"  {item.get('run_id')}  target={item.get('target')}  "
            f"status={item.get('status')}  kw={item.get('keyword_candidates', 0)} "
            f"prompts={item.get('ai_prompt_candidates', 0)}"
        )


def _print_db_summary() -> None:
    db = _load_local_db()
    if not LOCAL_DB_PATH.is_file():
        _save_local_db(db)
    print("\nSearchstack local research DB")
    print(f"  Path: {LOCAL_DB_PATH}")
    print(f"  Schema: {db.get('schema_version')}")
    print(f"  Updated: {db.get('updated_at') or '-'}")
    print(f"  Runs: {len(db.get('runs', []))}")
    print(f"  Competitors: {len(db.get('competitors', {}))}")
    candidates = db.get("candidates", {})
    print(f"  Keyword candidates: {len(candidates.get('keywords', []))}")
    print(f"  AEO prompt candidates: {len(candidates.get('ai_prompts', []))}")


def _print_candidates(run_id: str) -> None:
    run_dir = _find_run(run_id)
    if not run_dir:
        print(f"No run found for {run_id!r}.")
        return

    candidates = _load_json(run_dir / "candidates.json") or {}
    keywords = candidates.get("keywords", [])
    prompts = candidates.get("ai_prompts", [])

    print(f"\nCandidates: {run_dir.name}")
    print(f"  Path: {run_dir}")

    if keywords:
        print("\nKeyword candidates")
        for item in keywords:
            print(
                f"  {item.get('id')}  score={item.get('score', 0):>3}  "
                f"{item.get('recommended_cadence', ''):<16} {item.get('keyword')} "
                f"vol={item.get('volume', 0)} pos={item.get('competitor_position')}"
            )
    else:
        print("\nNo keyword candidates.")

    if prompts:
        print("\nAEO prompt candidates")
        for item in prompts:
            print(
                f"  {item.get('id')}  score={item.get('score', 0):>3}  "
                f"{item.get('recommended_cadence', ''):<16} {item.get('prompt')}"
            )
    else:
        print("\nNo AEO prompt candidates.")

    print("\nGuard: candidates are proposed only. Apply/promote only after operator approval.")


def _print_usage() -> None:
    print(
        """Usage:
  searchstack competitor study <domain> [--cluster <name>]
  searchstack competitor list
  searchstack competitor candidates <run_id|latest>
  searchstack competitor db

Examples:
  searchstack competitor study competitor.com
  searchstack competitor study competitor.com --cluster pricing
  searchstack competitor candidates latest
  searchstack competitor db

This command saves a proposed research run under research/runs/.
It does not modify presets, .searchstack.toml, daily jobs, or server runtime."""
    )


def run(config: Config, *args: str) -> None:
    if not args or args[0] in {"-h", "--help", "help"}:
        _print_usage()
        return

    action = args[0]
    if action == "list":
        _list_runs()
        return

    if action == "db":
        _print_db_summary()
        return

    if action in {"candidates", "show"}:
        _print_candidates(args[1] if len(args) > 1 else "latest")
        return

    if action != "study":
        print(f"Unknown competitor action: {action}")
        print()
        _print_usage()
        return

    if len(args) < 2:
        _print_usage()
        return

    if not _check_configured(config):
        return

    domain = _normalize_domain(args[1])
    if not domain:
        print("Target domain is required.")
        return

    cluster = ""
    rest = list(args[2:])
    if "--cluster" in rest:
        idx = rest.index("--cluster")
        if idx + 1 < len(rest):
            cluster = rest[idx + 1]

    print(f"\nCompetitor research: {domain}")
    print("  Guard: study only; no runtime/server changes will be applied.")

    profile = _find_competitor_profile(domain)
    seeds = _seed_keywords(config, cluster)

    print(f"  Known competitor: {profile.get('known')}")
    print(f"  Seed keywords: {len(seeds)}")
    print("  Fetching ranked keywords from DataForSEO...")
    ranked = _fetch_ranked_keywords(config, domain)

    if ranked and "error" in ranked[0]:
        print(f"  DataForSEO error: {ranked[0]['error']}")
        return

    print(f"  Ranked keywords: {len(ranked)}")
    print("  Checking SERP overlap for seed keywords...")
    serp_overlap = _fetch_serp_overlap(config, seeds, domain) if seeds else []

    current = _current_keywords(config)
    keyword_candidates = _candidate_keywords(ranked, current, profile)
    prompt_candidates = _candidate_prompts(domain, profile, keyword_candidates)

    run_dir = _write_run(
        domain=domain,
        cluster=cluster or "all",
        profile=profile,
        seeds=seeds,
        ranked=ranked,
        serp_overlap=serp_overlap,
        keywords=keyword_candidates,
        prompts=prompt_candidates,
    )

    daily = [c for c in keyword_candidates if c["recommended_cadence"] == "daily_candidate"]
    weekly = [c for c in keyword_candidates if c["recommended_cadence"] == "weekly_candidate"]

    print("\nResult")
    print(f"  Run: {run_dir}")
    print(f"  Keyword candidates: {len(keyword_candidates)}")
    print(f"    daily candidates: {len(daily)}")
    print(f"    weekly candidates: {len(weekly)}")
    print(f"  AEO prompt candidates: {len(prompt_candidates)}")

    if keyword_candidates:
        print("\nTop keyword candidates")
        for item in keyword_candidates[:8]:
            print(
                f"  {item['id']}  score={item['score']:>3}  {item['recommended_cadence']:<16} "
                f"{item['keyword']}  vol={item.get('volume', 0)} pos={item.get('competitor_position')}"
            )

    if prompt_candidates:
        print("\nAEO prompt candidates")
        for item in prompt_candidates:
            print(f"  {item['id']}  score={item['score']:>3}  {item['prompt']}")

    print("\nNext: review candidates.json. Apply/promote only after operator approval.")
