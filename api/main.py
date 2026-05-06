"""
TruthStream AI — FastAPI Backend
=================================
Connects MongoDB (scored articles) + OpenAI GPT for explanation & summarization.

If MongoDB is unreachable, the server starts in **demo mode** with an
in-memory data store so the frontend can still be developed / demonstrated.

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

import logging
import os
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.fallback_store import FallbackStore
from api.live_ingestion import ingestion_loop
from api.routers import articles, explain, stats, websocket

load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")


_mongo_client = None
_use_fallback = False


def get_db():
    """Return a MongoDB database or None if unreachable."""
    global _mongo_client
    if _mongo_client is None:
        try:
            from pymongo import MongoClient
            uri = os.getenv("MONGO_URI_EXTERNAL", "mongodb://localhost:27017")
            _mongo_client = MongoClient(uri, serverSelectionTimeoutMS=3000)
            _mongo_client.admin.command("ping")
        except Exception:
            _mongo_client = None
            return None
    try:
        return _mongo_client["truthstream"]
    except Exception:
        return None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _use_fallback

    db = get_db()
    if db is not None:
        try:
            db.command("ping")
            print("[OK] MongoDB connected — using live database")
            app.state.db = db
            app.state.use_fallback = False
        except Exception:
            print("[WARN] MongoDB ping failed — starting in DEMO mode")
            app.state.db = None
            app.state.use_fallback = True
            app.state.fallback = FallbackStore()
    else:
        print("[WARN] MongoDB unreachable — starting in DEMO mode")
        app.state.db = None
        app.state.use_fallback = True
        app.state.fallback = FallbackStore()

    import asyncio
    ingestion_task = asyncio.create_task(ingestion_loop(app))
    print("[LIVE] Live news ingestion started (polling every 60s)")

    yield

    ingestion_task.cancel()
    if _mongo_client:
        _mongo_client.close()
    print("Server shutdown complete")


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

app.include_router(articles.router,   prefix="/articles", tags=["Articles"])
app.include_router(stats.router,      prefix="/stats",    tags=["Statistics"])
app.include_router(explain.router,    prefix="",          tags=["GPT"])
app.include_router(websocket.router,  prefix="",          tags=["WebSocket"])


@app.get("/health", tags=["System"])
def health(request=None):
    mode = "demo"
    if hasattr(request, "app") and hasattr(request.app, "state"):
        mode = "demo" if getattr(request.app.state, "use_fallback", True) else "live"
    return {
        "status": "ok",
        "service": "TruthStream AI API",
        "mode": mode,
    }
