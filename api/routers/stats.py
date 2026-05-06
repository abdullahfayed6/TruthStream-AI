"""Stats router — counts, percentages, timeline."""
from __future__ import annotations

from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Request

router = APIRouter()


@router.get("")
def stats(request: Request):
    """
    Live statistics from MongoDB (or fallback demo store):
    - Total articles, Fake count, Real count
    - Top sources (by volume)
    - Fake-rate percentage
    """
    if getattr(request.app.state, "use_fallback", False):
        return request.app.state.fallback.get_stats()

    coll = request.app.state.db["articles_scored"]
    total   = coll.count_documents({})
    fake    = coll.count_documents({"label": "Fake"})
    real    = coll.count_documents({"label": "Real"})

    pipeline_sources = [
        {"$group": {"_id": "$source", "count": {"$sum": 1}}},
        {"$sort":  {"count": -1}},
        {"$limit": 10},
        {"$project": {"source": "$_id", "count": 1, "_id": 0}},
    ]
    top_sources = list(coll.aggregate(pipeline_sources))

    pipeline_fake_rate = [
        {"$group": {
            "_id": "$source",
            "total":     {"$sum": 1},
            "fake_count": {"$sum": {"$cond": [{"$eq": ["$label", "Fake"]}, 1, 0]}},
        }},
        {"$match": {"total": {"$gte": 3}}},
        {"$addFields": {"fake_rate": {"$divide": ["$fake_count", "$total"]}}},
        {"$sort": {"fake_rate": -1}},
        {"$limit": 10},
        {"$project": {"source": "$_id", "total": 1, "fake_count": 1, "fake_rate": 1, "_id": 0}},
    ]
    fake_rate_by_source = list(coll.aggregate(pipeline_fake_rate))

    pipeline_breakdown = [
        {"$group": {
            "_id": "$source",
            "total": {"$sum": 1},
            "fake":  {"$sum": {"$cond": [{"$eq": ["$label", "Fake"]}, 1, 0]}},
            "real":  {"$sum": {"$cond": [{"$eq": ["$label", "Real"]}, 1, 0]}},
        }},
        {"$sort": {"total": -1}},
        {"$limit": 10},
        {"$project": {"source": "$_id", "total": 1, "fake": 1, "real": 1, "_id": 0}},
    ]
    source_breakdown = list(coll.aggregate(pipeline_breakdown))

    return {
        "total": total,
        "fake":  fake,
        "real":  real,
        "fake_pct": round(fake / total * 100, 1) if total else 0,
        "real_pct": round(real / total * 100, 1) if total else 0,
        "top_sources": top_sources,
        "fake_rate_by_source": fake_rate_by_source,
        "source_breakdown": source_breakdown,
    }


@router.get("/timeline")
def timeline(request: Request, hours: int = 24):
    """
    Articles scored per hour for the last `hours` hours.
    Returns a list of {hour, fake, real, total} dicts.
    """
    if getattr(request.app.state, "use_fallback", False):
        return request.app.state.fallback.get_timeline(hours)

    coll = request.app.state.db["articles_scored"]
    since = datetime.now(UTC) - timedelta(hours=hours)

    pipeline = [
        {"$match": {"scored_at": {"$gte": since.isoformat()}}},
        {"$addFields": {
            "hour": {
                "$dateToString": {
                    "format": "%Y-%m-%dT%H:00",
                    "date": {"$dateFromString": {"dateString": "$scored_at"}},
                }
            }
        }},
        {"$group": {
            "_id":   {"hour": "$hour", "label": "$label"},
            "count": {"$sum": 1},
        }},
        {"$sort": {"_id.hour": 1}},
    ]
    raw = list(coll.aggregate(pipeline))

    pivot: dict[str, dict] = {}
    for r in raw:
        h = r["_id"]["hour"]
        label = r["_id"]["label"]
        if h not in pivot:
            pivot[h] = {"hour": h, "fake": 0, "real": 0}
        pivot[h][label.lower()] = r["count"]

    result = sorted(pivot.values(), key=lambda x: x["hour"])
    for row in result:
        row["total"] = row["fake"] + row["real"]

    return result
