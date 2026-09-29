"""Extract People Also Ask (PAA) questions from SERP for content ideation."""

from __future__ import annotations

from searchstack.config import Config
from searchstack.providers.dataforseo import (
    api_request,
    get_language_code,
    get_location_code,
)


def run(config: Config, *args: str) -> None:
    """Fetch People Also Ask questions for a query."""
    if not config.dataforseo.login or not config.dataforseo.password:
        print("DataForSEO not configured. Set [dataforseo] in .searchstack.toml")
        return

    query = " ".join(args) if args else ""
    if not query:
        print("Usage: searchstack questions \"keyword or topic\"")
        return

    print(f"\nExtracting People Also Ask for: \"{query}\"...")

    body = [
        {
            "keyword": query,
            "location_code": get_location_code(config),
            "language_code": get_language_code(config),
            "depth": 10,
            "device": "desktop",
        }
    ]

    data = api_request(config, "serp/google/organic/live/advanced", body)
    if "error" in data:
        print(f"API error: {data['error']}")
        return

    tasks = data.get("tasks", [])
    if not tasks or not tasks[0].get("result"):
        print("No results returned.")
        return

    items = tasks[0]["result"][0].get("items", []) or []
    paa_items = [i for i in items if i.get("type") == "people_also_ask"]

    questions: list[dict[str, str]] = []
    for block in paa_items:
        for item in block.get("items", []) or []:
            title = item.get("title", "")
            snippet = item.get("description", "") or item.get("snippet", "")
            domain = item.get("domain", "")
            url = item.get("url", "")
            if title:
                questions.append({
                    "question": title,
                    "snippet": snippet,
                    "domain": domain,
                    "url": url,
                })

    if not questions:
        print(f"No 'People Also Ask' questions found on the SERP for \"{query}\".")
        return

    print(f"\nFound {len(questions)} People Also Ask questions:\n")
    for idx, q in enumerate(questions, 1):
        print(f"  {idx}. {q['question']}")
        if q['domain']:
            print(f"     Answered by: {q['domain']}")
        if q['snippet']:
            snippet_preview = q['snippet'].replace("\n", " ")[:100]
            print(f"     Snippet: \"{snippet_preview}...\"")
        print()
