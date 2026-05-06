"""Articles router — paginated list + single-article fetch."""
from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, HTTPException, Query, Request

router = APIRouter()


def _clean(doc: dict) -> dict:
    """Remove MongoDB _id and convert ObjectId to str."""
    doc.pop("_id", None)
    return doc


@router.get("")
def list_articles(
    request: Request,
    label: Literal["Fake", "Real", "all"] = "all",
    source: str | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    """
    Return a paginated list of scored articles.

    - **label**: filter by `Fake`, `Real`, or `all`
    - **source**: filter by source prefix (e.g. `newsapi:CNN`)
    - **page** / **page_size**: pagination
    """
    # --- Fallback mode (no MongoDB) ---
    if getattr(request.app.state, "use_fallback", False):
        fallback = request.app.state.fallback
        return fallback.get_articles(label=label, source=source, page=page, page_size=page_size)

    # --- Live MongoDB mode ---
    coll = request.app.state.db["articles_scored"]
    filt: dict = {}
    if label != "all":
        filt["label"] = label
    if source:
        filt["source"] = {"$regex": f"^{source}", "$options": "i"}

    total = coll.count_documents(filt)
    skip = (page - 1) * page_size
    docs = list(
        coll.find(filt, {"_id": 0})
            .sort("fetched_at", -1)
            .skip(skip)
            .limit(page_size)
    )
    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "pages": max(1, -(-total // page_size)),
        "articles": docs,
    }


@router.get("/{article_id}")
def get_article(article_id: str, request: Request):
    """Fetch a single article by its 24-char stable id."""
    # --- Fallback mode ---
    if getattr(request.app.state, "use_fallback", False):
        doc = request.app.state.fallback.get_article(article_id)
        if doc is None:
            raise HTTPException(status_code=404, detail="Article not found")
        return doc

    # --- Live MongoDB mode ---
    coll = request.app.state.db["articles_scored"]
    doc = coll.find_one({"id": article_id}, {"_id": 0})
    if doc is None:
        raise HTTPException(status_code=404, detail="Article not found")
    return doc
