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
        if not creds_path.exists():
            return None
        try:
            from google_auth_oauthlib.flow import InstalledAppFlow

            scopes = [
                "https://www.googleapis.com/auth/webmasters.readonly",
                "https://www.googleapis.com/auth/webmasters",
                "https://www.googleapis.com/auth/indexing",
            ]
            print(f"  No token.pickle found. Starting Google OAuth flow with {creds_path.name}...")
            flow = InstalledAppFlow.from_client_secrets_file(str(creds_path), scopes)
            new_creds = flow.run_local_server(port=0)
            with open(token_path, "wb") as f:
                pickle.dump(new_creds, f)
            token_path.chmod(0o600)
            return new_creds.token
        except Exception as exc:
            print(f"  Google OAuth flow failed: {exc}")
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
            raw = resp.read()
            if not raw:
                return {}
            return json.loads(raw)  # type: ignore[no-any-return]
    except urllib.error.HTTPError as exc:
        return {"error": f"HTTP {exc.code}: {exc.reason}"}
    except Exception as exc:
        return {"error": str(exc)}


def get_gsc_site_url_encoded(config: Config) -> str:
    """URL-encode the site_url for API path segments.

    Example: sc-domain:example.com -> sc-domain%3Aexample.com
    """
    return quote(config.gsc.site_url, safe="")


def query(
    *,
    site_url: str,
    start_date: str,
    end_date: str,
    dimensions: list[str],
    config: Config,
    row_limit: int = 100,
    search_type: str = "web",
) -> dict[str, Any]:
    """Run Search Analytics query with optional search type (web, discover, googleNews)."""
    encoded_site = quote(site_url, safe="")
    body: dict[str, Any] = {
        "startDate": start_date,
        "endDate": end_date,
        "dimensions": dimensions,
        "rowLimit": row_limit,
    }
    if search_type and search_type != "web":
        body["type"] = search_type
    data = gsc_request(
        config,
        f"webmasters/v3/sites/{encoded_site}/searchAnalytics/query",
        method="POST",
        body=body,
    )
    return data or {"rows": []}


def list_sitemaps(*, site_url: str, config: Config) -> dict[str, Any]:
    """List submitted sitemaps for the property."""
    encoded_site = quote(site_url, safe="")
    data = gsc_request(
        config,
        f"webmasters/v3/sites/{encoded_site}/sitemaps",
        method="GET",
    )
    return data or {"sitemap": []}


def submit_sitemap(*, site_url: str, sitemap_url: str, config: Config) -> dict[str, Any]:
    """Submit or resubmit a sitemap."""
    encoded_site = quote(site_url, safe="")
    encoded_sitemap = quote(sitemap_url, safe="")
    data = gsc_request(
        config,
        f"webmasters/v3/sites/{encoded_site}/sitemaps/{encoded_sitemap}",
        method="PUT",
    )
    return data or {"status": "submitted"}


def inspect_url(*, site_url: str, url: str, config: Config) -> dict[str, Any]:
    """Inspect one URL via the URL Inspection API."""
    body = {
        "inspectionUrl": url,
        "siteUrl": site_url,
    }
    data = gsc_request(
        config,
        "v1/urlInspection/index:inspect",
        method="POST",
        body=body,
    )
    return data or {"inspectionResult": {}}
