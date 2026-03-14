# app/routers/news.py
import logging
from datetime import datetime
from fastapi import APIRouter, HTTPException
from app.models import NewsRequest, NewsResponse, Article
from app.services.agents import SearchAgent, SummaryAgent

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/summary", response_model=NewsResponse)
async def summarize_news(payload: NewsRequest):
    """
    Orchestrates:
      - SearchAgent via MCP tool capability (internally called here)
      - SummaryAgent via Azure OpenAI
    Returns combined result.
    """
    logger.info("Incoming request: topic=%s max_results=%s time_range=%s lang=%s",
                payload.topic, payload.max_results, payload.time_range, payload.language)

    try:
        articles = await SearchAgent.search(
            topic=payload.topic,
            max_results=payload.max_results,
            time_range=payload.time_range,
            language=payload.language,
        )
    except Exception as e:
        logger.exception("SearchAgent failed")
        raise HTTPException(status_code=502, detail=f"Search error: {e}")

    if not articles:
        raise HTTPException(status_code=404, detail="No articles found for the given topic/time_range.")

    try:
        summary, bullets, follow_ups = await SummaryAgent.summarize(payload.topic, articles)
    except Exception as e:
        logger.exception("SummaryAgent failed")
        raise HTTPException(status_code=502, detail=f"LLM summarization error: {e}")

    response = NewsResponse(
        topic=payload.topic,
        articles=[Article(**a) for a in articles],
        summary=summary,
        bullets=bullets,
        follow_ups=follow_ups,
        generated_at=datetime.utcnow(),
        metadata={
            "article_count": len(articles),
            "time_range": payload.time_range,
            "language": payload.language,
        },
    )
    return response