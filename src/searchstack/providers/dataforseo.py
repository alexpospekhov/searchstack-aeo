"""DataForSEO API provider.

Uses the `requests` library (not urllib) because DataForSEO endpoints
require complex nested JSON bodies that benefit from requests' ergonomics.
"""

from __future__ import annotations

import base64
from typing import Any

import requests

from searchstack.config import Config


def get_auth(config: Config) -> str:
    """Return base64-encoded login:password for the Authorization header."""
    credentials = f"{config.dataforseo.login}:{config.dataforseo.password}"
    return base64.b64encode(credentials.encode()).decode()


def api_request(
    config: Config,
    endpoint: str,
    body: list[dict[str, Any]],
) -> dict[str, Any]:
    """POST to https://api.dataforseo.com/v3/{endpoint}.

    Returns parsed JSON response, or {"error": str} on failure.
    """
    url = f"https://api.dataforseo.com/v3/{endpoint.lstrip('/')}"
    headers = {
        "Authorization": f"Basic {get_auth(config)}",
        "Content-Type": "application/json",
    }

    try:
        resp = requests.post(url, json=body, headers=headers, timeout=60)
        resp.raise_for_status()
        return resp.json()  # type: ignore[no-any-return]
    except requests.exceptions.HTTPError as exc:
        return {"error": f"HTTP {exc.response.status_code}: {exc.response.text[:500]}"}
    except requests.exceptions.RequestException as exc:
        return {"error": str(exc)}


def get_location_code(config: Config) -> int:
    """Return location_code from config, default 2840 (US)."""
    return config.dataforseo.location_code or 2840


def get_language_code(config: Config) -> str:
    """Return language_code from config, default 'en'."""
    return config.dataforseo.language_code or "en"
