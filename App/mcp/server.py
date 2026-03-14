# app/mcp/server.py
import logging
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Dict, Any, List
from app.mcp.tools import news_search_tool

logger = logging.getLogger(__name__)

# Minimal MCP-like shape: list tools and call tools over HTTP.
# If you have the real fastmcp server, you can swap this easily.

class ToolDef(BaseModel):
    name: str
    description: str
    input_schema: Dict[str, Any] = Field(default_factory=dict)

class ToolCallRequest(BaseModel):
    name: str
    arguments: Dict[str, Any] = Field(default_factory=dict)

class ToolCallResponse(BaseModel):
    ok: bool
    result: Dict[str, Any] | None = None
    error: str | None = None

def get_mcp_router() -> APIRouter:
    router = APIRouter()

    @router.get("/tools", response_model=List[ToolDef])
    async def list_tools():
        """
        Lists available MCP tools.
        """
        return [
            ToolDef(
                name="news_search",
                description="Search latest news via SerpAPI (Google News).",
                input_schema={
                    "type": "object",
                    "properties": {
                        "topic": {"type": "string"},
                        "max_results": {"type": "integer", "minimum": 1, "maximum": 20},
                        "time_range": {"type": "string", "enum": ["24h", "7d", "30d"]},
                        "language": {"type": "string"},
                    },
                    "required": ["topic"],
                }
            )
        ]

    @router.post("/call", response_model=ToolCallResponse)
    async def call_tool(req: ToolCallRequest):
        """
        Calls a tool by name with provided arguments.
        """
        try:
            if req.name == "news_search":
                result = await _call_sync_tool_in_thread(news_search_tool, req.arguments)
                return ToolCallResponse(ok=True, result=result)
            raise HTTPException(status_code=404, detail=f"Tool not found: {req.name}")
        except Exception as e:
            logger.exception("Error calling tool %s", req.name)
            return ToolCallResponse(ok=False, error=str(e))

    return router

# Helper to run sync functions in a thread in async context
import asyncio
async def _call_sync_tool_in_thread(fn, *args, **kwargs):
    return await asyncio.to_thread(fn, *args, **kwargs)