# app/services/azure_llm.py
import logging
from typing import List, Tuple
from openai import AzureOpenAI
from app.config import get_settings

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are an assistant that synthesizes the latest news from multiple articles.

Guidelines:
- Be concise, neutral, and balanced. Avoid sensational language.
- Do not invent facts not supported by the provided articles.
- Acknowledge uncertainties and conflicting reports when present.
- Include context only if it is necessary to understand the story.
- Prefer paragraph summary followed by key bullet points and suggested follow-up angles.
"""

def build_user_prompt(topic: str, articles: List[dict]) -> str:
    lines = [f"Topic: {topic}", "", "Here are the articles:"]
    for idx, a in enumerate(articles, start=1):
        lines.append(
            f"{idx}. Title: {a.get('title')}\n"
            f"   Source: {a.get('source')}\n"
            f"   URL: {a.get('url')}\n"
            f"   Published: {a.get('published_at')}\n"
            f"   Snippet: {a.get('snippet')}"
        )
    lines.append("")
    lines.append("Please produce:")
    lines.append("- A concise multi-paragraph summary (3-5 short paragraphs).")
    lines.append("- 5-8 key bullet points.")
    lines.append("- 3-5 suggested follow-up questions or angles.")
    return "\n".join(lines)

def get_azure_client() -> AzureOpenAI:
    settings = get_settings()
    client = AzureOpenAI(
        azure_endpoint=settings.AZURE_OPENAI_ENDPOINT,
        api_key=settings.AZURE_OPENAI_API_KEY,
        api_version=settings.AZURE_OPENAI_API_VERSION,
    )
    return client

def summarize_with_azure_llm(topic: str, articles: List[dict]) -> Tuple[str, List[str], List[str]]:
    """
    Calls Azure OpenAI chat completion to generate a summary, bullets, and follow-up questions.
    Returns (summary, bullets, follow_ups).
    """
    settings = get_settings()
    client = get_azure_client()

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": build_user_prompt(topic, articles)},
    ]

    logger.info("Calling Azure OpenAI deployment=%s", settings.AZURE_OPENAI_DEPLOYMENT)

    resp = client.chat.completions.create(
        model=settings.AZURE_OPENAI_DEPLOYMENT,
        messages=messages,
        temperature=0.2,
        max_tokens=900,
    )

    content = (resp.choices[0].message.content or "").strip()

    # Simple parsing heuristic:
    # Expect the model to produce sections separated by headings or list markers.
    # We'll look for 'Key bullet points' and 'Follow-up questions' style markers.
    summary, bullets, followups = _split_sections(content)
    return summary, bullets, followups

def _split_sections(text: str) -> tuple[str, List[str], List[str]]:
    """
    Very simple parser: try to split into summary / bullets / follow-ups by scanning for common markers.
    If not found, treat the whole response as summary and produce empty bullets/follow-ups.
    """
    lower = text.lower()
    bullets_markers = ["key bullet points", "key points", "highlights", "bullets:"]
    follow_markers = ["follow-up", "follow ups", "followups", "questions", "angles"]

    # naive split
    bullets_start = None
    follow_start = None

    for mk in bullets_markers:
        idx = lower.find(mk)
        if idx != -1:
            bullets_start = idx
            break

    for mk in follow_markers:
        idx = lower.find(mk)
        if idx != -1:
            follow_start = idx
            break

    if bullets_start is None and follow_start is None:
        return text, [], []

    # Ensure order
    markers = sorted([("bullets", bullets_start), ("follow", follow_start)], key=lambda x: (x[1] is None, x[1] if x[1] is not None else 10**9))
    parts = []
    last = 0
    for name, pos in markers:
        if pos is not None:
            parts.append(text[last:pos].strip())
            last = pos
    parts.append(text[last:].strip())

    # Now try to identify which is which
    summary = parts[0] if parts else text
    bullets_text = ""
    follow_text = ""

    if bullets_start is not None and follow_start is not None:
        if bullets_start < follow_start:
            bullets_text = text[bullets_start:follow_start]
            follow_text = text[follow_start:]
        else:
            follow_text = text[follow_start:bullets_start]
            bullets_text = text[bullets_start:]
    elif bullets_start is not None:
        bullets_text = text[bullets_start:]
    elif follow_start is not None:
        follow_text = text[follow_start:]

    def to_list(block: str) -> List[str]:
        lines = [ln.strip("-•* \t") for ln in block.splitlines() if ln.strip()]
        # drop heading-like first line if it contains the word "bullet" or "follow"
        if lines and any(k in lines[0].lower() for k in ["bullet", "follow", "question", "angle", "highlight", "key points"]):
            lines = lines[1:]
        # only keep reasonable bullet-like lines
        return [ln for ln in lines if len(ln) > 2]

    bullets = to_list(bullets_text)
    followups = to_list(follow_text)
    return summary.strip(), bullets[:10], followups[:10]