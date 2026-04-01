"""Configuration loader for searchstack.

Reads from .searchstack.toml (CWD first, then ~/.config/searchstack/config.toml),
overlays environment variables, and returns typed Config dataclass.
"""

from __future__ import annotations

import base64
import os
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

if sys.version_info >= (3, 11):
    import tomllib
else:
    try:
        import tomli as tomllib  # type: ignore[no-redef]
    except ImportError as exc:
        raise ImportError(
            "Python < 3.11 requires the 'tomli' package: pip install tomli"
        ) from exc


# ---------------------------------------------------------------------------
# Config dataclasses
# ---------------------------------------------------------------------------

@dataclass
class GscConfig:
    credentials_file: str = "credentials.json"
    site_url: str = ""
    gcp_project: str = ""


@dataclass
class DataforseoConfig:
    login: str = ""
    password: str = ""
    location_code: int = 2840
    language_code: str = "en"


@dataclass
class ApiKeyConfig:
    api_key: str = ""


@dataclass
class PlausibleConfig:
    api_key: str = ""
    site_id: str = ""


@dataclass
class IndexnowConfig:
    key: str = ""


@dataclass
class OllamaConfig:
    base_url: str = "http://localhost:11434/v1"
    model: str = ""
    api_key: str = ""


@dataclass
class GoogleAdsConfig:
    customer_id: str = ""
    developer_token: str = ""
    client_id: str = ""
    client_secret: str = ""
    refresh_token: str = ""
    location_code: int = 2840
    language_code: str = "en"


@dataclass
class Config:
    domain: str = ""
    sitemap: str = ""
    gsc: GscConfig = field(default_factory=GscConfig)
    dataforseo: DataforseoConfig = field(default_factory=DataforseoConfig)
    openai: ApiKeyConfig = field(default_factory=ApiKeyConfig)
    perplexity: ApiKeyConfig = field(default_factory=ApiKeyConfig)
    anthropic: ApiKeyConfig = field(default_factory=ApiKeyConfig)
    grok: ApiKeyConfig = field(default_factory=ApiKeyConfig)
    ollama: OllamaConfig = field(default_factory=OllamaConfig)
    plausible: PlausibleConfig = field(default_factory=PlausibleConfig)
    bing: ApiKeyConfig = field(default_factory=ApiKeyConfig)
    indexnow: IndexnowConfig = field(default_factory=IndexnowConfig)
    google_ads: GoogleAdsConfig = field(default_factory=GoogleAdsConfig)
    ai_queries: list[str] = field(default_factory=list)
    geo_keywords: dict[str, list[str]] = field(default_factory=dict)
    competitors: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _find_toml() -> Path | None:
    """Find the first .searchstack.toml: CWD, then ~/.config/searchstack/."""
    cwd_path = Path.cwd() / ".searchstack.toml"
    if cwd_path.is_file():
        return cwd_path

    xdg_path = Path.home() / ".config" / "searchstack" / "config.toml"
    if xdg_path.is_file():
        return xdg_path

    return None


def _get_nested(data: dict[str, Any], *keys: str, default: Any = "") -> Any:
    """Safely traverse nested dicts."""
    current = data
    for key in keys:
        if not isinstance(current, dict):
            return default
        current = current.get(key, default)
    return current


def _build_config(raw: dict[str, Any]) -> Config:
    """Build Config from parsed TOML dict."""
    gsc_raw = raw.get("gsc", {})
    dfs_raw = raw.get("dataforseo", {})
    plausible_raw = raw.get("plausible", {})
    ga_raw = raw.get("google_ads", {})

    return Config(
        domain=raw.get("domain", ""),
        sitemap=raw.get("sitemap", ""),
        gsc=GscConfig(
            credentials_file=gsc_raw.get("credentials_file", "credentials.json"),
            site_url=gsc_raw.get("site_url", ""),
            gcp_project=gsc_raw.get("gcp_project", ""),
        ),
        dataforseo=DataforseoConfig(
            login=dfs_raw.get("login", ""),
            password=dfs_raw.get("password", ""),
            location_code=dfs_raw.get("location_code", 2840),
            language_code=dfs_raw.get("language_code", "en"),
        ),
        openai=ApiKeyConfig(api_key=_get_nested(raw, "openai", "api_key")),
        perplexity=ApiKeyConfig(api_key=_get_nested(raw, "perplexity", "api_key")),
        anthropic=ApiKeyConfig(api_key=_get_nested(raw, "anthropic", "api_key")),
        grok=ApiKeyConfig(api_key=_get_nested(raw, "grok", "api_key")),
        ollama=OllamaConfig(
            base_url=_get_nested(raw, "ollama", "base_url") or "http://localhost:11434/v1",
            model=_get_nested(raw, "ollama", "model"),
            api_key=_get_nested(raw, "ollama", "api_key"),
        ),
        plausible=PlausibleConfig(
            api_key=plausible_raw.get("api_key", ""),
            site_id=plausible_raw.get("site_id", ""),
        ),
        bing=ApiKeyConfig(api_key=_get_nested(raw, "bing", "api_key")),
        indexnow=IndexnowConfig(key=_get_nested(raw, "indexnow", "key")),
        google_ads=GoogleAdsConfig(
            customer_id=ga_raw.get("customer_id", ""),
            developer_token=ga_raw.get("developer_token", ""),
            client_id=ga_raw.get("client_id", ""),
            client_secret=ga_raw.get("client_secret", ""),
            refresh_token=ga_raw.get("refresh_token", ""),
            location_code=ga_raw.get("location_code", 2840),
            language_code=ga_raw.get("language_code", "en"),
        ),
        ai_queries=raw.get("ai_queries", []),
        geo_keywords=raw.get("geo_keywords", {}),
        competitors=raw.get("competitors", []),
    )


_ENV_MAP: dict[str, tuple[str, ...]] = {
    "DATAFORSEO_LOGIN": ("dataforseo", "login"),
    "DATAFORSEO_PASSWORD": ("dataforseo", "password"),
    "OPENAI_API_KEY": ("openai", "api_key"),
    "PERPLEXITY_API_KEY": ("perplexity", "api_key"),
    "ANTHROPIC_API_KEY": ("anthropic", "api_key"),
    "XAI_API_KEY": ("grok", "api_key"),
    "PLAUSIBLE_API_KEY": ("plausible", "api_key"),
    "BING_WEBMASTER_API_KEY": ("bing", "api_key"),
    "GOOGLE_ADS_DEVELOPER_TOKEN": ("google_ads", "developer_token"),
    "GOOGLE_ADS_CUSTOMER_ID": ("google_ads", "customer_id"),
}


def _overlay_env(cfg: Config) -> None:
    """Override config fields with environment variables when set."""
    for env_var, attr_path in _ENV_MAP.items():
        value = os.environ.get(env_var)
        if not value:
            continue
        obj = cfg
        for part in attr_path[:-1]:
            obj = getattr(obj, part)
        setattr(obj, attr_path[-1], value)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def load_config() -> Config:
    """Load configuration from TOML file + environment variable overrides."""
    toml_path = _find_toml()
    raw: dict[str, Any] = {}

    if toml_path is not None:
        with open(toml_path, "rb") as f:
            raw = tomllib.load(f)

    cfg = _build_config(raw)
    _overlay_env(cfg)
    return cfg


def dataforseo_auth(cfg: Config | None = None) -> str:
    """Return base64-encoded login:password for DataForSEO API auth."""
    if cfg is None:
        cfg = load_config()
    credentials = f"{cfg.dataforseo.login}:{cfg.dataforseo.password}"
    return base64.b64encode(credentials.encode()).decode()
