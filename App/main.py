# app/main.py
import logging
from fastapi import FastAPI
from app.routers.news import router as news_router
from app.mcp.server import get_mcp_router

# Configure basic logging early
logging.basicConfig(
    level=logging.getLevelName("INFO"),
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
)

app = FastAPI(title="Latest News Integrator API", version="1.0.0")

# Health check
@app.get("/health", tags=["health"])
async def health():
    return {"status": "ok"}

# Mount API routers
app.include_router(news_router, prefix="/api/news", tags=["news"])

# Mount MCP routes (tools)
app.include_router(get_mcp_router(), prefix="/mcp", tags=["mcp"])