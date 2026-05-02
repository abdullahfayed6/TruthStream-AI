"""
GPT Explanation & Summarization router.

POST /explain   — ask GPT *why* the article was classified as Fake/Real
POST /summarize — ask GPT for a concise summary of the article

Both endpoints stream responses via Server-Sent Events for snappy UX,
with a non-streaming fallback so Streamlit can use plain requests.
"""
from __future__ import annotations

import os

from fastapi import APIRouter, HTTPException
from openai import OpenAI, OpenAIError
from pydantic import BaseModel

router = APIRouter()


def _get_client() -> OpenAI:
    api_key = os.getenv("OPENAI_API_KEY", "")
    if not api_key or api_key.startswith("your_"):
        raise HTTPException(
            status_code=503,
            detail="OPENAI_API_KEY is not configured. Add it to your .env file.",
        )
    return OpenAI(api_key=api_key)


# ---------------------------------------------------------------------------
# Request / Response models
# ---------------------------------------------------------------------------

class ArticleInput(BaseModel):
    title:   str
    content: str = ""
    label:   str          # "Fake" or "Real"
    confidence: float = 0.0
    source: str = ""


class GPTResponse(BaseModel):
    text: str
    model: str
    tokens_used: int


# ---------------------------------------------------------------------------
# Explanation endpoint
# ---------------------------------------------------------------------------
EXPLAIN_SYSTEM = """You are an expert media-literacy analyst and fact-checker.
You will be given a news article (title + content) and a classification label (Fake or Real)
that was produced by a RoBERTa fake-news detection model.

Your task is to write a clear, 3-5 sentence explanation of WHY the article was classified
the way it was. Focus on:
- Specific language patterns, emotional or sensational wording
- Missing attributions or unnamed sources
- Claims that contradict established facts
- Writing style and journalistic standards

Be direct, neutral, and educational. Do NOT repeat the label verbatim at the start.
"""


@router.post("/explain", response_model=GPTResponse)
def explain(article: ArticleInput):
    """
    Use GPT to explain the classification of a news article.

    - **label**: the RoBERTa label (`Fake` or `Real`)
    - **confidence**: model confidence score (0–1)
    """
    client = _get_client()

    user_msg = (
        f"**Classification**: {article.label} (confidence: {article.confidence:.1%})\n\n"
        f"**Source**: {article.source or 'Unknown'}\n\n"
        f"**Title**: {article.title}\n\n"
        f"**Content** (first 800 chars):\n{article.content[:800]}"
    )

    try:
        resp = client.chat.completions.create(
            model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            messages=[
                {"role": "system", "content": EXPLAIN_SYSTEM},
                {"role": "user",   "content": user_msg},
            ],
            max_tokens=350,
            temperature=0.3,
        )
    except OpenAIError as exc:
        raise HTTPException(status_code=502, detail=f"OpenAI error: {exc}") from exc

    return GPTResponse(
        text=resp.choices[0].message.content.strip(),
        model=resp.model,
        tokens_used=resp.usage.total_tokens if resp.usage else 0,
    )


# ---------------------------------------------------------------------------
# Summarization endpoint
# ---------------------------------------------------------------------------
SUMMARIZE_SYSTEM = """You are a professional news editor.
Summarize the provided news article in exactly 2-3 concise sentences.
Focus on the key facts: Who, What, When, Where, Why.
Do not add any opinion or judgment. Write in the third person.
"""


@router.post("/summarize", response_model=GPTResponse)
def summarize(article: ArticleInput):
    """
    Use GPT to produce a concise factual summary of a news article.
    """
    client = _get_client()

    user_msg = (
        f"**Title**: {article.title}\n\n"
        f"**Content**:\n{article.content[:1500]}"
    )

    try:
        resp = client.chat.completions.create(
            model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            messages=[
                {"role": "system", "content": SUMMARIZE_SYSTEM},
                {"role": "user",   "content": user_msg},
            ],
            max_tokens=200,
            temperature=0.2,
        )
    except OpenAIError as exc:
        raise HTTPException(status_code=502, detail=f"OpenAI error: {exc}") from exc

    return GPTResponse(
        text=resp.choices[0].message.content.strip(),
        model=resp.model,
        tokens_used=resp.usage.total_tokens if resp.usage else 0,
    )
