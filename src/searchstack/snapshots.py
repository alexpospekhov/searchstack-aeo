"""Snapshot manager for searchstack.

Persists command outputs as timestamped JSON files under ~/.searchstack/snapshots/.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path


def get_snapshot_dir() -> Path:
    """Return (and create) the snapshots directory."""
    snapshot_dir = Path.home() / ".searchstack" / "snapshots"
    snapshot_dir.mkdir(parents=True, exist_ok=True)
    return snapshot_dir


def save_snapshot(name: str, data: dict) -> Path:
    """Save data as {name}_{timestamp}.json and return the file path."""
    snapshot_dir = get_snapshot_dir()
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    filename = f"{name}_{ts}.json"
    path = snapshot_dir / filename

    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False, default=str)

    return path


def load_latest_snapshot(prefix: str) -> dict | None:
    """Load the most recent snapshot matching the given prefix, or None."""
    snapshot_dir = get_snapshot_dir()
    matches = sorted(snapshot_dir.glob(f"{prefix}_*.json"))

    if not matches:
        return None

    latest = matches[-1]
    with open(latest, "r", encoding="utf-8") as f:
        return json.load(f)


def save_positions(data: dict) -> Path:
    """Save position data as both positions_latest.json and a timestamped copy."""
    snapshot_dir = get_snapshot_dir()

    # Always overwrite the "latest" file
    latest_path = snapshot_dir / "positions_latest.json"
    with open(latest_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False, default=str)

    # Also save a timestamped copy
    save_snapshot("positions", data)

    return latest_path
