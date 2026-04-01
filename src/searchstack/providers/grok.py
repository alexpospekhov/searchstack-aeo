"""xAI Grok API provider — AEO citation check."""
from __future__ import annotations

import json
import urllib.request
import urllib.error

from searchstack.config import Config


def check_citation(config: Config, query_text: str, domain: str) -> dict:
    """Ask Grok and check if response mentions domain.

    Returns: {"cited": bool, "text": str, "model": str, "error": str|None}
    """
    api_key = config.grok.api_key
    if not api_key:
        return {"error": "No XAI_API_KEY"}

    body = json.dumps({
        "model": "grok-3-mini",
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are a helpful assistant. When answering, cite specific "
                    "websites and tools by name and URL when relevant."
                ),
            },
            {"role": "user", "content": query_text},
        ],
        "max_tokens": 500,
        "temperature": 0.3,
    }).encode()

    req = urllib.request.Request(
        "https://api.x.ai/v1/chat/completions",
        method="POST",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        data=body,
    )

    try:
        resp = json.loads(urllib.request.urlopen(req, timeout=30).read())
        text = resp["choices"][0]["message"]["content"]
        cited = domain.lower() in text.lower()
        return {"cited": cited, "text": text[:300], "model": "grok-3-mini"}
    except urllib.error.HTTPError as e:
        return {"error": f"HTTP {e.code}: {e.read().decode()[:100]}"}
    except Exception as e:
        return {"error": str(e)}
