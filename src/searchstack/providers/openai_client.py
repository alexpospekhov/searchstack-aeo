"""OpenAI (ChatGPT) citation-check provider.

Named openai_client.py to avoid conflict with the openai package.
All HTTP via urllib.request.
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
    payload = {
        "model": MODEL,
        "max_tokens": 500,
        "temperature": 0.3,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": query_text},
        ],
    }
    data = json.dumps(payload).encode()
    headers = {
        "Authorization": f"Bearer {config.openai.api_key}",
        "Content-Type": "application/json",
    }
    req = urllib.request.Request(API_URL, data=data, headers=headers, method="POST")

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            result = json.loads(resp.read())

        text = result["choices"][0]["message"]["content"]
        cited = domain.lower() in text.lower()
        return {
            "cited": cited,
            "text": text[:300],
            "model": MODEL,
            "error": None,
        }
    except urllib.error.HTTPError as exc:
        return {"cited": False, "text": "", "model": MODEL, "error": f"HTTP {exc.code}: {exc.reason}"}
    except Exception as exc:
        return {"cited": False, "text": "", "model": MODEL, "error": str(exc)}
