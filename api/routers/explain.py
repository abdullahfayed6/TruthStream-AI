"""
GPT Explanation & Summarization router.

POST /explain   — ask GPT *why* the article was classified as Fake/Real
POST /summarize — ask GPT for a concise summary of the article

If OPENAI_API_KEY is not configured, returns a demo/template response
so the frontend can still demonstrate the full flow.
"""
from __future__ import annotations

import os

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()


def _get_client():
    """Try to create an OpenAI client. Returns None if unavailable."""
    api_key = os.getenv("OPENAI_API_KEY", "")
    if not api_key or api_key.startswith("your_"):
        return None
    try:
        from openai import OpenAI
        return OpenAI(api_key=api_key)
    except Exception:
        return None



class ArticleInput(BaseModel):
    title:   str
    content: str = ""
    label:   str
    confidence: float = 0.0
    source: str = ""


class GPTResponse(BaseModel):
    text: str
    model: str
    tokens_used: int


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


def _fallback_explanation(article: ArticleInput) -> GPTResponse:
    """Generate a template explanation when GPT is unavailable."""
    if article.label.lower() == "fake":
        text = (
            f"**Classification: {article.label} ({article.confidence:.0%} confidence)**\n\n"
            f"This article was flagged by the RoBERTa model based on several indicators:\n\n"
            f"1. **Sensationalist Language**: The headline uses emotionally charged phrasing "
            f"commonly associated with misinformation.\n\n"
            f"2. **Source Credibility**: The source \"{article.source}\" has patterns consistent "
            f"with unreliable content distribution.\n\n"
            f"3. **Unverified Claims**: The article makes extraordinary claims without providing "
            f"verifiable evidence or credible citations.\n\n"
            f"4. **Missing Attribution**: Key claims rely on unnamed or anonymous sources.\n\n"
            f"**Recommendation**: Cross-reference with established news sources before sharing."
        )
    else:
        text = (
            f"**Classification: {article.label} ({article.confidence:.0%} confidence)**\n\n"
            f"This article was classified as genuine based on several factors:\n\n"
            f"1. **Professional Tone**: The writing follows standard journalistic practices "
            f"with objective, measured language.\n\n"
            f"2. **Source Attribution**: Claims are attributed to named, verifiable sources.\n\n"
            f"3. **Factual Consistency**: The content aligns with established facts and "
            f"can be corroborated through independent sources.\n\n"
            f"4. **Source Credibility**: \"{article.source}\" is recognized as a reliable "
            f"news organization."
        )
    return GPTResponse(text=text, model="demo-fallback", tokens_used=0)


def _fallback_summary(article: ArticleInput) -> GPTResponse:
    """Generate a template summary when GPT is unavailable."""
    content_preview = article.content[:200] if article.content else article.title
    text = (
        f"This article titled \"{article.title}\" was published by {article.source or 'an unknown source'}. "
        f"The RoBERTa classification model determined it to be {article.label} "
        f"with {article.confidence:.0%} confidence. "
        f"{content_preview}"
    )
    return GPTResponse(text=text, model="demo-fallback", tokens_used=0)


@router.post("/explain", response_model=GPTResponse)
def explain(article: ArticleInput):
    """
    Use GPT to explain the classification of a news article.
    Falls back to a template response if OpenAI is not configured.
    """
    client = _get_client()
    if client is None:
        return _fallback_explanation(article)

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
    except Exception:
        return _fallback_explanation(article)

    return GPTResponse(
        text=resp.choices[0].message.content.strip(),
        model=resp.model,
        tokens_used=resp.usage.total_tokens if resp.usage else 0,
    )


SUMMARIZE_SYSTEM = """You are a professional news editor.
Summarize the provided news article in exactly 2-3 concise sentences.
Focus on the key facts: Who, What, When, Where, Why.
Do not add any opinion or judgment. Write in the third person.
"""


@router.post("/summarize", response_model=GPTResponse)
def summarize(article: ArticleInput):
    """
    Use GPT to produce a concise factual summary of a news article.
    Falls back to a template response if OpenAI is not configured.
    """
    client = _get_client()
    if client is None:
        return _fallback_summary(article)

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
    except Exception:
        return _fallback_summary(article)

    return GPTResponse(
        text=resp.choices[0].message.content.strip(),
        model=resp.model,
        tokens_used=resp.usage.total_tokens if resp.usage else 0,
    )
