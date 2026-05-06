"""
WebSocket router — real-time article stream for the Next.js frontend.

WS  /ws/articles  — push newly scored articles as they arrive
GET /articles/stream — SSE fallback for environments that can't use WS
"""
from __future__ import annotations

import asyncio
import json
from datetime import UTC, datetime

from fastapi import APIRouter, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse

router = APIRouter()



class ConnectionManager:
    """Manages active WebSocket connections."""

    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                pass


manager = ConnectionManager()


@router.websocket("/ws/articles")
async def websocket_articles(websocket: WebSocket):
    """
    WebSocket endpoint that polls for new articles and pushes them
    to connected clients.
    """
    await manager.connect(websocket)

    use_fallback = getattr(websocket.app.state, "use_fallback", False)
    last_check = datetime.now(UTC).isoformat()

    try:
        while True:
            try:
                if use_fallback:
                    fallback = websocket.app.state.fallback
                    new_docs = fallback.get_new_articles_since(last_check)
                    if new_docs:
                        last_check = new_docs[0].get("scored_at", last_check)
                        await websocket.send_json({
                            "type": "new_articles",
                            "articles": new_docs[:5],
                            "count": len(new_docs),
                            "timestamp": datetime.now(UTC).isoformat()
                        })
                    else:
                        await websocket.send_json({
                            "type": "heartbeat",
                            "timestamp": datetime.now(UTC).isoformat()
                        })
                else:
                    db = websocket.app.state.db
                    coll = db["articles_scored"]
                    new_docs = list(
                        coll.find(
                            {"scored_at": {"$gt": last_check}},
                            {"_id": 0}
                        )
                        .sort("scored_at", -1)
                        .limit(10)
                    )

                    if new_docs:
                        last_check = new_docs[0].get("scored_at", last_check)
                        for doc in new_docs:
                            for k, v in doc.items():
                                if hasattr(v, 'isoformat'):
                                    doc[k] = v.isoformat()
                        await websocket.send_json({
                            "type": "new_articles",
                            "articles": new_docs,
                            "count": len(new_docs),
                            "timestamp": datetime.now(UTC).isoformat()
                        })
                    else:
                        await websocket.send_json({
                            "type": "heartbeat",
                            "timestamp": datetime.now(UTC).isoformat()
                        })
            except WebSocketDisconnect:
                raise
            except Exception as e:
                try:
                    await websocket.send_json({
                        "type": "error",
                        "message": str(e)
                    })
                except Exception:
                    break

            await asyncio.sleep(3)

    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception:
        manager.disconnect(websocket)



@router.get("/articles/stream")
async def stream_articles(request: Request):
    """
    Server-Sent Events endpoint — fallback for environments
    that cannot use WebSockets.
    """
    use_fallback = getattr(request.app.state, "use_fallback", False)
    last_check = datetime.now(UTC).isoformat()

    async def event_generator():
        nonlocal last_check
        while True:
            if await request.is_disconnected():
                break

            try:
                if use_fallback:
                    fallback = request.app.state.fallback
                    new_docs = fallback.get_new_articles_since(last_check)
                    if new_docs:
                        last_check = new_docs[0].get("scored_at", last_check)
                        data = json.dumps({"articles": new_docs[:5], "count": len(new_docs)}, default=str)
                        yield f"event: new_articles\ndata: {data}\n\n"
                    else:
                        yield "event: heartbeat\ndata: {}\n\n"
                else:
                    coll = request.app.state.db["articles_scored"]
                    new_docs = list(
                        coll.find(
                            {"scored_at": {"$gt": last_check}},
                            {"_id": 0}
                        )
                        .sort("scored_at", -1)
                        .limit(10)
                    )
                    if new_docs:
                        last_check = new_docs[0].get("scored_at", last_check)
                        data = json.dumps({"articles": new_docs, "count": len(new_docs)}, default=str)
                        yield f"event: new_articles\ndata: {data}\n\n"
                    else:
                        yield "event: heartbeat\ndata: {}\n\n"
            except Exception as e:
                yield f"event: error\ndata: {{\"message\": \"{str(e)}\"}}\n\n"

            await asyncio.sleep(3)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
