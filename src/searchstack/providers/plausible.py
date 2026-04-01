"""Plausible Analytics API provider.

Uses the v2 query API: https://plausible.io/api/v2/query
All HTTP via urllib.request.
"""

from __future__ import annotations

import json
import urllib.request
import urllib.error
from typing import Any

from searchstack.config import Config

BASE = "https://plausible.io/api/v2/query"


def query(config: Config, body: dict[str, Any]) -> dict[str, Any]:
    """POST a query to the Plausible Analytics v2 API.

    Automatically injects site_id from config into the request body.
    Returns parsed JSON on success, or {"error": str} on failure.
    """
    body.setdefault("site_id", config.plausible.site_id)

    data = json.dumps(body).encode()
    headers = {
        "Authorization": f"Bearer {config.plausible.api_key}",
        "Content-Type": "application/json",
    }
    req = urllib.request.Request(BASE, data=data, headers=headers, method="POST")

    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read())  # type: ignore[no-any-return]
    except urllib.error.HTTPError as exc:
        return {"error": f"HTTP {exc.code}: {exc.reason}"}
    except Exception as exc:
        return {"error": str(exc)}
