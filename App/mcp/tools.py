# app/mcp/tools.py
from typing import Any, Dict
from pydantic import BaseModel, Field
from app.services.serpapi_client import search_latest_news

class NewsSearchInput(BaseModel):
    topic: str = Field(..., description="Topic or query to search")
    max_results: int = Field(10, ge=1, le=20)
    time_range: str | None = Field(default="7d", description="One of '24h', '7d', '30d'")
    language: str | None = Field(default="en")

def news_search_tool(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    MCP Tool: news_search
    """
    args = NewsSearchInput(**payload)
    articles = search_latest_news(
        topic=args.topic,
        max_results=args.max_results,
        time_range=args.time_range,
        language=args.language,
    )
    return {"articles": articles}