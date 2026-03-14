# tests/test_news_flow.py
import pytest
from fastapi.testclient import TestClient
from app.main import app

# Monkeypatch the agents to avoid external calls in test
@pytest.fixture(autouse=True)
def patch_agents(monkeypatch):
    async def fake_search(topic, max_results, time_range, language):
        return [
            {
                "title": "Sample Article A",
                "source": "Example News",
                "url": "https://example.com/a",
                "snippet": "A snippet",
                "published_at": "1 hour ago",
            },
            {
                "title": "Sample Article B",
                "source": "Another Source",
                "url": "https://example.com/b",
                "snippet": "B snippet",
                "published_at": "2 hours ago",
            },
        ][:max_results]

    async def fake_summarize(topic, articles):
        return (
            "This is a summary.",
            ["Point 1", "Point 2"],
            ["Follow-up 1", "Follow-up 2"],
        )

    from app.services import agents
    monkeypatch.setattr(agents.SearchAgent, "search", staticmethod(fake_search))
    monkeypatch.setattr(agents.SummaryAgent, "summarize", staticmethod(fake_summarize))
    yield

def test_summary_endpoint():
    client = TestClient(app)
    payload = {"topic": "test topic", "max_results": 2, "time_range": "7d", "language": "en"}
    res = client.post("/api/news/summary", json=payload)
    assert res.status_code == 200, res.text
    data = res.json()

    assert data["topic"] == "test topic"
    assert len(data["articles"]) == 2
    assert "summary" in data and data["summary"]
    assert "bullets" in data and len(data["bullets"]) == 2
    assert "follow_ups" in data and len(data["follow_ups"]) == 2
    assert "generated_at" in data
    assert data["metadata"]["article_count"] == 2