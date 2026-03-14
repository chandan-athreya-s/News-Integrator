# app/models.py
from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime

class NewsRequest(BaseModel):
    topic: str = Field(..., description="Topic or query to search the latest news for")
    max_results: int = Field(10, ge=1, le=20, description="Max number of articles to retrieve")
    time_range: Optional[str] = Field(
        default="7d",
        description="Time window: '24h' | '7d' | '30d'",
    )
    language: Optional[str] = Field(default="en", description="Language code, e.g., 'en'")

class Article(BaseModel):
    title: str
    source: Optional[str] = None
    url: str
    snippet: Optional[str] = None
    published_at: Optional[str] = None  # ISO or human readable date

class NewsResponse(BaseModel):
    topic: str
    articles: List[Article]
    summary: str
    bullets: List[str]
    follow_ups: List[str]
    generated_at: datetime
    metadata: dict