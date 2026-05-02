"""
TruthStream AI — FastAPI Backend
=================================
Connects MongoDB (scored articles) + OpenAI GPT for explanation & summarization.

Endpoints:
  GET  /articles           — paginated list with filters
  GET  /articles/{id}      — single article
  GET  /stats              — live counts (total, fake, real, by source)
  GET  /stats/timeline     — articles-per-hour for the last 24h
  POST /explain            — GPT explanation of why article is Fake/Real
  POST /summarize          — GPT one-paragraph summary of article content
  GET  /health             — liveness probe
"""
from __future__ import annotations

import os
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pymongo import MongoClient

from api.routers import articles, explain, stats

load_dotenv()


# ---------------------------------------------------------------------------
# DB singleton
# ---------------------------------------------------------------------------
_mongo_client: MongoClient | None = None


def get_db():
    global _mongo_client
    if _mongo_client is None:
        uri = os.getenv("MONGO_URI_EXTERNAL", "mongodb://localhost:27017")
        _mongo_client = MongoClient(uri, serverSelectionTimeoutMS=5000)
    return _mongo_client["truthstream"]


# ---------------------------------------------------------------------------
# App lifecycle
# ---------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: verify DB connection
    db = get_db()
    db.command("ping")
    print("[OK] MongoDB connected")
    app.state.db = db
    yield
    # Shutdown
    if _mongo_client:
        _mongo_client.close()
    print("MongoDB connection closed")


app = FastAPI(
    title="TruthStream AI",
    description="Real-time fake-news detection API powered by RoBERTa + GPT",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(articles.router, prefix="/articles", tags=["Articles"])
app.include_router(stats.router,    prefix="/stats",    tags=["Statistics"])
app.include_router(explain.router,  prefix="",          tags=["GPT"])


@app.get("/health", tags=["System"])
def health():
    return {"status": "ok", "service": "TruthStream AI API"}
