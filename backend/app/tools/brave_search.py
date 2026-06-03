from typing import Any

import httpx

from app.config import settings

BRAVE_API_URL = "https://api.search.brave.com/res/v1/web/search"


async def brave_search(query: str, count: int = 10) -> list[dict[str, Any]]:
    """Devuelve lista de resultados con title, url, description, y discussions si las hay."""
    if not settings.BRAVE_API_KEY:
        return []

    headers = {
        "Accept": "application/json",
        "Accept-Encoding": "gzip",
        "X-Subscription-Token": settings.BRAVE_API_KEY,
    }
    params = {"q": query, "count": count, "search_lang": "es", "extra_snippets": "true"}

    async with httpx.AsyncClient(timeout=15) as client:
        response = await client.get(BRAVE_API_URL, headers=headers, params=params)
        response.raise_for_status()
        data = response.json()

    results: list[dict[str, Any]] = []

    for r in data.get("web", {}).get("results", []):
        results.append({
            "type": "web",
            "title": r.get("title", ""),
            "url": r.get("url", ""),
            "description": r.get("description", ""),
            "extra_snippets": r.get("extra_snippets", []),
        })

    for r in data.get("discussions", {}).get("results", []):
        results.append({
            "type": "discussion",
            "title": r.get("title", ""),
            "url": r.get("url", ""),
            "description": r.get("description", ""),
            "extra_snippets": [],
        })

    return results
