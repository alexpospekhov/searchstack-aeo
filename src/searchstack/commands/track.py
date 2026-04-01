"""Position tracking -- compare current rankings to previous snapshot."""

from __future__ import annotations

import json
from pathlib import Path

from searchstack.config import Config
from searchstack.providers.dataforseo import (
    api_request,
    get_language_code,
    get_location_code,
)
from searchstack.snapshots import get_snapshot_dir, save_positions


def _check_configured(config: Config) -> bool:
    if not config.dataforseo.login or not config.dataforseo.password:
        print("❌ DataForSEO not configured. Set [dataforseo] in .searchstack.toml")
        return False
    return True


def _load_previous() -> dict[str, dict[str, int]]:
    """Load the previous positions_latest.json snapshot."""
    latest_path = get_snapshot_dir() / "positions_latest.json"
    if not latest_path.exists():
        return {}
    try:
        with open(latest_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return {}


def run(config: Config, *args: str) -> None:
    """Track position changes since the last snapshot."""
    if not _check_configured(config):
        return

    target = config.domain
    if not target:
        print("Set domain in .searchstack.toml")
        return

    body = [
        {
            "target": target,
            "location_code": get_location_code(config),
            "language_code": get_language_code(config),
            "limit": 100,
        }
    ]

    data = api_request(config, "dataforseo_labs/google/ranked_keywords/live", body)

    if "error" in data:
        print(f"API error: {data['error']}")
        return

    tasks = data.get("tasks", [])
    if not tasks or not tasks[0].get("result"):
        print("No results returned.")
        return

    items = tasks[0]["result"][0].get("items", [])
    if not items:
        print(f"No ranked keywords for {target}.")
        return

    # Build current positions
    current: dict[str, dict[str, int]] = {}
    for item in items:
        kw_data = item.get("keyword_data", {})
        info = kw_data.get("keyword_info", {})
        ranked = item.get("ranked_serp_element", {}) or {}
        serp_item = ranked.get("serp_item", {}) or {}

        keyword = kw_data.get("keyword", "")
        position = serp_item.get("rank_absolute") or item.get("rank_absolute", 0)
        volume = info.get("search_volume") or 0

        if keyword:
            current[keyword] = {"pos": position, "vol": volume}

    # Load previous
    previous = _load_previous()

    # Compare
    improved: list[tuple[str, int, int, int, int]] = []
    declined: list[tuple[str, int, int, int, int]] = []
    new_kws: list[tuple[str, int, int]] = []

    for kw, now in current.items():
        if kw in previous:
            prev_pos = previous[kw]["pos"]
            now_pos = now["pos"]
            delta = prev_pos - now_pos  # positive = improved
            if prev_pos > now_pos:
                improved.append((kw, prev_pos, now_pos, delta, now["vol"]))
            elif prev_pos < now_pos:
                declined.append((kw, prev_pos, now_pos, delta, now["vol"]))
        else:
            new_kws.append((kw, now["pos"], now["vol"]))

    # Print table
    all_rows: list[tuple[str, str, str, str, int]] = []
    for kw, prev, now, delta, vol in improved:
        delta_str = f"+{delta}"
        all_rows.append((kw, str(prev), str(now), delta_str, vol))
    for kw, prev, now, delta, vol in declined:
        all_rows.append((kw, str(prev), str(now), str(delta), vol))
    for kw, pos, vol in new_kws:
        all_rows.append((kw, "—", str(pos), "new", vol))

    # Sort: improved first, then declined, then new
    all_rows.sort(key=lambda r: (0 if r[3].startswith("+") else 1 if r[3].lstrip("-").isdigit() else 2, r[0]))

    if all_rows:
        kw_width = max(len(r[0]) for r in all_rows)
        kw_width = max(kw_width, 7)

        print(f"\nPosition tracking for {target}")
        if not previous:
            print("(first run — no previous data to compare)")
        print(f"{'Keyword':<{kw_width}}  {'Prev':>5}  {'Now':>5}  {'Delta':>6}  {'Volume':>8}")
        print(f"{'─' * kw_width}  {'─' * 5}  {'─' * 5}  {'─' * 6}  {'─' * 8}")

        for kw, prev, now, delta, vol in all_rows:
            print(f"{kw:<{kw_width}}  {prev:>5}  {now:>5}  {delta:>6}  {vol:>8,}")
    else:
        print(f"\nPosition tracking for {target}")
        print("No changes detected.")

    # Summary
    print(f"\n↑{len(improved)} improved | ↓{len(declined)} declined | 🆕{len(new_kws)} new")

    # Save current snapshot
    path = save_positions(current)
    print(f"Saved: {path}")
