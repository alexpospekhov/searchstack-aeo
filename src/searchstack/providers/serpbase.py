"""Serpbase provider for Google SERP data."""
import os
import requests


def search_organic(query: str, location: str = "", language: str = "", num: int = 10) -> list:
    """Fetch organic search results from Serpbase API."""
    api_key = os.getenv("SERPBASE_API_KEY")
    if not api_key:
        raise ValueError("Serpbase API key not set. Set SERPBASE_API_KEY env var or add [serpbase] api_key to .searchstack.toml")

    url = "https://api.serpbase.dev/google/search"
    params = {
        "q": query,
        "api_key": api_key,
        "num": num,
    }
    if location:
        params["location"] = location
    if language:
        params["language"] = language

    response = requests.get(url, params=params)
    response.raise_for_status()
    data = response.json()

    results = []
    for item in data.get("organic_results", []):
        results.append({
            "position": item.get("position"),
            "title": item.get("title", ""),
            "link": item.get("link", ""),
            "snippet": item.get("snippet", ""),
        })
    return results
