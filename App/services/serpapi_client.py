# app/services/serpapi_client.py
import logging
from typing import List, Dict, Optional
from serpapi import GoogleSearch
from app.config import get_settings

logger = logging.getLogger(__name__)

TIME_RANGE_TO_WHEN = {
    "24h": "1 day ago",
    "7d": "7 days ago",
    "30d": "30 days ago",
}

def search_latest_news(
    topic: str,
    max_results: int = 10,
    time_range: Optional[str] = "7d",
    language: Optional[str] = "en",
) -> List[Dict]:
    """
    Use SerpAPI's Google News engine to fetch latest news.
    Returns a list of dicts: {title, source, link/url, snippet, date, ...}
    """
    settings = get_settings()
    api_key = settings.SERPAPI_API_KEY

    params = {
        "engine": "google_news",
        "q": topic,
        "api_key": api_key,
        "num": max_results,
        "hl": language or "en",
    }

    if time_range:
        when = TIME_RANGE_TO_WHEN.get(time_range, "7 days ago")
        params["when"] = when

    logger.info("SerpAPI request: topic=%s max_results=%s time_range=%s", topic, max_results, time_range)
    search = GoogleSearch(params)
    results = search.get_dict()

    news_results = results.get("news_results", [])
    logger.info("SerpAPI returned %d articles", len(news_results))

    articles = []
    for item in news_results[:max_results]:
        articles.append({
            "title": item.get("title"),
            "source": (item.get("source") or {}).get("name") if isinstance(item.get("source"), dict) else item.get("source"),
            "url": item.get("link") or item.get("url"),
            "snippet": item.get("snippet") or item.get("description"),
            "published_at": item.get("date"),
        })
    return articles