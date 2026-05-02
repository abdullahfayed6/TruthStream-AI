"""Stats router — counts, percentages, timeline."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Request

router = APIRouter()


@router.get("")
def stats(request: Request):
    """
    Live statistics from MongoDB:
    - Total articles, Fake count, Real count
    - Top sources (by volume)
    - Fake-rate percentage
    """
    coll = request.app.state.db["articles_scored"]
    total   = coll.count_documents({})
    fake    = coll.count_documents({"label": "Fake"})
    real    = coll.count_documents({"label": "Real"})

    # Top 10 sources by article count
    pipeline_sources = [
        {"$group": {"_id": "$source", "count": {"$sum": 1}}},
        {"$sort":  {"count": -1}},
        {"$limit": 10},
        {"$project": {"source": "$_id", "count": 1, "_id": 0}},
    ]
    top_sources = list(coll.aggregate(pipeline_sources))

    # Top 10 sources with highest fake rate
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

    return {
        "total": total,
        "fake":  fake,
        "real":  real,
        "fake_pct": round(fake / total * 100, 1) if total else 0,
        "real_pct": round(real / total * 100, 1) if total else 0,
        "top_sources": top_sources,
        "fake_rate_by_source": fake_rate_by_source,
    }


@router.get("/timeline")
def timeline(request: Request, hours: int = 24):
    """
    Articles scored per hour for the last `hours` hours.
    Returns a list of {hour, fake, real, total} dicts.
    """
    coll = request.app.state.db["articles_scored"]
    since = datetime.now(timezone.utc) - timedelta(hours=hours)

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

    # Pivot into {hour -> {fake, real}}
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
