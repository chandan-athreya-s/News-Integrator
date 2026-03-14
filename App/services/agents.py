# app/services/agents.py
import time
import asyncio
import logging
from typing import Dict, Tuple, List
from app.services.serpapi_client import search_latest_news
from app.services.azure_llm import summarize_with_azure_llm
from app.config import get_settings

logger = logging.getLogger(__name__)

class TTLCache:
    def __init__(self, ttl_seconds: int = 300):
        self.ttl = ttl_seconds
        self._store: Dict[Tuple, Tuple[float, object]] = {}

    def get(self, key: Tuple):
        entry = self._store.get(key)
        if not entry:
            return None
        exp, val = entry
        if time.time() > exp:
            self._store.pop(key, None)
            return None
        return val

    def set(self, key: Tuple, value: object):
        self._store[key] = (time.time() + self.ttl, value)

# Instantiate a small cache
_cache = TTLCache(ttl_seconds=get_settings().CACHE_TTL_SECONDS)

class SearchAgent:
    """
    Wraps the capability of searching news via SerpAPI.
    Exposed as an MCP tool elsewhere, but callable directly too.
    """
    @staticmethod
    async def search(topic: str, max_results: int, time_range: str | None, language: str | None) -> List[dict]:
        key = ("search", topic.strip().lower(), max_results, time_range or "", language or "")
        cached = _cache.get(key)
        if cached is not None:
            logger.info("SearchAgent cache hit for %s", key)
            return cached

        logger.info("SearchAgent executing search for topic=%s", topic)
        # Run blocking call in a thread to avoid blocking event loop
        articles = await asyncio.to_thread(search_latest_news, topic, max_results, time_range, language)
        _cache.set(key, articles)
        return articles

class SummaryAgent:
    """
    Consumes search results and calls Azure OpenAI to generate a synthesis.
    """
    @staticmethod
    async def summarize(topic: str, articles: List[dict]):
        key = ("summary", topic.strip().lower(), tuple(a.get("url") for a in articles))
        cached = _cache.get(key)
        if cached is not None:
            logger.info("SummaryAgent cache hit for %s", key)
            return cached

        logger.info("SummaryAgent calling Azure OpenAI for topic=%s with %d articles", topic, len(articles))
        summary, bullets, followups = await asyncio.to_thread(summarize_with_azure_llm, topic, articles)
        _cache.set(key, (summary, bullets, followups))
        return summary, bullets, followups