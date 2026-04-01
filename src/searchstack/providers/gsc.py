"""Google Search Console API provider.

Uses token.pickle for auth (auto-refreshes expired tokens).
All HTTP via urllib.request — no external dependencies beyond google-auth.
"""

from __future__ import annotations

import json
import pickle
import urllib.request
import urllib.error
from pathlib import Path
from typing import Any
from urllib.parse import quote

from searchstack.config import Config


def get_gsc_token(config: Config) -> str | None:
    """Load OAuth token from token.pickle, auto-refresh if expired.

    Looks for token.pickle next to the credentials_file path.
    Returns the access token string, or None on failure.
    """
    creds_path = Path(config.gsc.credentials_file)
    token_path = creds_path.parent / "token.pickle"

    if not token_path.exists():
        return None

    try:
        with open(token_path, "rb") as f:
            creds = pickle.load(f)  # noqa: S301
    except Exception:
        return None

    if creds.expired and creds.refresh_token:
        try:
            from google.auth.transport.requests import Request  # type: ignore[import-untyped]

            creds.refresh(Request())
            with open(token_path, "wb") as f:
                pickle.dump(creds, f)
        except Exception:
            return None

    return creds.token  # type: ignore[no-any-return]


def gsc_request(
    config: Config,
    endpoint: str,
    method: str = "GET",
    body: dict[str, Any] | None = None,
) -> dict[str, Any] | None:
    """Make a Google Search Console API request.

    Base URL: https://searchconsole.googleapis.com/
    Returns parsed JSON on success, None on failure.
    """
    token = get_gsc_token(config)
    if not token:
        return None

    url = f"https://searchconsole.googleapis.com/{endpoint.lstrip('/')}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    if config.gsc.gcp_project:
        headers["x-goog-user-project"] = config.gsc.gcp_project

    data = json.dumps(body).encode() if body else None
    req = urllib.request.Request(url, data=data, headers=headers, method=method)

    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read())  # type: ignore[no-any-return]
    except urllib.error.HTTPError as exc:
        return {"error": f"HTTP {exc.code}: {exc.reason}"}
    except Exception as exc:
        return {"error": str(exc)}


def get_gsc_site_url_encoded(config: Config) -> str:
    """URL-encode the site_url for API path segments.

    Example: sc-domain:example.com -> sc-domain%3Aexample.com
    """
    return quote(config.gsc.site_url, safe="")
