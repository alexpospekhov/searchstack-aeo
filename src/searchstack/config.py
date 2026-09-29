"""Configuration loader for searchstack.

Reads from .searchstack.toml (CWD first, then ~/.config/searchstack/config.toml),
supports named presets, overlays environment variables and system secret stores,
and returns a typed Config dataclass.
"""

from __future__ import annotations

import base64
from functools import lru_cache
import os
from pathlib import Path
import subprocess
import sys
from dataclasses import dataclass, field
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
class OpenrouterConfig:
    """Unified OpenRouter routing for all AI citation providers.

    When ``api_key`` is set, the openai / anthropic / perplexity / grok
    providers route their requests through OpenRouter's OpenAI-compatible
    endpoint using the model IDs below, instead of hitting each vendor's
    native API. This lets a user run ``searchstack ai`` with a single key and
    unified billing, which matches how many AI-native founders already manage
    their API access today.

    Leaving ``api_key`` empty preserves the original behavior — native APIs
    direct, no change for existing users.
    """
    api_key: str = ""
    base_url: str = "https://openrouter.ai/api/v1"
    chatgpt_model: str = "openai/gpt-4o-mini"
    claude_model: str = "anthropic/claude-haiku-4.5"
    perplexity_model: str = "perplexity/sonar"
    grok_model: str = "x-ai/grok-3-mini"


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
    gemini: ApiKeyConfig = field(default_factory=ApiKeyConfig)
    ollama: OllamaConfig = field(default_factory=OllamaConfig)
    openrouter: OpenrouterConfig = field(default_factory=OpenrouterConfig)
    plausible: PlausibleConfig = field(default_factory=PlausibleConfig)
    bing: ApiKeyConfig = field(default_factory=ApiKeyConfig)
    indexnow: IndexnowConfig = field(default_factory=IndexnowConfig)
    google_ads: GoogleAdsConfig = field(default_factory=GoogleAdsConfig)
    ai_queries: list[str] = field(default_factory=list)
    geo_keywords: dict[str, list[str]] = field(default_factory=dict)
    competitors: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Presets and paths
# ---------------------------------------------------------------------------

PRESET_DIRS = [
    Path.cwd() / "presets",
    Path.home() / ".config" / "searchstack" / "presets",
]


def _find_preset(preset_name: str) -> Path | None:
    filename = preset_name if preset_name.endswith(".toml") else f"{preset_name}.toml"
    for pdir in PRESET_DIRS:
        candidate = pdir / filename
        if candidate.is_file():
            return candidate
    return None


def _find_toml() -> Path | None:
    """Find the default config file: env var, preset, CWD, then ~/.config/searchstack/."""
    env_path = os.environ.get("SEARCHSTACK_CONFIG", "").strip()
    if env_path:
        resolved = Path(env_path).expanduser()
        if resolved.is_file():
            return resolved

    env_preset = os.environ.get("SEARCHSTACK_PRESET", "").strip()
    if env_preset:
        preset_file = _find_preset(env_preset)
        if preset_file:
            return preset_file

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
        gemini=ApiKeyConfig(api_key=_get_nested(raw, "gemini", "api_key")),
        ollama=OllamaConfig(
            base_url=_get_nested(raw, "ollama", "base_url") or "http://localhost:11434/v1",
            model=_get_nested(raw, "ollama", "model"),
            api_key=_get_nested(raw, "ollama", "api_key"),
        ),
        openrouter=OpenrouterConfig(
            api_key=_get_nested(raw, "openrouter", "api_key"),
            base_url=_get_nested(raw, "openrouter", "base_url") or "https://openrouter.ai/api/v1",
            chatgpt_model=_get_nested(raw, "openrouter", "chatgpt_model") or "openai/gpt-4o-mini",
            claude_model=_get_nested(raw, "openrouter", "claude_model") or "anthropic/claude-haiku-4.5",
            perplexity_model=_get_nested(raw, "openrouter", "perplexity_model") or "perplexity/sonar",
            grok_model=_get_nested(raw, "openrouter", "grok_model") or "x-ai/grok-3-mini",
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
    "GROK_API_KEY": ("grok", "api_key"),
    "GEMINI_API_KEY": ("gemini", "api_key"),
    "OPENROUTER_API_KEY": ("openrouter", "api_key"),
    "PLAUSIBLE_API_KEY": ("plausible", "api_key"),
    "BING_WEBMASTER_API_KEY": ("bing", "api_key"),
    "GOOGLE_ADS_DEVELOPER_TOKEN": ("google_ads", "developer_token"),
    "GOOGLE_ADS_CUSTOMER_ID": ("google_ads", "customer_id"),
    "GOOGLE_ADS_CLIENT_ID": ("google_ads", "client_id"),
    "GOOGLE_ADS_CLIENT_SECRET": ("google_ads", "client_secret"),
    "GOOGLE_ADS_REFRESH_TOKEN": ("google_ads", "refresh_token"),
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


@lru_cache(maxsize=64)
def _get_keychain_secret(secret_name: str) -> str:
    """Fetch secret from macOS Keychain via `security find-generic-password`."""
    if sys.platform != "darwin":
        return ""
    candidates = [
        secret_name,
        f"hf-{secret_name}",
        secret_name.replace("-", "_"),
        secret_name.replace("_", "-"),
    ]
    seen: set[str] = set()
    for name in candidates:
        if name in seen:
            continue
        seen.add(name)
        try:
            proc = subprocess.run(
                ["security", "find-generic-password", "-s", name, "-w"],
                capture_output=True,
                text=True,
                timeout=2,
                check=False,
            )
            if proc.returncode == 0 and proc.stdout.strip():
                return proc.stdout.strip()
        except Exception:
            pass
    return ""


@lru_cache(maxsize=64)
def _get_gsm_secret(secret_name: str, gcp_project: str) -> str:
    """Fetch secret from Google Secret Manager if GCP project is set."""
    if not gcp_project:
        return ""
    try:
        proc = subprocess.run(
            [
                "gcloud",
                "secrets",
                "versions",
                "access",
                "latest",
                f"--secret={secret_name}",
                f"--project={gcp_project}",
            ],
            capture_output=True,
            text=True,
            timeout=8,
            check=False,
        )
        if proc.returncode == 0 and proc.stdout.strip():
            return proc.stdout.strip()
    except Exception:
        pass
    return ""


def _overlay_secret_manager(cfg: Config) -> None:
    """Optionally overlay secrets from macOS Keychain or Google Secret Manager."""
    gcp_proj = os.environ.get("SEARCHSTACK_GCP_PROJECT", "") or cfg.gsc.gcp_project

    def get_sec(name: str) -> str:
        kc = _get_keychain_secret(name)
        if kc:
            return kc
        if gcp_proj:
            return _get_gsm_secret(name, gcp_proj)
        return ""

    if not cfg.dataforseo.login:
        cfg.dataforseo.login = get_sec("dataforseo-login")
    if not cfg.dataforseo.password:
        cfg.dataforseo.password = get_sec("dataforseo-password")

    secret_keys: dict[tuple[str, ...], str] = {
        ("openai", "api_key"): "openai-api-key",
        ("perplexity", "api_key"): "perplexity-api-key",
        ("anthropic", "api_key"): "anthropic-api-key",
        ("grok", "api_key"): "xai-api-key",
        ("gemini", "api_key"): "gemini-api-key",
        ("openrouter", "api_key"): "openrouter-api-key",
        ("plausible", "api_key"): "plausible-api-key",
        ("bing", "api_key"): "bing-webmaster-api-key",
    }

    for (section, attr), sec_name in secret_keys.items():
        obj = getattr(cfg, section)
        if not getattr(obj, attr):
            val = get_sec(sec_name)
            if val:
                setattr(obj, attr, val)


def _apply_defaults(cfg: Config) -> None:
    """Apply intelligent defaults based on domain if provided."""
    if cfg.domain:
        if not cfg.sitemap:
            cfg.sitemap = f"https://{cfg.domain}/sitemap.xml"
        if not cfg.gsc.site_url:
            cfg.gsc.site_url = f"sc-domain:{cfg.domain}"
        if not cfg.plausible.site_id:
            cfg.plausible.site_id = cfg.domain


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def load_config(config_path: Path | str | None = None) -> Config:
    """Load configuration from TOML file + environment variable overrides."""
    toml_path: Path | None = None

    if config_path is not None:
        p = Path(config_path).expanduser()
        if p.is_file():
            toml_path = p
        else:
            preset = _find_preset(str(config_path))
            if preset:
                toml_path = preset
            else:
                toml_path = _find_toml()
    else:
        toml_path = _find_toml()

    raw: dict[str, Any] = {}

    if toml_path is not None and toml_path.is_file():
        with open(toml_path, "rb") as f:
            raw = tomllib.load(f)

    cfg = _build_config(raw)
    _apply_defaults(cfg)
    _overlay_secret_manager(cfg)
    _overlay_env(cfg)
    return cfg


def dataforseo_auth(cfg: Config | None = None) -> str:
    """Return base64-encoded login:password for DataForSEO API auth."""
    if cfg is None:
        cfg = load_config()
    credentials = f"{cfg.dataforseo.login}:{cfg.dataforseo.password}"
    return base64.b64encode(credentials.encode()).decode()
