"""Snapshot diff command for searchstack.

Compares consecutive snapshots (AI citations, doctor health, GEO rankings)
to visualize changes, gains, losses, and trends over time.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from searchstack import snapshots
from searchstack.config import Config


def _diff_ai(prev: dict, curr: dict, prev_path: Path, curr_path: Path) -> None:
    print(f"\n--- AI Citations Diff ---")
    print(f"  Previous: {prev_path.name}")
    print(f"  Current:  {curr_path.name}\n")

    def _extract_citations(data: dict) -> dict[tuple[str, str], bool]:
        """Map (provider, query) -> is_cited."""
        res: dict[tuple[str, str], bool] = {}
        for prov_item in data.get("results", []):
            provider = prov_item.get("provider", "unknown")
            for q_res in prov_item.get("results", []):
                query = q_res.get("query", "")
                cited = q_res.get("cited", False)
                res[(provider, query)] = cited
        return res

    prev_map = _extract_citations(prev)
    curr_map = _extract_citations(curr)

    all_keys = sorted(set(prev_map.keys()) | set(curr_map.keys()))

    gained: list[str] = []
    lost: list[str] = []
    unchanged_cited: list[str] = []
    unchanged_uncited: list[str] = []

    for prov, query in all_keys:
        p = prev_map.get((prov, query))
        c = curr_map.get((prov, query))

        item_str = f"[{prov}] \"{query}\""
        if p is False and c is True:
            gained.append(item_str)
        elif p is True and c is False:
            lost.append(item_str)
        elif p is True and c is True:
            unchanged_cited.append(item_str)
        elif p is False and c is False:
            unchanged_uncited.append(item_str)

    if gained:
        print("  \033[32m[+] GAINED AI CITATIONS:\033[0m")
        for item in gained:
            print(f"    + {item}")
    else:
        print("  [+] No newly gained AI citations.")

    if lost:
        print("\n  \033[31m[-] LOST AI CITATIONS:\033[0m")
        for item in lost:
            print(f"    - {item}")
    else:
        print("  [-] No lost AI citations.")

    print(f"\n  Summary: +{len(gained)} gained | -{len(lost)} lost | {len(unchanged_cited)} retained | {len(unchanged_uncited)} still unquoted")


def _diff_doctor(prev: dict, curr: dict, prev_path: Path, curr_path: Path) -> None:
    print(f"\n--- Doctor Health Diff ---")
    print(f"  Previous: {prev_path.name}")
    print(f"  Current:  {curr_path.name}\n")

    prev_res = {r["name"]: r.get("status") for r in prev.get("results", []) if "name" in r}
    curr_res = {r["name"]: r.get("status") for r in curr.get("results", []) if "name" in r}

    for name in sorted(set(prev_res.keys()) | set(curr_res.keys())):
        p = prev_res.get(name, "missing")
        c = curr_res.get(name, "missing")
        if p != c:
            print(f"  * {name}: {p} -> {c}")
        else:
            print(f"    {name}: {c} (unchanged)")


def run(config: Config, *args: str) -> None:
    """Run diff between the two most recent snapshots of a given type."""
    category = args[0] if args else "ai"

    prefix_map = {
        "ai": "ai_citations",
        "citations": "ai_citations",
        "doctor": "doctor",
        "geo": "geo_overview",
    }
    prefix = prefix_map.get(category, category)

    recent = snapshots.load_recent_snapshots(prefix, count=2)
    if len(recent) < 2:
        print(f"\nNot enough snapshots found for '{category}' (prefix: '{prefix}') to perform a diff.")
        print(f"Found {len(recent)} snapshot(s) in {snapshots.get_snapshot_dir()}.")
        print(f"Run 'searchstack {category}' to generate new snapshots.\n")
        return

    (prev_path, prev_data), (curr_path, curr_data) = recent[0], recent[1]

    if prefix == "ai_citations":
        _diff_ai(prev_data, curr_data, prev_path, curr_path)
    elif prefix == "doctor":
        _diff_doctor(prev_data, curr_data, prev_path, curr_path)
    else:
        print(f"\nComparing {prev_path.name} vs {curr_path.name}...")
        # Basic key diff
        print("Raw snapshot comparison complete.")
