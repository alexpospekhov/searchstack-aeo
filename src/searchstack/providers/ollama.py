"""Ollama / local LLM provider — AEO citation check with any OpenAI-compatible API.

Works with:
  - Ollama (localhost:11434)
  - LM Studio (localhost:1234)
  - vLLM, llama.cpp server, LocalAI
  - Any OpenAI-compatible endpoint

Config:
  [ollama]
  base_url = "http://localhost:11434/v1"   # Ollama default
  model = "qwen3:8b"                       # any model you have pulled
  api_key = ""                             # optional, some servers need it
"""

from __future__ import annotations

import json
import urllib.request
import urllib.error

from searchstack.config import Config


def check_citation(config: Config, query_text: str, domain: str) -> dict:
    """Ask a local LLM and check if response mentions domain.

    Returns: {"cited": bool, "text": str, "model": str, "error": str|None}
    """
    base_url = config.ollama.base_url
    model = config.ollama.model
    api_key = config.ollama.api_key

    if not base_url or not model:
        return {"error": "No [ollama] config. Set base_url and model in .searchstack.toml"}

    body = json.dumps({
        "model": model,
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
        "stream": False,
    }).encode()

    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    # Ensure URL ends with /chat/completions
    url = base_url.rstrip("/")
    if not url.endswith("/chat/completions"):
        url = f"{url}/chat/completions"

    req = urllib.request.Request(url, method="POST", headers=headers, data=body)

    try:
        resp = json.loads(urllib.request.urlopen(req, timeout=120).read())
        text = resp["choices"][0]["message"]["content"]
        cited = domain.lower() in text.lower()
        return {"cited": cited, "text": text[:300], "model": model}
    except urllib.error.URLError as e:
        return {"error": f"Cannot connect to {base_url}: {e.reason}. Is Ollama running?"}
    except Exception as e:
        return {"error": str(e)}
