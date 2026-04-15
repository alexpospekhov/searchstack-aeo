"""OpenAI (ChatGPT) citation-check provider.

Named openai_client.py to avoid conflict with the openai package.
All HTTP via urllib.request.

When ``config.openrouter.api_key`` is set, the request is routed through
OpenRouter's OpenAI-compatible endpoint using ``config.openrouter.chatgpt_model``
instead of the native OpenAI API. This lets a user run every AI provider
through a single OpenRouter key for unified billing.
"""

from __future__ import annotations

import json
import urllib.request
import urllib.error

from searchstack.config import Config

API_URL = "https://api.openai.com/v1/chat/completions"
MODEL = "gpt-4o-mini"
SYSTEM_PROMPT = (
    "You are a helpful assistant. When answering, cite specific websites "
    "and tools by name and URL when relevant."
)


def check_citation(config: Config, query_text: str, domain: str) -> dict[str, object]:
    """Ask ChatGPT a query and check whether the response mentions *domain*.

    Returns:
        {"cited": bool, "text": str (first 300 chars), "model": str, "error": str | None}
    """
    if config.openrouter.api_key:
        api_url = f"{config.openrouter.base_url.rstrip('/')}/chat/completions"
        model = config.openrouter.chatgpt_model
        api_key = config.openrouter.api_key
    else:
        api_url = API_URL
        model = MODEL
        api_key = config.openai.api_key

    payload = {
        "model": model,
        "max_tokens": 500,
        "temperature": 0.3,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": query_text},
        ],
    }
    data = json.dumps(payload).encode()
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    req = urllib.request.Request(api_url, data=data, headers=headers, method="POST")

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            result = json.loads(resp.read())

        text = result["choices"][0]["message"]["content"]
        cited = domain.lower() in text.lower()
        return {
            "cited": cited,
            "text": text[:300],
            "model": model,
            "error": None,
        }
    except urllib.error.HTTPError as exc:
        return {"cited": False, "text": "", "model": model, "error": f"HTTP {exc.code}: {exc.reason}"}
    except Exception as exc:
        return {"cited": False, "text": "", "model": model, "error": str(exc)}
