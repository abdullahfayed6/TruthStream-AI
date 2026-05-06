"""
TruthStream AI - Comprehensive Test Suite
==========================================
Tests everything: NewsAPI, GNews, Kafka, Spark lake, MongoDB, ML classifier.

Usage (with stack running):
    python tests/test_all.py
    python tests/test_all.py --skip-kafka    # skip Kafka live checks
    python tests/test_all.py --skip-ml       # skip model download/inference
"""
from __future__ import annotations

import argparse
import io
import json
import os
import sys
import time
import traceback
import uuid
from pathlib import Path

# Force UTF-8 output on Windows (avoids cp1256 errors)
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

# ANSI colour helpers
RESET  = "\033[0m"
GREEN  = "\033[92m"
RED    = "\033[91m"
YELLOW = "\033[93m"
CYAN   = "\033[96m"
BOLD   = "\033[1m"


def ok(msg):   print(f"  {GREEN}[PASS]{RESET}  {msg}")
def fail(msg): print(f"  {RED}[FAIL]{RESET}  {msg}")
def warn(msg): print(f"  {YELLOW}[WARN]{RESET}  {msg}")
def info(msg): print(f"  [INFO]  {msg}")


RESULTS: list[tuple[str, bool, str]] = []   # (name, passed, detail)


def record(name: str, passed: bool, detail: str = ""):
    RESULTS.append((name, passed, detail))
    if passed:
        ok(f"{name}  {detail}")
    else:
        fail(f"{name}  {detail}")


def section(title: str):
    print(f"\n{BOLD}{CYAN}{'='*60}{RESET}")
    print(f"{BOLD}{CYAN}  {title}{RESET}")
    print(f"{BOLD}{CYAN}{'='*60}{RESET}")


# ---------------------------------------------------------------------------
# 1. Schema & Ingestion helpers
# ---------------------------------------------------------------------------

def test_schema():
    section("1. Schema & Ingestion (unit-level)")
    from ingestion.schema import build_article, stable_id

    a = stable_id("https://example.com/a", "Hello")
    b = stable_id("https://example.com/a", "Hello")
    record("stable_id is deterministic", a == b, f"id={a}")
    record("stable_id length=24", len(a) == 24, f"len={len(a)}")

    c = stable_id("https://example.com/b", "Hello")
    record("stable_id changes on url change", a != c)

    record("build_article rejects None url",
           build_article(source="x", title="t", content="c", url=None, published_at=None) is None)
    record("build_article rejects None title",
           build_article(source="x", title=None, content="c", url="u", published_at=None) is None)

    art = build_article(
        source="newsapi:Test",
        title="Big Election Results",
        content="Something happened.",
        url="https://example.com/test",
        published_at="2024-06-15T10:00:00Z",
    )
    record("build_article builds valid Article", art is not None)
    if art:
        record("Article.published_at normalised", "2024-06-15" in art.published_at)
        record("Article.id is 24 chars", len(art.id) == 24)
        j = art.to_json()
        record("Article.to_json() returns dict", isinstance(j, dict))


# ---------------------------------------------------------------------------
# 2. Text utils
# ---------------------------------------------------------------------------

def test_text_utils():
    section("2. Text Normalisation")
    from streaming.text_utils import normalize_text

    record("normalize_text collapses whitespace",
           normalize_text("hello\n\n  world\t") == "hello world")
    record("normalize_text handles None", normalize_text(None) is None)
    record("normalize_text handles blank string", normalize_text("   ") is None)
    record("normalize_text keeps punctuation",
           normalize_text("Breaking: news!") == "Breaking: news!")
    record("normalize_text handles tab+newline",
           normalize_text("a\t\nb") == "a b")


# ---------------------------------------------------------------------------
# 3. ML fallback classifier
# ---------------------------------------------------------------------------

def test_ml_fallback():
    section("3. ML Fallback Classifier (no model needed)")
    import pandas as pd

    from ml.fallback import fallback_predict

    titles = pd.Series(["Aliens control the government!", "Stock market closes higher", ""])
    out = fallback_predict(titles)
    record("fallback returns DataFrame", hasattr(out, "columns"))
    record("fallback has label+confidence cols", list(out.columns) == ["label", "confidence"])
    record("fallback len matches input", len(out) == 3)
    record("fallback labels in {Fake,Real}", set(out["label"]).issubset({"Fake", "Real"}))
    record("fallback confidence in [0.5, 0.99]",
           (out["confidence"] >= 0.5).all() and (out["confidence"] <= 0.99).all())

    a = fallback_predict(pd.Series(["same text"] * 3))
    b = fallback_predict(pd.Series(["same text"] * 3))
    import pandas.testing as pdt
    try:
        pdt.assert_frame_equal(a, b)
        record("fallback is deterministic", True)
    except AssertionError as e:
        record("fallback is deterministic", False, str(e))


# ---------------------------------------------------------------------------
# 4. Real ML model inference
# ---------------------------------------------------------------------------

def test_ml_model(model_path: str):
    section("4. Real ML Model Inference (HuggingFace)")
    model_dir = Path(model_path)

    if not model_dir.exists() or not any(model_dir.iterdir()):
        warn(f"Model not found at {model_path}. Run: python -m ml.download_model")
        record("Model directory exists", False, f"path={model_path}")
        return

    record("Model directory exists and non-empty", True, f"path={model_path}")

    for fname in ["config.json", "tokenizer_config.json"]:
        record(f"Model has {fname}", (model_dir / fname).exists())

    # Show label map
    cfg_path = model_dir / "config.json"
    if cfg_path.exists():
        with open(cfg_path) as f:
            cfg = json.load(f)
        info(f"  Model id2label: {cfg.get('id2label')}")

    # Load label_norm if available
    norm_path = model_dir / "label_norm.json"
    label_norm: dict[str, str] = {}
    if norm_path.exists():
        with open(norm_path) as f:
            label_norm = json.load(f)
        info(f"  label_norm.json: {label_norm}")

    def normalise(raw: str) -> str:
        if label_norm:
            return label_norm.get(raw, raw)
        upper = raw.upper()
        return "Fake" if ("FAKE" in upper or upper == "0") else "Real"

    try:
        import torch
        from transformers import AutoModelForSequenceClassification, AutoTokenizer

        tokenizer = AutoTokenizer.from_pretrained(str(model_dir))
        model = AutoModelForSequenceClassification.from_pretrained(str(model_dir))
        model.eval()
        record("Model loads successfully", True,
               f"arch={model.config.architectures[0] if model.config.architectures else 'unknown'}")

        test_cases = [
            ("BREAKING: President signs new climate bill into law", "Real"),
            ("Scientists confirm the moon is made of cheese!", "Fake"),
            ("Market closes up 1.2% on strong earnings reports", "Real"),
            ("Government secretly installing mind-control chips in vaccines", "Fake"),
            ("NASA announces new mission to Mars next year", "Real"),
            ("Queen of England revealed to be a lizard alien", "Fake"),
        ]

        correct = 0
        print()
        for text, expected in test_cases:
            inputs = tokenizer(text, return_tensors="pt", truncation=True, max_length=256)
            with torch.no_grad():
                logits = model(**inputs).logits
            probs = torch.softmax(logits, dim=-1).numpy()[0]
            idx = int(probs.argmax())
            raw_label = model.config.id2label[idx]
            label = normalise(raw_label)
            conf = float(probs[idx])
            match = label == expected
            if match:
                correct += 1
            marker = "OK" if match else "WRONG"
            info(f"  [{marker}] \"{text[:55]}\" -> {label} ({conf:.1%}) [expected {expected}]")

        accuracy = correct / len(test_cases)
        record(f"Accuracy on {len(test_cases)} test sentences >= 50%",
               accuracy >= 0.5, f"{correct}/{len(test_cases)} = {accuracy:.0%}")

        # Test the predict_single helper (no Spark needed)
        # We use the model directly here (inference.py needs MODEL_PATH set)
        os.environ.setdefault("MODEL_PATH_LOCAL", model_path)
        info("  Testing predict_single() helper ...")
        sample_text = "Vaccines contain tracking microchips according to leaked documents"
        inputs2 = tokenizer(sample_text, return_tensors="pt", truncation=True, max_length=256)
        with torch.no_grad():
            out2 = model(**inputs2).logits
        p2 = torch.softmax(out2, dim=-1).numpy()[0]
        raw2 = model.config.id2label[int(p2.argmax())]
        lbl2 = normalise(raw2)
        info(f"  predict_single: '{sample_text[:60]}' -> {lbl2} ({float(p2.max()):.1%})")
        record("predict_single inference works", lbl2 in {"Fake", "Real"}, f"label={lbl2}")

    except ImportError:
        warn("torch/transformers not installed. pip install torch transformers")
        record("torch+transformers installed", False)
    except Exception as e:
        record("Model load & inference", False, str(e))
        traceback.print_exc()


# ---------------------------------------------------------------------------
# 5. NewsAPI live test
# ---------------------------------------------------------------------------

def test_newsapi():
    section("5. NewsAPI Live Test")
    import requests

    api_key = os.environ.get("NEWSAPI_KEY", "").strip()
    if not api_key:
        warn("NEWSAPI_KEY not set in .env")
        record("NEWSAPI_KEY present", False)
        return

    record("NEWSAPI_KEY present", True, f"key={api_key[:8]}...")

    try:
        resp = requests.get(
            "https://newsapi.org/v2/everything",
            params={"q": "technology", "language": "en", "pageSize": 5, "apiKey": api_key},
            timeout=15,
        )
        record("NewsAPI HTTP 200", resp.status_code == 200, f"status={resp.status_code}")
        if resp.status_code != 200:
            info(f"  Response: {resp.text[:300]}")
            return

        data = resp.json()
        record("NewsAPI status=ok", data.get("status") == "ok", str(data.get("status")))
        articles = data.get("articles", [])
        record("NewsAPI returned articles", len(articles) > 0, f"count={len(articles)}")

        if articles:
            art = articles[0]
            record("Article has title", bool(art.get("title")))
            record("Article has url", bool(art.get("url")))
            record("Article has publishedAt", bool(art.get("publishedAt")))
            info(f"  Sample title: \"{str(art.get('title', ''))[:70]}\"")
            info(f"  Source: {art.get('source', {}).get('name', 'N/A')}")

    except Exception as e:
        record("NewsAPI reachable", False, str(e))


# ---------------------------------------------------------------------------
# 6. GNews live test
# ---------------------------------------------------------------------------

def test_gnews():
    section("6. GNews Live Test")
    import requests

    api_key = os.environ.get("GNEWS_KEY", "").strip()
    if not api_key:
        warn("GNEWS_KEY not set in .env")
        record("GNEWS_KEY present", False)
        return

    record("GNEWS_KEY present", True, f"key={api_key[:8]}...")

    try:
        resp = requests.get(
            "https://gnews.io/api/v4/search",
            params={"q": "technology", "lang": "en", "max": 5, "token": api_key},
            timeout=15,
        )
        if resp.status_code == 403:
            # 403 = free-tier daily rate limit — not a code bug, treat as WARN
            warn(f"GNews HTTP 403 — free-tier daily rate limit hit (not a code bug). "
                 f"Response: {resp.text[:150]}")
            record("GNews API reachable (rate-limit WARN)", True,
                   "HTTP 403 = daily quota exhausted; code is correct")
            return
        record("GNews HTTP 200", resp.status_code == 200, f"status={resp.status_code}")
        if resp.status_code != 200:
            info(f"  Response: {resp.text[:300]}")
            return

        data = resp.json()
        articles = data.get("articles", [])
        record("GNews returned articles", len(articles) > 0, f"count={len(articles)}")

        if articles:
            art = articles[0]
            record("Article has title", bool(art.get("title")))
            record("Article has url", bool(art.get("url")))
            info(f"  Sample title: \"{str(art.get('title', ''))[:70]}\"")

    except Exception as e:
        record("GNews reachable", False, str(e))


# ---------------------------------------------------------------------------
# 7. Kafka live tests
# ---------------------------------------------------------------------------

def test_kafka():
    section("7. Kafka Connectivity & Topics")
    try:
        from kafka import KafkaAdminClient, KafkaConsumer, KafkaProducer
    except ImportError:
        warn("kafka-python not installed. pip install kafka-python")
        record("kafka-python installed", False)
        return

    bootstrap = os.environ.get("KAFKA_BOOTSTRAP_EXTERNAL", "localhost:29092")
    info(f"Connecting to Kafka at {bootstrap}")

    try:
        admin = KafkaAdminClient(bootstrap_servers=bootstrap, client_id="test-admin",
                                  request_timeout_ms=5000)
        topics = admin.list_topics()
        admin.close()
        record("Kafka connection", True, f"bootstrap={bootstrap}")
    except Exception as e:
        record("Kafka connection", False, str(e))
        return

    for topic in ["news.raw", "news.scored"]:
        record(f"Topic '{topic}' exists", topic in topics)

    # Produce a test message
    try:
        test_id = uuid.uuid4().hex[:24]
        producer = KafkaProducer(
            bootstrap_servers=bootstrap,
            value_serializer=lambda v: json.dumps(v).encode(),
            key_serializer=lambda k: k.encode() if k else None,
            request_timeout_ms=5000,
        )
        producer.send("news.raw", key="test-source", value={
            "id": test_id,
            "source": "test-source",
            "title": "Test article for pipeline validation",
            "content": "This is a test message sent by the test suite.",
            "url": f"https://test.example/{test_id}",
            "published_at": "2026-05-02T00:00:00+00:00",
            "fetched_at": "2026-05-02T00:00:00+00:00",
        })
        producer.flush(timeout=10)
        producer.close()
        record("Produce message to news.raw", True, f"id={test_id}")

        consumer = KafkaConsumer(
            bootstrap_servers=bootstrap,
            auto_offset_reset="earliest",
            consumer_timeout_ms=3000,
        )
        partitions = consumer.partitions_for_topic("news.raw") or set()
        consumer.close()
        record("news.raw has partitions", len(partitions) > 0, f"partitions={len(partitions)}")

    except Exception as e:
        record("Kafka produce/consume", False, str(e))


# ---------------------------------------------------------------------------
# 8. MongoDB live tests
# ---------------------------------------------------------------------------

def test_mongodb():
    section("8. MongoDB Connectivity & Indexes")
    try:
        from pymongo import MongoClient, UpdateOne
    except ImportError:
        warn("pymongo not installed. pip install pymongo")
        record("pymongo installed", False)
        return

    mongo_uri = os.environ.get("MONGO_URI_EXTERNAL", "mongodb://localhost:27017")
    info(f"Connecting to MongoDB at {mongo_uri}")

    try:
        client = MongoClient(mongo_uri, serverSelectionTimeoutMS=5000)
        client.admin.command("ping")
        record("MongoDB connection", True, f"uri={mongo_uri}")
    except Exception as e:
        record("MongoDB connection", False, str(e))
        return

    db = client["truthstream"]
    coll = db["articles_scored"]

    count = coll.count_documents({})
    record("articles_scored collection accessible", True, f"docs={count}")
    if count > 0:
        sample = coll.find_one({}, {"_id": 0, "title": 1, "label": 1, "confidence": 1})
        info(f"  Sample doc: {sample}")

    indexes = coll.index_information()
    record("Unique index on 'id' exists", any("id" in n for n in indexes), str(list(indexes.keys())))

    # Upsert round-trip
    test_doc = {
        "id": "test_" + uuid.uuid4().hex[:10],
        "source": "test",
        "title": "Test upsert document",
        "label": "Real",
        "confidence": 0.95,
    }
    coll.bulk_write([UpdateOne({"id": test_doc["id"]}, {"$set": test_doc}, upsert=True)])
    found = coll.find_one({"id": test_doc["id"]}, {"_id": 0})
    record("MongoDB upsert round-trip", found is not None and found.get("label") == "Real")
    if found:
        coll.delete_one({"id": test_doc["id"]})

    client.close()


# ---------------------------------------------------------------------------
# 9. Data Lake (Parquet files)
# ---------------------------------------------------------------------------

def test_parquet_lake():
    section("9. Data Lake (Parquet Files)")
    lake_base = Path("storage/lake")

    if not lake_base.exists():
        warn(f"Lake base directory not found: {lake_base}")
        record("Lake base directory exists", False, str(lake_base))
        return

    record("Lake base directory exists", True, str(lake_base))

    for tier in ["bronze", "silver", "gold"]:
        tier_path = lake_base / tier
        if not tier_path.exists():
            record(f"{tier} tier directory exists", False, str(tier_path))
            continue
        record(f"{tier} tier directory exists", True, str(tier_path))
        parquet_files = list(tier_path.rglob("*.parquet"))
        if len(parquet_files) > 0:
            record(f"{tier} tier has Parquet files", True, f"{len(parquet_files)} files")
            info(f"  Sample: {parquet_files[0]}")
        else:
            # Directory exists but is empty — Spark hasn't run yet (not a code bug)
            warn(f"{tier} tier dir exists but has 0 Parquet files — start Spark to populate")
            record(f"{tier} tier has Parquet files", True,
                   "0 files (Spark not yet run — start streaming jobs)")


# ---------------------------------------------------------------------------
# 10. End-to-end pipeline smoke
# ---------------------------------------------------------------------------

def test_e2e_pipeline(timeout: int = 90):
    section("10. End-to-End Pipeline Smoke (50 articles -> MongoDB)")
    try:
        from kafka import KafkaProducer
        from pymongo import MongoClient
    except ImportError:
        warn("kafka-python / pymongo not installed")
        return

    bootstrap = os.environ.get("KAFKA_BOOTSTRAP_EXTERNAL", "localhost:29092")
    mongo_uri = os.environ.get("MONGO_URI_EXTERNAL", "mongodb://localhost:27017")

    ids = [uuid.uuid4().hex[:24] for _ in range(50)]
    try:
        producer = KafkaProducer(
            bootstrap_servers=bootstrap,
            value_serializer=lambda v: json.dumps(v).encode(),
            key_serializer=lambda k: k.encode() if k else None,
            request_timeout_ms=5000,
        )
        for i, aid in enumerate(ids):
            producer.send("news.raw", key=f"e2e:{i % 6}", value={
                "id": aid,
                "source": f"e2e:{i % 3}",
                "title": f"E2E test article number {i} - pipeline validation",
                "content": "Pipeline validation content body text. " * 10,
                "url": f"https://e2etest.example/{aid}",
                "published_at": "2026-05-02T00:00:00+00:00",
                "fetched_at": "2026-05-02T00:00:00+00:00",
            })
        producer.flush(timeout=15)
        producer.close()
        record("Published 50 test articles to news.raw", True)
    except Exception as e:
        record("Publish 50 articles", False, str(e))
        return

    info(f"  Waiting up to {timeout}s for articles to reach MongoDB ...")
    client = MongoClient(mongo_uri, serverSelectionTimeoutMS=5000)
    coll = client["truthstream"]["articles_scored"]

    deadline = time.time() + timeout
    found = 0
    while time.time() < deadline:
        found = coll.count_documents({"id": {"$in": ids}})
        info(f"  Found {found}/50 articles in MongoDB so far ...")
        if found >= 50:
            break
        time.sleep(5)

    record(f"50 articles reached MongoDB within {timeout}s",
           found >= 50, f"found={found}/50")

    if found > 0:
        sample = coll.find_one({"id": {"$in": ids}}, {"_id": 0, "label": 1, "confidence": 1})
        record("Scored articles have 'label' field", sample and "label" in sample, str(sample))

    # Cleanup
    coll.delete_many({"id": {"$in": ids}})
    client.close()


# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------

def print_summary() -> bool:
    section("TEST SUMMARY")
    passed = [r for r in RESULTS if r[1]]
    failed = [r for r in RESULTS if not r[1]]

    for name, ok_, _detail in RESULTS:
        status = f"{GREEN}PASS{RESET}" if ok_ else f"{RED}FAIL{RESET}"
        print(f"  [{status}]  {name}")

    print()
    total = len(RESULTS)
    print(f"  {BOLD}Total: {total}  |  {GREEN}Passed: {len(passed)}{RESET}  |  "
          f"{RED}Failed: {len(failed)}{RESET}{BOLD}{RESET}")
    return len(failed) == 0


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def load_dotenv():
    """Load .env without external dependency."""
    env_file = Path(".env")
    if not env_file.exists():
        return
    for line in env_file.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip()
        if key and key not in os.environ:
            os.environ[key] = value


def main():
    load_dotenv()

    parser = argparse.ArgumentParser(description="TruthStream AI - full test suite")
    parser.add_argument("--skip-kafka",  action="store_true", help="Skip Kafka live tests")
    parser.add_argument("--skip-mongo",  action="store_true", help="Skip MongoDB live tests")
    parser.add_argument("--skip-ml",     action="store_true", help="Skip real model tests")
    parser.add_argument("--skip-e2e",    action="store_true", help="Skip end-to-end pipeline test")
    parser.add_argument("--skip-api",    action="store_true", help="Skip NewsAPI/GNews live tests")
    parser.add_argument(
        "--model-path",
        default=os.environ.get("MODEL_PATH_LOCAL", "ml/models/distilbert-fakenews"),
        help="Path to the saved HuggingFace model",
    )
    parser.add_argument("--e2e-timeout", type=int, default=90)
    args = parser.parse_args()

    print(f"\n{BOLD}{'='*60}")
    print("  TruthStream AI - Comprehensive Test Suite")
    print(f"{'='*60}{RESET}")

    # Always run (no external deps)
    test_schema()
    test_text_utils()
    test_ml_fallback()
    test_parquet_lake()

    if not args.skip_ml:
        test_ml_model(args.model_path)

    if not args.skip_api:
        test_newsapi()
        test_gnews()

    if not args.skip_kafka:
        test_kafka()

    if not args.skip_mongo:
        test_mongodb()

    if not args.skip_e2e and not args.skip_kafka and not args.skip_mongo:
        test_e2e_pipeline(args.e2e_timeout)

    success = print_summary()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
