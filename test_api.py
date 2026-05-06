"""
TruthStream AI — Full System Test
Tests all API endpoints, data integrity, live ingestion, and WebSocket.
"""
import asyncio
import json
import sys
import time
import httpx
import websockets

BASE = "http://localhost:8000"
WS_BASE = "ws://localhost:8000"
PASS = 0
FAIL = 0


def ok(label, detail=""):
    global PASS
    PASS += 1
    suffix = f"  →  {detail}" if detail else ""
    print(f"  ✅  {label}{suffix}")


def fail(label, detail=""):
    global FAIL
    FAIL += 1
    suffix = f"  →  {detail}" if detail else ""
    print(f"  ❌  {label}{suffix}")


def section(title):
    print(f"\n{'─'*60}")
    print(f"  {title}")
    print(f"{'─'*60}")


# ─────────────────────────────────────────────────────────────
# 1. Health
# ─────────────────────────────────────────────────────────────
section("1 · Health Check")
try:
    r = httpx.get(f"{BASE}/health", timeout=5)
    d = r.json()
    assert r.status_code == 200
    assert d["status"] == "ok"
    ok("GET /health", f"status={d['status']}  mode={d.get('mode','?')}")
except Exception as e:
    fail("GET /health", str(e))

# ─────────────────────────────────────────────────────────────
# 2. Statistics
# ─────────────────────────────────────────────────────────────
section("2 · Statistics")
stats = None
try:
    r = httpx.get(f"{BASE}/stats", timeout=5)
    stats = r.json()
    assert r.status_code == 200
    assert stats["total"] >= 20, f"Expected ≥20 articles, got {stats['total']}"
    ok("GET /stats — total count", f"{stats['total']} articles")
except Exception as e:
    fail("GET /stats — total count", str(e))

try:
    assert stats is not None
    assert "fake" in stats and "real" in stats
    assert stats["fake"] + stats["real"] == stats["total"]
    ok("GET /stats — fake+real == total", f"fake={stats['fake']}  real={stats['real']}")
except Exception as e:
    fail("GET /stats — fake+real == total", str(e))

try:
    assert stats is not None
    assert "source_breakdown" in stats
    assert len(stats["source_breakdown"]) >= 3
    ok("GET /stats — source_breakdown present", f"{len(stats['source_breakdown'])} sources")
except Exception as e:
    fail("GET /stats — source_breakdown present", str(e))

try:
    assert stats is not None
    assert "top_sources" in stats and len(stats["top_sources"]) > 0
    ok("GET /stats — top_sources", f"{len(stats['top_sources'])} sources")
except Exception as e:
    fail("GET /stats — top_sources", str(e))

try:
    assert stats is not None
    assert "fake_rate_by_source" in stats
    ok("GET /stats — fake_rate_by_source", f"{len(stats['fake_rate_by_source'])} entries")
except Exception as e:
    fail("GET /stats — fake_rate_by_source", str(e))

# ─────────────────────────────────────────────────────────────
# 3. Timeline
# ─────────────────────────────────────────────────────────────
section("3 · Timeline")
try:
    r = httpx.get(f"{BASE}/stats/timeline?hours=24", timeout=5)
    timeline = r.json()
    assert r.status_code == 200
    assert isinstance(timeline, list)
    assert len(timeline) >= 1
    for entry in timeline:
        assert "hour" in entry and "fake" in entry and "real" in entry and "total" in entry
    ok("GET /stats/timeline", f"{len(timeline)} hours with data")
except Exception as e:
    fail("GET /stats/timeline", str(e))

# ─────────────────────────────────────────────────────────────
# 4. Articles — Pagination
# ─────────────────────────────────────────────────────────────
section("4 · Articles (Pagination & Filtering)")
articles_data = None
try:
    r = httpx.get(f"{BASE}/articles?page=1&page_size=10", timeout=5)
    articles_data = r.json()
    assert r.status_code == 200
    assert articles_data["total"] >= 20
    assert len(articles_data["articles"]) == 10
    assert articles_data["page"] == 1
    assert articles_data["pages"] >= 2
    ok("GET /articles — pagination", f"total={articles_data['total']}  pages={articles_data['pages']}")
except Exception as e:
    fail("GET /articles — pagination", str(e))

try:
    r = httpx.get(f"{BASE}/articles?label=Fake&page_size=50", timeout=5)
    d = r.json()
    assert r.status_code == 200
    assert all(a["label"] == "Fake" for a in d["articles"]), "Non-Fake article in filtered results"
    ok("GET /articles?label=Fake", f"{d['total']} fake articles returned correctly")
except Exception as e:
    fail("GET /articles?label=Fake", str(e))

try:
    r = httpx.get(f"{BASE}/articles?label=Real&page_size=50", timeout=5)
    d = r.json()
    assert r.status_code == 200
    assert all(a["label"] == "Real" for a in d["articles"]), "Non-Real article in filtered results"
    ok("GET /articles?label=Real", f"{d['total']} real articles returned correctly")
except Exception as e:
    fail("GET /articles?label=Real", str(e))

# ─────────────────────────────────────────────────────────────
# 5. Single Article
# ─────────────────────────────────────────────────────────────
section("5 · Single Article Fetch")
try:
    assert articles_data and articles_data["articles"]
    art = articles_data["articles"][0]
    art_id = art["id"]
    r = httpx.get(f"{BASE}/articles/{art_id}", timeout=5)
    d = r.json()
    assert r.status_code == 200
    assert d["id"] == art_id
    assert "title" in d and "label" in d and "confidence" in d
    ok(f"GET /articles/{{id}}", f"id={art_id[:12]}...  label={d['label']}")
except Exception as e:
    fail("GET /articles/{id}", str(e))

try:
    r = httpx.get(f"{BASE}/articles/nonexistent_id_that_doesnt_exist", timeout=5)
    assert r.status_code == 404
    ok("GET /articles/{bad_id} → 404", "correct error code")
except Exception as e:
    fail("GET /articles/{bad_id} → 404", str(e))

# ─────────────────────────────────────────────────────────────
# 6. Article data integrity
# ─────────────────────────────────────────────────────────────
section("6 · Article Data Integrity")
try:
    r = httpx.get(f"{BASE}/articles?page_size=50", timeout=5)
    all_arts = r.json()["articles"]
    required_fields = ["id", "title", "source", "label", "confidence", "scored_at"]
    bad = [a for a in all_arts if not all(f in a for f in required_fields)]
    assert len(bad) == 0, f"{len(bad)} articles missing required fields"
    ok("All articles have required fields", f"checked {len(all_arts)} articles")
except Exception as e:
    fail("All articles have required fields", str(e))

try:
    r = httpx.get(f"{BASE}/articles?page_size=50", timeout=5)
    all_arts = r.json()["articles"]
    bad_labels = [a for a in all_arts if a["label"] not in ("Fake", "Real")]
    assert len(bad_labels) == 0, f"{len(bad_labels)} articles with invalid labels"
    ok("All labels are Fake or Real", f"{len(all_arts)} articles checked")
except Exception as e:
    fail("All labels are Fake or Real", str(e))

try:
    r = httpx.get(f"{BASE}/articles?page_size=50", timeout=5)
    all_arts = r.json()["articles"]
    bad_conf = [a for a in all_arts if not (0 <= a["confidence"] <= 1)]
    assert len(bad_conf) == 0, f"{len(bad_conf)} articles with confidence out of [0,1]"
    ok("All confidence scores in [0.0, 1.0]", f"{len(all_arts)} articles checked")
except Exception as e:
    fail("All confidence scores in [0.0, 1.0]", str(e))

# ─────────────────────────────────────────────────────────────
# 7. GPT Explain
# ─────────────────────────────────────────────────────────────
section("7 · GPT Explain & Summarize")
payload_fake = {
    "title": "Government Hiding Aliens at Secret Base",
    "content": "Anonymous sources claim alien spacecraft are hidden in Nevada.",
    "label": "Fake",
    "confidence": 0.97,
    "source": "SocialBuzz",
}
payload_real = {
    "title": "NASA Successfully Launches New Mars Rover",
    "content": "NASA's Perseverance rover landed successfully in Jezero Crater on Mars.",
    "label": "Real",
    "confidence": 0.93,
    "source": "Reuters",
}
try:
    r = httpx.post(f"{BASE}/explain", json=payload_fake, timeout=20)
    d = r.json()
    assert r.status_code == 200
    assert "text" in d and len(d["text"]) > 20
    assert "model" in d
    ok("POST /explain (Fake article)", f"model={d['model']}  tokens={d.get('tokens_used',0)}")
except Exception as e:
    fail("POST /explain (Fake article)", str(e))

try:
    r = httpx.post(f"{BASE}/explain", json=payload_real, timeout=20)
    d = r.json()
    assert r.status_code == 200
    assert "text" in d and len(d["text"]) > 20
    ok("POST /explain (Real article)", f"model={d['model']}")
except Exception as e:
    fail("POST /explain (Real article)", str(e))

try:
    r = httpx.post(f"{BASE}/summarize", json=payload_real, timeout=20)
    d = r.json()
    assert r.status_code == 200
    assert "text" in d and len(d["text"]) > 10
    ok("POST /summarize", f"model={d['model']}  len={len(d['text'])} chars")
except Exception as e:
    fail("POST /summarize", str(e))

# ─────────────────────────────────────────────────────────────
# 8. Live Ingestion check
# ─────────────────────────────────────────────────────────────
section("8 · Live Ingestion")
try:
    r1 = httpx.get(f"{BASE}/stats", timeout=5)
    count_before = r1.json()["total"]
    # Articles with real sources should be present (live ingestion ran)
    r = httpx.get(f"{BASE}/articles?page_size=100", timeout=5)
    all_arts = r.json()["articles"]
    # Check that we have articles beyond the original 20 demo articles
    assert count_before > 20, f"Expected >20 articles after live ingestion, got {count_before}"
    ok("Live ingestion added articles", f"total={count_before} (>20 demo baseline)")
except Exception as e:
    fail("Live ingestion added articles", str(e))

try:
    r = httpx.get(f"{BASE}/articles?page_size=100", timeout=5)
    all_arts = r.json()["articles"]
    # Real news articles have real URLs (not example.com)
    live_arts = [a for a in all_arts if "example.com" not in a.get("url", "")]
    assert len(live_arts) > 0, "No live-ingested articles found"
    ok("Live articles have real URLs", f"{len(live_arts)} articles from real sources")
except Exception as e:
    fail("Live articles have real URLs", str(e))

# ─────────────────────────────────────────────────────────────
# 9. WebSocket
# ─────────────────────────────────────────────────────────────
section("9 · WebSocket Real-Time Stream")

async def test_websocket():
    try:
        async with websockets.connect(f"{WS_BASE}/ws/articles", open_timeout=5) as ws:
            msg_raw = await asyncio.wait_for(ws.recv(), timeout=8)
            msg = json.loads(msg_raw)
            assert "type" in msg
            assert msg["type"] in ("heartbeat", "new_articles", "error")
            assert "timestamp" in msg
            ok("WS /ws/articles — connects & receives message", f"type={msg['type']}")
            return True
    except Exception as e:
        fail("WS /ws/articles", str(e))
        return False

asyncio.run(test_websocket())

# ─────────────────────────────────────────────────────────────
# 10. CORS Headers
# ─────────────────────────────────────────────────────────────
section("10 · CORS Headers")
try:
    r = httpx.options(
        f"{BASE}/stats",
        headers={"Origin": "http://localhost:3000", "Access-Control-Request-Method": "GET"},
        timeout=5,
    )
    assert "access-control-allow-origin" in r.headers
    ok("CORS headers present", f"allow-origin={r.headers.get('access-control-allow-origin','?')}")
except Exception as e:
    fail("CORS headers present", str(e))

# ─────────────────────────────────────────────────────────────
# Summary
# ─────────────────────────────────────────────────────────────
total = PASS + FAIL
print(f"\n{'═'*60}")
print(f"  RESULTS:  {PASS}/{total} passed  |  {FAIL} failed")
print(f"{'═'*60}")
if FAIL > 0:
    print("  ⚠️  Some tests failed — check output above for details.")
    sys.exit(1)
else:
    print("  🎉  All tests passed!")
    sys.exit(0)
